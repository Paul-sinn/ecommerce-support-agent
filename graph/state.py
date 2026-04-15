from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    request_id: Optional[str]
    thread_id: Optional[str]

    # triage 결과
    category: Optional[str]
    priority: Optional[str]
    missing_fields: Optional[List[str]]

    # policy 결과
    policy_status: Optional[str]
    policy_message: Optional[str]
    policy_risk_level: Optional[str]
    escalation_required: Optional[bool]
    error_code: Optional[str]

    # 에이전트 policy 적합 판정
    eligible: Optional[bool]

    # 최종 응답
    final_reply: Optional[str]
    ticket_id: Optional[int]
