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


def billing_agent(state: GraphState):
    inquiry = _latest_user_text(state.get("messages"))
    conversation = _recent_conversation_text(state.get("messages"))
    priority = state["priority"]

    llm = get_llm_by_priority(priority)

    refund_policy = BUSINESS_POLICIES["refund_window"]
    billing_dispute_policy = BUSINESS_POLICIES["billing_dispute_window"]
    account_policy = BUSINESS_POLICIES["account_verification"]

    prompt = f"""
You are a billing support agent for an e-commerce company.

Your job is to explain billing-related issues clearly and politely,
using company policies as the basis for your explanation.

Company policies you must follow:
- {refund_policy["title"]}: {refund_policy["rule"]}
- {billing_dispute_policy["title"]}: {billing_dispute_policy["rule"]}
- {account_policy["title"]}: {account_policy["rule"]}

Rules:
- Do NOT invent new policies.
- Do NOT mention internal systems or workflows.
- If a request cannot be fulfilled, explain why using the policy and offer alternatives if appropriate.

Customer inquiry:
"{inquiry}"

Recent conversation context:
{conversation}
"""

    response = llm.invoke(prompt)

    return {
        "final_reply": response.content
    }
