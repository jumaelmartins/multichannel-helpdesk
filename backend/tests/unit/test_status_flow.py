import pytest

from app.application.services.status_flow import assert_transition, can_transition
from app.core.exceptions import DomainValidationError
from app.domain.enums import TicketStatus as S


def test_active_statuses_transition_freely():
    active = [S.OPEN, S.IN_ANALYSIS, S.IN_PROGRESS, S.WAITING_CUSTOMER, S.WAITING_INTERNAL]
    for a in active:
        for b in active:
            if a != b:
                assert can_transition(a, b), f"{a} -> {b} should be allowed"


def test_active_can_resolve_and_cancel():
    assert can_transition(S.OPEN, S.RESOLVED)
    assert can_transition(S.IN_PROGRESS, S.CANCELLED)


def test_resolved_can_close_or_reopen():
    assert can_transition(S.RESOLVED, S.CLOSED)
    assert can_transition(S.RESOLVED, S.OPEN)


def test_closed_can_only_reopen():
    assert can_transition(S.CLOSED, S.OPEN)
    assert not can_transition(S.CLOSED, S.IN_PROGRESS)
    assert not can_transition(S.CLOSED, S.RESOLVED)


def test_cancelled_is_terminal():
    for target in S:
        assert not can_transition(S.CANCELLED, target)


def test_same_status_is_invalid():
    assert not can_transition(S.OPEN, S.OPEN)


def test_resolved_cannot_jump_to_active_except_open():
    assert not can_transition(S.RESOLVED, S.IN_PROGRESS)


def test_assert_transition_raises_on_invalid():
    with pytest.raises(DomainValidationError):
        assert_transition(S.CLOSED, S.IN_PROGRESS)


def test_assert_transition_passes_on_valid():
    assert_transition(S.OPEN, S.IN_ANALYSIS)
