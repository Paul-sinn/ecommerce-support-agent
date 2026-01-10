from langgraph.graph import StateGraph
from langchain.chat_models import init_chat_model
from typing import List, Optional, TypedDict

llm = init_chat_model("openai:gpt-4o")

class GraphState(TypedDict):
    inquiry: str

    # triage 결과
    category: Optional[str]
    priority: Optional[str]
    missing_fields: Optional[List[str]]


    # policy 결과
    policy_status: Optional[str]  # VALID | OUT_OF_SCOPE | POLICY_LIMIT | MISSING_INFO
    policy_message: Optional[str]
    policy_risk_level: Optional[str]


    # 최종 응답
    final_reply: Optional[str]

