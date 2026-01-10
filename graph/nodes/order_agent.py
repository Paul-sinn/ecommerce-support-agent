from ..state import GraphState
from llm.client import get_llm_by_priority
from ..business_policy_store import BUSINESS_POLICIES

def order_agent(state: GraphState):
    inquiry = state["inquiry"]
    priority = state["priority"]

    assert priority is not None, "order_agent called before triage/policy"

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
