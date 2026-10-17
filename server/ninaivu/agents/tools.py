"""Agent tools. Each one wraps a memory/coordination function.

Isolation by construction: tools are closures over a TurnContext, so the model never supplies
tenant or customer ids and cannot reach another customer's memory.
"""
import json
from dataclasses import dataclass, field
from typing import Literal

from anthropic import beta_tool

from .. import coordination, memory
from ..clock import DAY
from ..ids import new_id


@dataclass(frozen=True)
class TurnContext:
    tenant: str
    customer_id: str
    session_id: str
    agent: str
    now: int


@dataclass
class TurnState:
    """What the tools did during one agent run: the UI trace, and whether it handed off."""

    trace: list[dict] = field(default_factory=list)
    handoff_to: str | None = None


# Which tools each agent gets (PLAN.md §7). Every support agent can open an issue for a new problem;
# Billing also gets playbooks so its seeded billing playbooks are used.
AGENT_TOOLS: dict[str, tuple[str, ...]] = {
    "triage": ("search_memory", "issue_history", "open_issue", "link_order", "handoff_to", "remember_fact"),
    "billing": ("search_memory", "lookup_order", "issue_refund", "find_playbook", "record_playbook_outcome",
                "open_issue", "resolve_issue", "handoff_to", "remember_fact"),
    "tech": ("search_memory", "find_playbook", "record_playbook_outcome", "open_issue", "resolve_issue",
             "handoff_to", "remember_fact"),
}


def _json(value) -> str:
    return json.dumps(value, default=str)


def build_tools(ctx: TurnContext, state: TurnState) -> list:
    """Return the @beta_tool functions for ctx.agent, each bound to ctx and recording into state.trace."""
    t, cid = ctx.tenant, ctx.customer_id

    def done(tool: str, args: dict, result) -> str:
        out = _json(result)
        state.trace.append({"agent": ctx.agent, "tool": tool, "input": args, "result": out[:400]})
        return out

    def fail(tool: str, args: dict, error: str) -> str:
        return done(tool, args, {"ok": False, "error": error})

    @beta_tool
    def search_memory(query: str) -> str:
        """Search stored facts about this customer by meaning.

        Args:
            query: What you are looking for, e.g. "how they like to be contacted".
        """
        return done("search_memory", {"query": query}, memory.semantic_recall(t, cid, query))

    @beta_tool
    def issue_history(days: int = 30) -> str:
        """List this customer's issues from the last N days, with status, resolution and the fix that worked.

        Args:
            days: How far back to look.
        """
        return done("issue_history", {"days": days}, memory.issue_history(t, cid, ctx.now - days * DAY))

    @beta_tool
    def open_issue(title: str, category: Literal["billing", "tech", "general"], order_id: str | None = None) -> str:
        """Open a new issue for a new problem. You become its owner; hand it off if it belongs to a teammate.

        Args:
            title: Short title, e.g. "Earbuds arrived damaged (A-1001)".
            category: billing, tech or general.
            order_id: The related order id, if the customer mentioned one.
        """
        args = {"title": title, "category": category, "order_id": order_id}
        iid = memory.open_issue(t, cid, ctx.session_id, new_id("i"), title, category, ctx.now)
        coordination.claim_issue(t, cid, iid, ctx.agent, ctx.now)
        result = {"ok": True, "issue_id": iid, "owner": ctx.agent}
        if order_id:
            result["order_linked"] = memory.link_order(t, cid, iid, order_id)
            if not result["order_linked"]:
                result["note"] = f"Order {order_id} is not on this customer's account."
        return done("open_issue", args, result)

    @beta_tool
    def link_order(issue_id: str, order_id: str) -> str:
        """Attach an order to an existing issue.

        Args:
            issue_id: The issue id.
            order_id: The order id.
        """
        args = {"issue_id": issue_id, "order_id": order_id}
        if not memory.link_order(t, cid, issue_id, order_id):
            return fail("link_order", args, "Issue or order not found on this customer's account.")
        return done("link_order", args, {"ok": True})

    @beta_tool
    def handoff_to(agent: Literal["triage", "billing", "tech"], issue_id: str, reason: str, context_summary: str) -> str:
        """Hand an issue you own to a teammate. They take over in this same conversation, right after you.

        Args:
            agent: The teammate who should take over.
            issue_id: The issue being handed over.
            reason: Why they should take it, in a few words.
            context_summary: What they need to continue without asking the customer again.
        """
        args = {"agent": agent, "issue_id": issue_id, "reason": reason, "context_summary": context_summary}
        if agent == ctx.agent:
            return fail("handoff_to", args, "You can't hand off to yourself.")
        if state.handoff_to:
            return fail("handoff_to", args, f"Already handed off to {state.handoff_to} this turn.")
        hid = coordination.handoff(t, cid, issue_id, ctx.agent, agent, reason, context_summary, ctx.now)
        if hid is None:
            return fail("handoff_to", args, "You don't own this issue, or it doesn't exist. Check the issue id.")
        state.handoff_to = agent
        return done("handoff_to", args, {"ok": True, "handoff_id": hid,
                                         "next": f"{agent} takes over now. Tell the customer in one short sentence, then stop."})

    @beta_tool
    def remember_fact(key: str, text: str) -> str:
        """Store a lasting fact about the customer. A new value for an existing key replaces the old one (history is kept).

        Args:
            key: Stable snake_case key such as contact_preference, city, language, device.
            text: The fact as a short sentence, e.g. "Prefers WhatsApp updates, not email".
        """
        return done("remember_fact", {"key": key, "text": text},
                    memory.remember_fact(t, cid, ctx.session_id, key, text, ctx.now))

    @beta_tool
    def lookup_order(order_id: str) -> str:
        """Get an order's status, amount, date, products and refunds.

        Args:
            order_id: The order id, e.g. A-1001.
        """
        order = memory.lookup_order(t, cid, order_id)
        if order is None:
            return fail("lookup_order", {"order_id": order_id}, "No such order on this customer's account.")
        return done("lookup_order", {"order_id": order_id}, order)

    @beta_tool
    def issue_refund(order_id: str, amount: float) -> str:
        """Initiate a refund on an order (amount in INR).

        Args:
            order_id: The order to refund.
            amount: Refund amount in INR.
        """
        args = {"order_id": order_id, "amount": amount}
        rid = memory.create_refund(t, cid, order_id, amount, ctx.agent, ctx.now)
        if rid is None:
            return fail("issue_refund", args, "No such order on this customer's account.")
        return done("issue_refund", args, {"ok": True, "refund_id": rid, "status": "initiated",
                                           "expected": "5-7 working days"})

    @beta_tool
    def find_playbook(symptom: str) -> str:
        """Find playbooks that match a problem. Only close matches are returned, best success rate first: follow the top one.

        Args:
            symptom: The problem in a sentence, e.g. "earbuds won't pair with phone".
        """
        category = ctx.agent if ctx.agent in ("billing", "tech") else "tech"
        return done("find_playbook", {"symptom": symptom}, memory.find_playbooks(t, category, symptom))

    @beta_tool
    def record_playbook_outcome(issue_id: str, playbook_id: str, worked: bool) -> str:
        """Record whether a playbook fixed the issue, so the team learns which playbooks work.

        Args:
            issue_id: The issue it was used on.
            playbook_id: The playbook id from find_playbook.
            worked: True if it fixed the problem.
        """
        args = {"issue_id": issue_id, "playbook_id": playbook_id, "worked": worked}
        try:
            result = memory.record_playbook_outcome(t, cid, issue_id, playbook_id, worked, ctx.now)
        except memory.NotFound:
            return fail("record_playbook_outcome", args, "Issue or playbook not found.")
        return done("record_playbook_outcome", args, {"ok": True, **result})

    @beta_tool
    def resolve_issue(issue_id: str, resolution: str) -> str:
        """Mark an issue resolved once the customer's request is handled.

        Args:
            issue_id: The issue id.
            resolution: One sentence on what fixed it.
        """
        args = {"issue_id": issue_id, "resolution": resolution}
        try:
            memory.resolve_issue(t, cid, issue_id, resolution, ctx.now)
        except memory.NotFound:
            return fail("resolve_issue", args, "No such issue on this customer's account.")
        return done("resolve_issue", args, {"ok": True})

    available = {
        "search_memory": search_memory, "issue_history": issue_history, "open_issue": open_issue,
        "link_order": link_order, "handoff_to": handoff_to, "remember_fact": remember_fact,
        "lookup_order": lookup_order, "issue_refund": issue_refund, "find_playbook": find_playbook,
        "record_playbook_outcome": record_playbook_outcome, "resolve_issue": resolve_issue,
    }
    return [available[name] for name in AGENT_TOOLS[ctx.agent]]
