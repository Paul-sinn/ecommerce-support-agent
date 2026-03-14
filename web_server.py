from uuid import uuid4

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


from graph.nodes.billing_agent import billing_agent
from graph.nodes.order_agent import order_agent
from graph.nodes.policy_completeness_guard import policy_completeness_guard
from graph.nodes.policy_risk_guard import policy_risk_guard
from graph.nodes.policy_scope_guard import policy_scope_guard
from graph.nodes.triage_router import triage_router
from graph.state import GraphState

load_dotenv()

app = FastAPI(title="NeoMall Support API")


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    source: str | None = None  # 디버깅: order_agent | billing_agent | policy_scope_guard | ...
    category: str | None = None
    policy_status: str | None = None
    policy_message: str | None = None


def route_to_agent(state: GraphState) -> str:
    if state.get("policy_status") in {"OUT_OF_SCOPE", "NEED_MORE_INFO"}:
        return "end"

    category = state.get("category")
    if category == "order":
        return "order_agent"
    if category == "billing":
        return "billing_agent"
    return "end"


def build_graph_app():
    graph = StateGraph(GraphState)
    graph.add_node("triage", triage_router)
    graph.add_node("policy_scope", policy_scope_guard)
    graph.add_node("policy_completeness", policy_completeness_guard)
    graph.add_node("policy_risk", policy_risk_guard)
    graph.add_node("order_agent", order_agent)
    graph.add_node("billing_agent", billing_agent)

    graph.add_edge(START, "triage")
    graph.add_edge("triage", "policy_scope")
    graph.add_edge("policy_scope", "policy_completeness")
    graph.add_edge("policy_completeness", "policy_risk")
    graph.add_conditional_edges(
        "policy_risk",
        route_to_agent,
        {
            "order_agent": "order_agent",
            "billing_agent": "billing_agent",
            "end": END,
        },
    )
    graph.add_edge("order_agent", END)
    graph.add_edge("billing_agent", END)

    return graph.compile(checkpointer=MemorySaver())


graph_app = build_graph_app()

app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def root() -> FileResponse:
    return FileResponse("web/index.html")


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    thread_id = payload.thread_id or f"thread-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    result = graph_app.invoke(
        {"messages": [{"role": "user", "content": payload.message}]},
        config=config,
    )

    # main.py와 동일: final_reply 우선, 없으면 policy_message (인사 시 친절 메시지 등)
    category = result.get("category")
    policy_status = result.get("policy_status")
    reply = result.get("final_reply") or result.get("policy_message")
    if not reply:
        reply = "(응답 없음)"

    # 디버깅용 source (main.py와 동일 로직)
    if result.get("final_reply"):
        source = "order_agent" if category == "order" else "billing_agent" if category == "billing" else "agent"
    elif policy_status == "OUT_OF_SCOPE":
        source = "policy_scope_guard"
    elif policy_status == "NEED_MORE_INFO":
        source = "policy_completeness_guard"
    else:
        source = "end (no agent)"

    return ChatResponse(
        thread_id=thread_id,
        reply=reply,
        source=source,
        category=category,
        policy_status=policy_status,
        policy_message=result.get("policy_message"),
    )
