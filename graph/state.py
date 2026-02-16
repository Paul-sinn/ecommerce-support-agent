from typing import Annotated, List, Optional, TypedDict
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

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
