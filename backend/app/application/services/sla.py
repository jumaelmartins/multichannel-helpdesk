from datetime import datetime, timedelta

from app.domain.enums import SlaState, TicketPriority

FIRST_RESPONSE_WINDOWS: dict[TicketPriority, timedelta] = {
    TicketPriority.CRITICAL: timedelta(hours=2),
    TicketPriority.HIGH: timedelta(hours=4),
    TicketPriority.MEDIUM: timedelta(hours=24),
    TicketPriority.LOW: timedelta(hours=48),
}

NEAR_DUE_THRESHOLD = 0.25


def first_response_due(priority: TicketPriority, created_at: datetime) -> datetime:
    return created_at + FIRST_RESPONSE_WINDOWS[priority]


def compute_sla_state(
    created_at: datetime,
    first_response_due_at: datetime | None,
    first_response_at: datetime | None,
    now: datetime,
) -> SlaState:
    if first_response_at is not None:
        return SlaState.MET
    if first_response_due_at is None:
        return SlaState.OK
    if now >= first_response_due_at:
        return SlaState.OVERDUE
    total = (first_response_due_at - created_at).total_seconds()
    remaining = (first_response_due_at - now).total_seconds()
    if total > 0 and remaining <= total * NEAR_DUE_THRESHOLD:
        return SlaState.NEAR_DUE
    return SlaState.OK
