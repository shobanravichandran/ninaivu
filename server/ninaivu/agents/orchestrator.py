"""Routes a customer message to the agent that owns it, according to the graph.

The backend is stateless: ownership, history and memory are read from FalkorDB on every turn.
"""
import time

from .. import clock, coordination, llm, memory
from ..config import TENANTS
from ..ids import new_id
from .prompts import AGENT_PROMPTS
from .tools import TurnContext, TurnState, build_tools

MAX_HOPS = 2  # handoffs followed within one request

AGENT_EFFORT = {"triage": "low", "billing": "medium", "tech": "medium", "curator": "low"}


def _date(ts: int | None) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ts)) if ts else "?"


def _ago(ts: int | None, now: int) -> str:
    if not ts:
        return "?"
    days = (now - ts) // clock.DAY
    return "today" if days <= 0 else "yesterday" if days == 1 else f"{days} days ago"


def render_turn(pack: dict, transcript: list[dict], handoff_note: str | None, now: int) -> str:
    """The user turn: memory context, any handoff addressed to this agent, and this session's conversation."""
    c = pack["customer"]
    lines = [f"Current date: {_date(now)}", "", "<memory>", f"Customer: {c['name']} ({c['id']}, {c['tier']} tier)", "",
             "Open issues:"]
    lines += [
        f"- [{i['issue_id']}] {i['title']} | category {i['category']} | owner {i['owner'] or 'unassigned'}"
        f" | order {i['order_id'] or '-'} | opened {_ago(i['opened_at'], now)}"
        for i in pack["open_issues"]
    ] or ["- none"]
    lines += ["", "Known facts:"]
    lines += [f"- {f['key']}: {f['text']} (since {_date(f['since'])})" for f in pack["facts"]] or ["- none"]
    if pack.get("recalled"):
        lines += ["", "Facts most related to the latest message:"]
        lines += [f"- {r['key']}: {r['text']}" for r in pack["recalled"]]
    lines += ["", "Recent sessions:"]
    lines += [f"- {_ago(s['started_at'], now)}: {s['summary']}" for s in pack["recent_sessions"]] or ["- none"]
    lines.append("</memory>")
    if handoff_note:
        lines += ["", "<handoff_to_you>", handoff_note, "</handoff_to_you>"]
    lines += ["", "<conversation>"]
    lines += [f"{m['agent'] or 'customer'}: {m['text']}" for m in transcript]
    lines += ["</conversation>", "", "Reply to the customer's latest message."]
    return "\n".join(lines)


def _handoff_note(tenant: str, customer_id: str, owner: dict | None, agent: str) -> str | None:
    """The latest handoff addressed to this agent on the issue it owns (explain_trace)."""
    if not owner:
        return None
    steps = [s for s in coordination.explain_trace(tenant, customer_id, owner["issue_id"]) if s["to_agent"] == agent]
    if not steps:
        return None
    last = steps[-1]
    return f"Issue {owner['issue_id']} from {last['from_agent']}: {last['reason']}. Context: {last['context']}"


def run_agent(agent: str, ctx: TurnContext, state: TurnState, user_turn: str) -> str:
    runner = llm.client().beta.messages.tool_runner(
        max_tokens=16000,
        system=AGENT_PROMPTS[agent].format(company=TENANTS[ctx.tenant]),
        tools=build_tools(ctx, state),
        messages=[{"role": "user", "content": user_turn}],
        max_iterations=10,
        cache_control={"type": "ephemeral"},
        **llm.request_kwargs(AGENT_EFFORT[agent]),
    )
    final = runner.until_done()
    if final.stop_reason == "refusal":
        return llm.REFUSAL_REPLY
    return llm.text_of(final) or "(no reply)"


def handle_message(tenant: str, customer_id: str, session_id: str | None, message: str, clock_offset_days: float) -> dict:
    """One customer turn (PLAN.md §3, request flow). Returns {"session_id", "replies", "owner", "trace", "memory"}."""
    now = clock.now(clock_offset_days)
    if session_id is None:
        session_id = memory.start_session(tenant, customer_id, new_id("s"), now)
    memory.append_message(tenant, customer_id, session_id, "customer", None, message, now)

    owner = coordination.get_owner(tenant, customer_id)
    agent = owner["owner"] if owner and owner["owner"] in AGENT_PROMPTS else "triage"
    if owner:
        memory.link_issue_to_session(tenant, customer_id, owner["issue_id"], session_id)

    replies: list[dict] = []
    trace: list[dict] = []
    for hop in range(MAX_HOPS + 1):
        pack = memory.context_pack(tenant, customer_id, query_text=message)
        transcript = memory.session_messages(tenant, customer_id, session_id)
        user_turn = render_turn(pack, transcript, _handoff_note(tenant, customer_id, owner, agent), now)
        state = TurnState()
        ctx = TurnContext(tenant, customer_id, session_id, agent, now)
        reply = run_agent(agent, ctx, state, user_turn)
        memory.append_message(tenant, customer_id, session_id, "agent", agent, reply, now)
        replies.append({"agent": agent, "text": reply})
        trace.extend(state.trace)
        if not state.handoff_to or hop == MAX_HOPS:
            break
        agent = state.handoff_to
        owner = coordination.get_owner(tenant, customer_id)

    owner = coordination.get_owner(tenant, customer_id)
    return {
        "session_id": session_id,
        "replies": replies,
        "owner": owner["owner"] if owner else "triage",
        "trace": trace,
        "memory": memory.context_pack(tenant, customer_id),
    }
