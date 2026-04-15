from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.billing_agent import billing_agent
from .nodes.fallback_agent import fallback_agent
from .nodes.order_agent import order_agent
from .nodes.policy_completeness_guard import policy_completeness_guard
from .nodes.policy_risk_guard import policy_risk_guard
from .nodes.policy_scope_guard import policy_scope_guard
from .nodes.ticket_writer import ticket_writer
from .nodes.triage_router import triage_router
from .state import GraphState


def route_to_agent(state: GraphState) -> str:
    if state.get("policy_status") in {"OUT_OF_SCOPE", "NEED_MORE_INFO"}:
        return "end"

    category = state.get("category")
    if category == "order":
        return "order_agent"
    if category == "billing":
        return "billing_agent"
    return "fallback_agent"


def route_to_ticket(state: GraphState) -> str:
    return "ticket_writer" if state.get("eligible") else "end"


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("triage", triage_router)
    graph.add_node("policy_scope", policy_scope_guard)
    graph.add_node("policy_completeness", policy_completeness_guard)
    graph.add_node("policy_risk", policy_risk_guard)
    graph.add_node("order_agent", order_agent)
    graph.add_node("billing_agent", billing_agent)
    graph.add_node("fallback_agent", fallback_agent)
    graph.add_node("ticket_writer", ticket_writer)

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
            "fallback_agent": "fallback_agent",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "order_agent",
        route_to_ticket,
        {"ticket_writer": "ticket_writer", "end": END},
    )
    graph.add_conditional_edges(
        "billing_agent",
        route_to_ticket,
        {"ticket_writer": "ticket_writer", "end": END},
    )
    graph.add_edge("ticket_writer", END)
    graph.add_edge("fallback_agent", END)
    return graph


def compile_graph(*, checkpointer=None):
    graph = build_graph()
    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()
