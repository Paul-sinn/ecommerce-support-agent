from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph
from .state import GraphState
from langgraph.graph import START,END
from .nodes.triage_router import triage_router
from .nodes.policy_scope_guard import policy_scope_guard
from .nodes.policy_completeness_guard import policy_completeness_guard
from .nodes.policy_risk_guard import policy_risk_guard
from .nodes.order_agent import order_agent
from .nodes.billing_agent import billing_agent


def route_to_agent(state: GraphState) -> str:
    if state.get("policy_status") in {"OUT_OF_SCOPE", "NEED_MORE_INFO"}:
        return "end"

    category = state.get("category")

    if category == "order":
        return "order_agent"
    if category == "billing":
        return "billing_agent"

    return "end"


graph = StateGraph(GraphState)



graph.add_node("triage", triage_router)

graph.add_node("policy_scope", policy_scope_guard)
graph.add_node("policy_completeness", policy_completeness_guard)
graph.add_node("policy_risk", policy_risk_guard)

graph.add_node("order_agent", order_agent)
graph.add_node("billing_agent", billing_agent)


graph.set_entry_point("triage")

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
    }
)

graph.add_edge("order_agent", END)
graph.add_edge("billing_agent", END)


graph.compile()