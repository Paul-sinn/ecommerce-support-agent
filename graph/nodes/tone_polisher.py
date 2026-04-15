from ..llm.client import get_triage_llm
from ..state import GraphState


def tone_polisher(state: GraphState):
    reply = state.get("final_reply") or ""
    if not reply:
        return {}

    llm = get_triage_llm()

    prompt = f"""You are a customer service tone editor.

Rewrite the following customer support reply to be:
- Warm and professional
- Clear and concise
- Empathetic but not overly apologetic

Keep all factual content exactly the same. Do not add or remove information.
Do not add greetings or sign-offs.

Reply to polish:
"{reply}"

Return only the polished reply, nothing else."""

    response = llm.invoke(prompt)
    return {
        "final_reply": response.content,
        "messages": [{"role": "assistant", "content": response.content}],
    }
