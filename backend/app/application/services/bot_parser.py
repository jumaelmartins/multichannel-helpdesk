import re
import unicodedata
from dataclasses import dataclass

from app.domain.enums import TicketPriority, TicketStatus

HELP_TEXT = (
    "Available commands:\n"
    "/chamados abertos\n"
    "/chamados criticos\n"
    "/ver HD-0001\n"
    "/status HD-0001 em_analise\n"
    "/prioridade HD-0001 alta\n"
    "/responder HD-0001 <message>\n"
    "/resolver HD-0001 <message>\n"
    "/atribuir HD-0001 <agent>"
)

STATUS_ALIASES = {
    "aberto": TicketStatus.OPEN,
    "em_analise": TicketStatus.IN_ANALYSIS,
    "em_andamento": TicketStatus.IN_PROGRESS,
    "aguardando_cliente": TicketStatus.WAITING_CUSTOMER,
    "aguardando_interno": TicketStatus.WAITING_INTERNAL,
    "resolvido": TicketStatus.RESOLVED,
    "fechado": TicketStatus.CLOSED,
    "cancelado": TicketStatus.CANCELLED,
}

PRIORITY_ALIASES = {
    "baixa": TicketPriority.LOW,
    "media": TicketPriority.MEDIUM,
    "alta": TicketPriority.HIGH,
    "critica": TicketPriority.CRITICAL,
}

CODE_PATTERN = re.compile(r"^hd-\d+$", re.IGNORECASE)


class BotParseError(Exception):
    def __init__(self, message: str):
        super().__init__(f"{message}\n\n{HELP_TEXT}")
        self.message = message


@dataclass
class ParsedCommand:
    action: str
    code: str | None = None
    value: str | None = None
    text: str | None = None


def _strip_accents(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )


def _parse_code(raw: str) -> str:
    if not CODE_PATTERN.match(raw):
        raise BotParseError(f"Invalid ticket code: {raw}")
    return raw.upper()


def _parse_status(raw: str) -> TicketStatus:
    normalized = _strip_accents(raw.lower())
    if normalized in STATUS_ALIASES:
        return STATUS_ALIASES[normalized]
    try:
        return TicketStatus(normalized)
    except ValueError as exc:
        raise BotParseError(f"Unknown status: {raw}") from exc


def _parse_priority(raw: str) -> TicketPriority:
    normalized = _strip_accents(raw.lower())
    if normalized in PRIORITY_ALIASES:
        return PRIORITY_ALIASES[normalized]
    try:
        return TicketPriority(normalized)
    except ValueError as exc:
        raise BotParseError(f"Unknown priority: {raw}") from exc


def parse_command(text: str) -> ParsedCommand:
    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        raise BotParseError("Commands must start with /")

    command, args = parts[0].lower(), parts[1:]

    if command == "/chamados":
        if not args:
            raise BotParseError("Usage: /chamados abertos|criticos")
        subject = _strip_accents(args[0].lower())
        if subject == "abertos":
            return ParsedCommand(action="list_open")
        if subject == "criticos":
            return ParsedCommand(action="list_critical")
        raise BotParseError(f"Unknown list: {args[0]}")

    if command in ("/ver", "/status", "/prioridade", "/responder", "/resolver", "/atribuir"):
        if not args:
            raise BotParseError(f"Usage: {command} HD-0001 ...")
        code = _parse_code(args[0])
        rest = args[1:]

        if command == "/ver":
            return ParsedCommand(action="view", code=code)

        if command == "/status":
            if not rest:
                raise BotParseError("Usage: /status HD-0001 <status>")
            return ParsedCommand(action="set_status", code=code, value=_parse_status(rest[0]))

        if command == "/prioridade":
            if not rest:
                raise BotParseError("Usage: /prioridade HD-0001 <priority>")
            return ParsedCommand(action="set_priority", code=code, value=_parse_priority(rest[0]))

        if command == "/responder":
            if not rest:
                raise BotParseError("Usage: /responder HD-0001 <message>")
            return ParsedCommand(action="reply", code=code, text=" ".join(rest))

        if command == "/resolver":
            if not rest:
                raise BotParseError("Usage: /resolver HD-0001 <message>")
            return ParsedCommand(action="resolve", code=code, text=" ".join(rest))

        if command == "/atribuir":
            if not rest:
                raise BotParseError("Usage: /atribuir HD-0001 <agent>")
            return ParsedCommand(action="assign", code=code, value=rest[0])

    raise BotParseError(f"Unknown command: {command}")
