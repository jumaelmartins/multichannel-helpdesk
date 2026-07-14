from datetime import UTC, datetime, timedelta

from app.application.services.sla import compute_sla_state, first_response_due
from app.domain.enums import SlaState, TicketPriority

CREATED = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)


def test_first_response_due_critical_is_2h():
    assert first_response_due(TicketPriority.CRITICAL, CREATED) == CREATED + timedelta(hours=2)


def test_first_response_due_high_is_4h():
    assert first_response_due(TicketPriority.HIGH, CREATED) == CREATED + timedelta(hours=4)


def test_first_response_due_medium_is_24h():
    assert first_response_due(TicketPriority.MEDIUM, CREATED) == CREATED + timedelta(hours=24)


def test_first_response_due_low_is_48h():
    assert first_response_due(TicketPriority.LOW, CREATED) == CREATED + timedelta(hours=48)


def test_state_met_when_first_response_recorded():
    due = CREATED + timedelta(hours=4)
    state = compute_sla_state(
        created_at=CREATED,
        first_response_due_at=due,
        first_response_at=CREATED + timedelta(hours=1),
        now=CREATED + timedelta(hours=10),
    )
    assert state == SlaState.MET


def test_state_ok_when_plenty_of_time_left():
    due = CREATED + timedelta(hours=4)
    state = compute_sla_state(
        created_at=CREATED,
        first_response_due_at=due,
        first_response_at=None,
        now=CREATED + timedelta(hours=1),
    )
    assert state == SlaState.OK


def test_state_near_due_when_remaining_at_most_25_percent():
    due = CREATED + timedelta(hours=4)
    state = compute_sla_state(
        created_at=CREATED,
        first_response_due_at=due,
        first_response_at=None,
        now=CREATED + timedelta(hours=3, minutes=30),
    )
    assert state == SlaState.NEAR_DUE


def test_state_overdue_when_past_due_without_response():
    due = CREATED + timedelta(hours=4)
    state = compute_sla_state(
        created_at=CREATED,
        first_response_due_at=due,
        first_response_at=None,
        now=CREATED + timedelta(hours=5),
    )
    assert state == SlaState.OVERDUE


def test_state_ok_when_no_due_date():
    state = compute_sla_state(
        created_at=CREATED,
        first_response_due_at=None,
        first_response_at=None,
        now=CREATED,
    )
    assert state == SlaState.OK
