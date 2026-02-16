import json
from langchain.chat_models import init_chat_model
from ..state import GraphState
from ..llm.client import get_triage_llm

llm = get_triage_llm()

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


def triage_router(state: GraphState):
    inquiry = _latest_user_text(state.get("messages"))
    
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
