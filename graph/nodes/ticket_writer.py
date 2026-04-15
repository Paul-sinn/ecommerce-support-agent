from __future__ import annotations

import logging

from graph.db.models import SupportTicket
from graph.db.session import SessionLocal

from ..state import GraphState

logger = logging.getLogger("support_api")

CUSTOMER_CLOSING_MESSAGE = (
    "담당자에게 문의가 접수되었습니다. "
    "등록하신 이메일로 담당자가 직접 연락드릴 예정입니다."
)


def _latest_user_text(messages) -> str:
    for msg in reversed(messages or []):
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("type")
            content = msg.get("content", "")
        else:
            role = getattr(msg, "type", None) or getattr(msg, "role", None)
            content = getattr(msg, "content", "")
        if role in {"user", "human"}:
            return content
    return ""


def ticket_writer(state: GraphState) -> dict:
    customer_inquiry = _latest_user_text(state.get("messages"))
    agent_summary = state.get("final_reply") or ""

    ticket_id = None
    try:
        with SessionLocal() as session:
            ticket = SupportTicket(
                thread_id=state.get("thread_id") or "",
                request_id=state.get("request_id") or "",
                category=state.get("category") or "",
                priority=state.get("priority") or "",
                risk_level=state.get("policy_risk_level") or "LOW",
                escalation_required=bool(state.get("escalation_required")),
                customer_inquiry=customer_inquiry,
                agent_summary=agent_summary,
                status="pending_review",
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            ticket_id = ticket.id
            logger.info("ticket_created ticket_id=%s thread_id=%s", ticket_id, state.get("thread_id"))
    except Exception:
        logger.exception("ticket_write_failed thread_id=%s", state.get("thread_id"))

    return {
        "ticket_id": ticket_id,
        "final_reply": CUSTOMER_CLOSING_MESSAGE,
        "messages": [{"role": "assistant", "content": CUSTOMER_CLOSING_MESSAGE}],
    }
