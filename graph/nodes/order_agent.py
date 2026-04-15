import json

from graph.adapters.order_repository import get_order_context
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


def order_agent(state: GraphState):
    inquiry = _latest_user_text(state.get("messages"))
    conversation = _recent_conversation_text(state.get("messages"))
    priority = state["priority"]
    order_context = get_order_context(inquiry)

    llm = get_llm_by_priority(priority)

    cancel_policy = BUSINESS_POLICIES["post_delivery_cancellation"]
    pre_ship_cancel_policy = BUSINESS_POLICIES["pre_shipping_cancellation"]
    return_fee_policy = BUSINESS_POLICIES["return_shipping_fee"]
    damaged_policy = BUSINESS_POLICIES["damaged_item_policy"]

    prompt = f"""
You are an order support agent for an e-commerce company.

Evaluate the customer's request against the company policies below and determine eligibility.

Company policies:
- {cancel_policy["title"]}: {cancel_policy["rule"]}
- {pre_ship_cancel_policy["title"]}: {pre_ship_cancel_policy["rule"]}
- {return_fee_policy["title"]}: {return_fee_policy["rule"]}
- {damaged_policy["title"]}: {damaged_policy["rule"]}

Rules:
- Do NOT invent new policies.
- Do NOT promise actions that violate policy.
- CRITICAL: Always reply in the same language the customer used. If Korean, respond in Korean.

Customer inquiry:
"{inquiry}"

Order lookup context:
- order_id: {order_context["order_id"]}
- status: {order_context["status"]}
- eta: {order_context["eta"]}
- eligible_actions: {", ".join(order_context["eligible_actions"])}

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
