from ..state import GraphState
from graph.llm.client import get_llm_by_priority
from ..business_policy_store import BUSINESS_POLICIES

def _message_role_and_content(msg):
    if isinstance(msg, dict):
        role = msg.get("role") or msg.get("type")
        content = msg.get("content", "")
        return role, content
    role = getattr(msg, "type", None) or getattr(msg, "role", None)
    content = getattr(msg, "content", "")
    return role, content


def _latest_user_text(messages):
    for msg in reversed(messages or []):
        role, content = _message_role_and_content(msg)
        if role in {"user", "human"}:
            return content
    return ""

def _recent_conversation_text(messages, limit=8):
    rows = []
    for msg in (messages or [])[-limit:]:
        role, content = _message_role_and_content(msg)
        if role in {"user", "human"}:
            rows.append(f"USER: {content}")
        elif role in {"assistant", "ai"}:
            rows.append(f"ASSISTANT: {content}")
    return "\n".join(rows)


def order_agent(state: GraphState):
    inquiry = _latest_user_text(state.get("messages"))
    conversation = _recent_conversation_text(state.get("messages"))
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

Recent conversation context:
{conversation}
"""

    response = llm.invoke(prompt)

    return {
        "final_reply": response.content
    }
