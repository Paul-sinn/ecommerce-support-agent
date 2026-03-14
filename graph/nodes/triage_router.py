import json
from langchain.chat_models import init_chat_model
from ..state import GraphState
from ..llm.client import get_triage_llm

llm = get_triage_llm()

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
    - Say hello to the user When the user is the first message.
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
    result = json.loads(response.content)

    return {
        "category": result["category"],
        "priority": result["priority"],
        "missing_fields": result["missing_fields"],
    }
