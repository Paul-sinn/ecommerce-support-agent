from ..state import GraphState

def policy_completeness_guard(state: GraphState):
    # scope에서 이미 막혔으면 그대로 전달 (인사 등 → OUT_OF_SCOPE 메시지 유지)
    if state.get("policy_status") == "OUT_OF_SCOPE":
        return {}

    missing_fields = state.get("missing_fields") or []

    if len(missing_fields) > 0:
        return {
            "policy_status": "NEED_MORE_INFO",
            "policy_message": f"Missing required fields: {', '.join(missing_fields)}"
        }

    return {
        "policy_status": "VALID",
        "policy_message": None
    }
