from ..state import GraphState
from graph.llm.client import get_llm_by_priority
from ..business_policy_store import BUSINESS_POLICIES

def _latest_user_text(messages):
    for msg in reversed(messages or []):
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("type")
            if role in {"user", "human"}:
                return msg.get("content", "")
        else:
            role = getattr(msg, "type", None)
            if role in {"user", "human"}:
                return getattr(msg, "content", "")
    return ""


def order_agent(state: GraphState):
    inquiry = _latest_user_text(state.get("messages"))
    priority = state["priority"]

    llm = get_llm_by_priority(priority)

    delivery_cancel_policy = BUSINESS_POLICIES["post_delivery_cancellation"]
    digital_policy = BUSINESS_POLICIES["digital_goods"]

    prompt = f"""
You are an order support agent for an e-commerce company.

Your job is to assist with order and shipping-related issues,
using company policies as the basis for your explanations.

Company policies you must follow:
- {delivery_cancel_policy["title"]}: {delivery_cancel_policy["rule"]}
- {digital_policy["title"]}: {digital_policy["rule"]}

Rules:
- Do NOT invent new policies.
- Do NOT promise refunds or cancellations that violate policy.
- Explain policies clearly and respectfully.
- If the request cannot be fulfilled, suggest allowed alternatives.

Customer inquiry:
"{inquiry}"
"""

    response = llm.invoke(prompt)

    return {
        "final_reply": response.content
    }
