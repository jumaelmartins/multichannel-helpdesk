import pytest

from app.application.services.bot_parser import BotParseError, parse_command
from app.domain.enums import TicketPriority, TicketStatus


def test_list_open_tickets():
    cmd = parse_command("/chamados abertos")
    assert cmd.action == "list_open"


def test_list_critical_tickets():
    cmd = parse_command("/chamados criticos")
    assert cmd.action == "list_critical"


def test_list_critical_accepts_accent():
    cmd = parse_command("/chamados críticos")
    assert cmd.action == "list_critical"


def test_view_ticket():
    cmd = parse_command("/ver HD-0001")
    assert cmd.action == "view"
    assert cmd.code == "HD-0001"


def test_view_ticket_lowercase_code():
    cmd = parse_command("/ver hd-0001")
    assert cmd.code == "HD-0001"


def test_set_status_with_pt_alias():
    cmd = parse_command("/status HD-0001 em_analise")
    assert cmd.action == "set_status"
    assert cmd.code == "HD-0001"
    assert cmd.value == TicketStatus.IN_ANALYSIS


def test_set_status_with_enum_value():
    cmd = parse_command("/status HD-0002 waiting_customer")
    assert cmd.value == TicketStatus.WAITING_CUSTOMER


def test_set_status_invalid_value_raises():
    with pytest.raises(BotParseError):
        parse_command("/status HD-0001 banana")


def test_set_priority_with_pt_alias():
    cmd = parse_command("/prioridade HD-0001 alta")
    assert cmd.action == "set_priority"
    assert cmd.value == TicketPriority.HIGH


def test_set_priority_critical_accent():
    cmd = parse_command("/prioridade HD-0001 crítica")
    assert cmd.value == TicketPriority.CRITICAL


def test_reply_keeps_full_message():
    cmd = parse_command("/responder HD-0001 Estamos analisando sua solicitação.")
    assert cmd.action == "reply"
    assert cmd.code == "HD-0001"
    assert cmd.text == "Estamos analisando sua solicitação."


def test_resolve_requires_message():
    with pytest.raises(BotParseError):
        parse_command("/resolver HD-0001")


def test_resolve_with_message():
    cmd = parse_command("/resolver HD-0001 Ajuste realizado. Pode validar novamente.")
    assert cmd.action == "resolve"
    assert cmd.text == "Ajuste realizado. Pode validar novamente."


def test_assign_ticket():
    cmd = parse_command("/atribuir HD-0001 jumael")
    assert cmd.action == "assign"
    assert cmd.code == "HD-0001"
    assert cmd.value == "jumael"


def test_unknown_command_raises_with_help():
    with pytest.raises(BotParseError) as exc:
        parse_command("/foo bar")
    assert "/ver" in str(exc.value)


def test_empty_input_raises():
    with pytest.raises(BotParseError):
        parse_command("   ")


def test_missing_code_raises():
    with pytest.raises(BotParseError):
        parse_command("/ver")
