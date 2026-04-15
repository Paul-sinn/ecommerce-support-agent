import logging
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from graph.config import get_settings
from graph.db.models import SupportTicket
from graph.db.session import SessionLocal, init_db
from graph.workflow import compile_graph

settings = get_settings()
logger = logging.getLogger("support_api")
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(title="NeoMall Support API")
graph_app = compile_graph(checkpointer=MemorySaver())


@app.on_event("startup")
def startup() -> None:
    init_db()


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    request_id: str
    reply: str
    source: str | None = None
    category: str | None = None
    policy_status: str | None = None
    policy_message: str | None = None
    escalation_required: bool = False
    ticket_id: int | None = None


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id

    logger.info("request_started path=%s method=%s request_id=%s", request.url.path, request.method, request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info("request_completed path=%s status=%s request_id=%s", request.url.path, response.status_code, request_id)
    return response


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("unexpected_error request_id=%s", getattr(request.state, "request_id", "unknown"))
    return JSONResponse(
        status_code=500,
        content={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_code": "internal_error",
            "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        },
    )


def _check_api_key(x_api_key: str | None):
    if settings.demo_mode or not settings.api_auth_enabled:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _resolve_source(result: dict) -> str:
    category = result.get("category")
    policy_status = result.get("policy_status")
    if result.get("final_reply"):
        if category == "order":
            return "order_agent"
        if category == "billing":
            return "billing_agent"
        return "agent"
    if policy_status == "OUT_OF_SCOPE":
        return "policy_scope_guard"
    if policy_status == "NEED_MORE_INFO":
        return "policy_completeness_guard"
    return "end (no agent)"


app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def root() -> FileResponse:
    return FileResponse("web/index.html")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "auth_enabled": settings.api_auth_enabled and not settings.demo_mode,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, x_api_key: str | None = Header(default=None)) -> ChatResponse:
    _check_api_key(x_api_key)

    request_id = request.state.request_id
    thread_id = payload.thread_id or f"thread-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    result = graph_app.invoke(
        {
            "messages": [{"role": "user", "content": payload.message}],
            "thread_id": thread_id,
            "request_id": request_id,
        },
        config=config,
    )

    reply = result.get("final_reply") or result.get("policy_message") or "(응답 없음)"
    return ChatResponse(
        thread_id=thread_id,
        request_id=request_id,
        reply=reply,
        source=_resolve_source(result),
        category=result.get("category"),
        policy_status=result.get("policy_status"),
        policy_message=result.get("policy_message"),
        escalation_required=bool(result.get("escalation_required")),
        ticket_id=result.get("ticket_id"),
    )


@app.get("/api/tickets")
def list_tickets(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> list[dict]:
    with SessionLocal() as session:
        query = session.query(SupportTicket)
        if status:
            query = query.filter(SupportTicket.status == status)
        tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "thread_id": t.thread_id,
            "created_at": t.created_at.isoformat(),
            "category": t.category,
            "priority": t.priority,
            "risk_level": t.risk_level,
            "escalation_required": t.escalation_required,
            "customer_inquiry": t.customer_inquiry,
            "agent_summary": t.agent_summary,
            "status": t.status,
        }
        for t in tickets
    ]
