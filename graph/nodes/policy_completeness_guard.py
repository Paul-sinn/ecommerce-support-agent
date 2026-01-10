from ..state import GraphState

def policy_completeness_guard(state: GraphState):
    missing_fields = state["missing_fields"]

    # triage 이후 노드라는 계약
    assert missing_fields is not None, "policy_completeness_guard called before triage"

    if len(missing_fields) > 0:
        return {
            "policy_status": "NEED_MORE_INFO",
            "policy_message": f"Missing required fields: {', '.join(missing_fields)}"
        }

    return {
        "policy_status": "VALID",
        "policy_message": None
    }
