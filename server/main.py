"""Ninaivu API (FastAPI). Vercel picks up `app` from this file; locally: uvicorn main:app --reload --port 8000."""
from typing import Any, Callable

import anthropic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ninaivu import coordination, memory
from ninaivu.agents.curator import run_curator
from ninaivu.agents.orchestrator import handle_message
from ninaivu.config import TENANTS
from ninaivu.db import UnknownTenant, get_db, query_log

app = FastAPI(title="Ninaivu API")


@app.exception_handler(NotImplementedError)
async def not_implemented(_: Request, __: NotImplementedError) -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": "Not implemented yet (scaffold)."})


@app.exception_handler(UnknownTenant)
async def unknown_tenant(_: Request, exc: UnknownTenant) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Unknown tenant: {exc}"})


@app.exception_handler(memory.NotFound)
async def not_found(_: Request, exc: memory.NotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Not found: {exc}"})


@app.exception_handler(anthropic.APIError)
async def llm_error(_: Request, exc: anthropic.APIError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": f"Model call failed: {exc.message}"})


def _with_query_log(fn: Callable[..., dict], *args: Any) -> dict:
    """Run fn and attach the named Cypher queries it executed (for the Query Inspector)."""
    token = query_log.set([])
    try:
        result = fn(*args)
        result["queries"] = query_log.get()
        return result
    finally:
        query_log.reset(token)


class ChatRequest(BaseModel):
    tenant: str
    customer_id: str
    session_id: str | None = None
    message: str
    clock_offset_days: float = 0


class EndSessionRequest(BaseModel):
    tenant: str
    customer_id: str
    session_id: str
    clock_offset_days: float = 0


@app.get("/api/health")
def health() -> dict:
    try:
        get_db().list_graphs()
        status = "ok"
    except Exception as exc:  # report, don't crash, so the deploy check stays useful
        status = f"unreachable: {type(exc).__name__}"
    return {"ok": True, "falkordb": status}


@app.get("/api/tenants")
def tenants() -> list[dict]:
    return [{"id": tid, "name": name} for tid, name in TENANTS.items()]


@app.get("/api/customers")
def customers(tenant: str) -> list[dict]:
    return memory.list_customers(tenant)


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    return _with_query_log(handle_message, req.tenant, req.customer_id, req.session_id, req.message, req.clock_offset_days)


@app.post("/api/sessions/end")
def end_session(req: EndSessionRequest) -> dict:
    return _with_query_log(run_curator, req.tenant, req.customer_id, req.session_id, req.clock_offset_days)


@app.get("/api/memory")
def memory_pack(tenant: str, customer_id: str) -> dict:
    return memory.context_pack(tenant, customer_id)


@app.get("/api/graph")
def graph(tenant: str, customer_id: str) -> dict:
    return memory.customer_graph(tenant, customer_id)


@app.get("/api/trace")
def trace(tenant: str, customer_id: str, issue_id: str) -> list[dict]:
    return coordination.explain_trace(tenant, customer_id, issue_id)
