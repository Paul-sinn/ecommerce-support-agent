# graph/nodes/policy_scope_guard.py

from ..state import GraphState
from ..policy_store import is_category_allowed

# 인사/일반 멘트일 때는 차단 메시지 대신 안내 문구로 응답
OUT_OF_SCOPE_FRIENDLY = (
    "안녕하세요! 주문·결제·배송·환불 관련 문의만 도와드리고 있어요. "
    "무엇을 도와드릴까요?"
)

def policy_scope_guard(state: GraphState):
    category = state["category"]

    if not is_category_allowed(category):
        return {
            "policy_status": "OUT_OF_SCOPE",
            "policy_message": OUT_OF_SCOPE_FRIENDLY,
            "messages": [{"role": "assistant", "content": OUT_OF_SCOPE_FRIENDLY}],
        }

    return {
        "policy_status": "VALID",
        "policy_message": None
    }
