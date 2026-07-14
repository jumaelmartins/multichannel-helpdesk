from app.application.services.ticket_codes import format_ticket_code


def test_pads_to_four_digits():
    assert format_ticket_code(1) == "HD-0001"


def test_keeps_larger_sequences():
    assert format_ticket_code(12345) == "HD-12345"


def test_sequence_42():
    assert format_ticket_code(42) == "HD-0042"
