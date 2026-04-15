import json

from ..llm.client import get_triage_llm
from ..state import GraphState

ALLOWED_CATEGORIES = {"order", "billing", "account", "technical", "unknown"}
ALLOWED_PRIORITIES = {"low", "medium", "high"}


def _safe_json_loads(raw_content: str):
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(raw_content[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def _fallback_triage(inquiry: str) -> dict:
    text = (inquiry or "").lower()
    category = "unknown"
    priority = "medium"
    missing_fields = []

    ORDER_KEYWORDS = {"order", "delivery", "shipping", "cancel", "return",
                      "주문", "배송", "취소", "반품", "교환", "배달"}
    BILLING_KEYWORDS = {"refund", "payment", "charge", "invoice", "billing",
                        "환불", "결제", "청구", "쿠폰", "중복", "이중"}

    if any(keyword in text for keyword in ORDER_KEYWORDS):
        category = "order"
        if "ord-" not in text and not any(k in text for k in {"주문번호", "ord"}):
            missing_fields.append("order_id")
    elif any(keyword in text for keyword in BILLING_KEYWORDS):
        category = "billing"
        if "pay-" not in text and not any(k in text for k in {"결제번호", "pay"}):
            missing_fields.append("payment_id")

    HIGH_KEYWORDS = {"charged twice", "duplicate", "payment failed", "missing order", "system error",
                     "이중결제", "중복결제", "결제실패", "주문누락"}
    MEDIUM_KEYWORDS = {"refund", "shipping delay", "cancel", "return",
                       "환불", "배송지연", "취소", "반품"}

    if any(keyword in text for keyword in HIGH_KEYWORDS):
        priority = "high"
    elif any(keyword in text for keyword in MEDIUM_KEYWORDS):
        priority = "medium"
    else:
        priority = "low" if category == "unknown" else priority

    return {
        "category": category,
        "priority": priority,
        "missing_fields": missing_fields,
    }


def _normalize_result(result: dict | None, inquiry: str) -> dict:
    fallback = _fallback_triage(inquiry)
    if not isinstance(result, dict):
        return fallback

    category = result.get("category")
    priority = result.get("priority")
    missing_fields = result.get("missing_fields")

    if category not in ALLOWED_CATEGORIES:
        category = fallback["category"]
    if priority not in ALLOWED_PRIORITIES:
        priority = fallback["priority"]
    if not isinstance(missing_fields, list):
        missing_fields = fallback["missing_fields"]

    return {
        "category": category,
        "priority": priority,
        "missing_fields": [str(field) for field in missing_fields],
    }


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


def triage_router(state: GraphState):
    llm = get_triage_llm()
    inquiry = _latest_user_text(state.get("messages"))
    conversation = _recent_conversation_text(state.get("messages"))

    prompt = f"""
            You are a triage agent for an e-commerce customer support system.

    Your job is NOT to answer the customer.
    Your job is ONLY to analyze the inquiry and extract structured information.

    You must classify the inquiry into:
    - category
    - priority
    - missing_fields

    Follow these rules strictly:
    - Do NOT explain policies.
    - Do NOT reject or approve requests.
    - Do NOT generate customer-facing responses.
    - Only return valid JSON. No extra text.

    Categories (choose ONE):
    - order: orders, shipping, delivery status, cancellations, returns
    - billing: payments, refunds, charges, invoices, coupons
    - account: login, password, account info, profile
    - technical: website/app errors, bugs, checkout issues
    - unknown: not related to e-commerce customer support

    Priority (choose ONE):
    - high: payment issues, duplicate charges, missing orders, system errors
    - medium: shipping delays, refund requests, order changes
    - low: general questions, information requests

    Missing fields:
    - Identify information required to proceed but not provided.
    - Common examples: order_id, email, payment_id
    - If nothing is missing, return an empty list.

    Customer inquiry:
    "{inquiry}"

    Recent conversation context:
    {conversation}

    Return JSON in this format:
    {{
    "category": "",
    "priority": "",
    "missing_fields": []
    }}
    """

    response = llm.invoke(prompt)
    result = _normalize_result(_safe_json_loads(response.content), inquiry)

    return {
        "category": result["category"],
        "priority": result["priority"],
        "missing_fields": result["missing_fields"],
    }
