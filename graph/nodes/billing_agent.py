from ..state import GraphState
from llm.client import get_llm_by_priority
from ..business_policy_store import BUSINESS_POLICIES

def billing_agent(state: GraphState):
    inquiry = state["inquiry"]
    priority = state["priority"]

    assert priority is not None, "billing_agent called before triage/policy"

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
"""

    response = llm.invoke(prompt)

    return {
        "final_reply": response.content
    }
