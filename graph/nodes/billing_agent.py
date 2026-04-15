import json

from graph.adapters.billing_repository import get_billing_context
from graph.llm.client import get_llm_by_priority

from ..business_policy_store import BUSINESS_POLICIES
from ..state import GraphState


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
    billing_context = get_billing_context(inquiry)

    llm = get_llm_by_priority(priority)

    refund_policy = BUSINESS_POLICIES["refund_window"]
    billing_dispute_policy = BUSINESS_POLICIES["billing_dispute_window"]
    account_policy = BUSINESS_POLICIES["account_verification"]

    prompt = f"""
You are a billing support agent for an e-commerce company.

Evaluate the customer's request against the company policies below and determine eligibility.

Company policies:
- {refund_policy["title"]}: {refund_policy["rule"]}
- {billing_dispute_policy["title"]}: {billing_dispute_policy["rule"]}
- {account_policy["title"]}: {account_policy["rule"]}

Rules:
- Do NOT invent new policies.
- Do NOT mention internal systems or workflows.
- CRITICAL: Always reply in the same language the customer used. If Korean, respond in Korean.

Customer inquiry:
"{inquiry}"

Billing lookup context:
- payment_id: {billing_context["payment_id"]}
- status: {billing_context["status"]}
- amount: {billing_context["amount"]}
- issue: {billing_context["issue"]}

Recent conversation context:
{conversation}

Return ONLY valid JSON in this exact format:
{{
  "eligible": true or false,
  "customer_message": "message to the customer explaining the assessment and what will happen next (or why it was rejected)"
}}
"""

    response = llm.invoke(prompt)

    result = None
    raw = response.content.strip()
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        result = None

    eligible = bool(result.get("eligible")) if result else False
    customer_message = (result or {}).get("customer_message") or raw

    return {
        "eligible": eligible,
        "final_reply": customer_message,
        "error_code": None,
    }
