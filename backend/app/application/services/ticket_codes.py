CODE_PREFIX = "HD"


def format_ticket_code(sequence: int) -> str:
    return f"{CODE_PREFIX}-{sequence:04d}"
