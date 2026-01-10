# graph/nodes/policy_scope_guard.py

from ..state import GraphState
from ..policy_store import is_category_allowed

def policy_scope_guard(state: GraphState):
    category = state["category"]

    if not is_category_allowed(category):
        return {
            "policy_status": "OUT_OF_SCOPE",
            "policy_message": "This request is outside supported domains."
        }

    return {
        "policy_status": "VALID",
        "policy_message": None
    }
