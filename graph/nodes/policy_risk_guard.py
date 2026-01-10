from ..state import GraphState

HIGH_RISK_CATEGORIES = {"billing"}
HIGH_RISK_PRIORITIES = {"high"}

def policy_risk_guard(state: GraphState):
    category = state["category"]
    priority = state["priority"]

    # triage 이후라는 계약
    assert category is not None, "policy_risk_guard called before triage"
    assert priority is not None, "policy_risk_guard called before triage"

    # 기본값
    risk_level = "LOW"

    if category in HIGH_RISK_CATEGORIES and priority in HIGH_RISK_PRIORITIES:
        risk_level = "HIGH"

    return {
        "policy_risk_level": risk_level
    }
