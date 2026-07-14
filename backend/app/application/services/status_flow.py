from app.core.exceptions import DomainValidationError
from app.domain.enums import TicketStatus

ACTIVE_STATUSES = {
    TicketStatus.OPEN,
    TicketStatus.IN_ANALYSIS,
    TicketStatus.IN_PROGRESS,
    TicketStatus.WAITING_CUSTOMER,
    TicketStatus.WAITING_INTERNAL,
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    if current == target:
        return False
    if current in ACTIVE_STATUSES:
        return target in ACTIVE_STATUSES or target in (
            TicketStatus.RESOLVED,
            TicketStatus.CANCELLED,
        )
    if current == TicketStatus.RESOLVED:
        return target in (TicketStatus.CLOSED, TicketStatus.OPEN)
    if current == TicketStatus.CLOSED:
        return target == TicketStatus.OPEN
    return False  # cancelled is terminal


def assert_transition(current: TicketStatus, target: TicketStatus) -> None:
    if not can_transition(current, target):
        raise DomainValidationError(f"Invalid status transition: {current} -> {target}")
