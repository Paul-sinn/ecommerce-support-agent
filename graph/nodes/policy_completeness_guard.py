from ..state import GraphState

FIELD_LABELS = {
    "order_id": "주문번호",
    "payment_id": "결제번호",
    "email": "이메일",
}


def _friendly_missing_message(missing_fields: list[str]) -> str:
    labels = [FIELD_LABELS.get(field, field) for field in missing_fields]
    joined = ", ".join(labels)
    return f"계속 진행하려면 {joined} 정보를 알려주세요."


def policy_completeness_guard(state: GraphState):
    if state.get("policy_status") == "OUT_OF_SCOPE":
        return {}

    missing_fields = state.get("missing_fields") or []

    if len(missing_fields) > 0:
        msg = _friendly_missing_message(missing_fields)
        return {
            "policy_status": "NEED_MORE_INFO",
            "policy_message": msg,
            "messages": [{"role": "assistant", "content": msg}],
        }

    return {
        "policy_status": "VALID",
        "policy_message": None,
    }
