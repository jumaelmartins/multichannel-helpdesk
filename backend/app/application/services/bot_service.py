from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.application.services.bot_parser import BotParseError, ParsedCommand, parse_command
from app.application.services.ticket_service import TicketService
from app.core.exceptions import AppError
from app.domain.enums import SenderType, UserRole
from app.infra.database.repositories.user_repository import UserRepository

ADMIN_ONLY_ACTIONS = {"set_priority", "assign"}


def _line(ticket: dict[str, Any]) -> str:
    assignee = ticket.get("assigned_to_name") or "unassigned"
    return (
        f"{ticket['code']} [{ticket['priority']}] {ticket['title']} "
        f"— {ticket['status']} — {assignee}"
    )


class BotService:
    def __init__(self, db: AsyncDatabase):
        self.tickets = TicketService(db)
        self.users = UserRepository(db)

    async def execute(self, text: str, actor: dict[str, Any]) -> str:
        try:
            command = parse_command(text)
        except BotParseError as exc:
            return str(exc)

        if command.action in ADMIN_ONLY_ACTIONS and actor["role"] != UserRole.ADMIN:
            return "Only admins can change priority or assign tickets."

        try:
            return await self._dispatch(command, actor)
        except AppError as exc:
            return f"Error: {exc.message}"

    async def _dispatch(self, command: ParsedCommand, actor: dict[str, Any]) -> str:
        actor_id = actor["email"]
        sender_name = actor["name"]

        if command.action == "list_open":
            result = await self.tickets.list_tickets(status="open", limit=10)
            if not result["items"]:
                return "No open tickets."
            lines = [_line(t) for t in result["items"]]
            return f"Open tickets ({result['total']}):\n" + "\n".join(lines)

        if command.action == "list_critical":
            result = await self.tickets.list_tickets(
                priority="critical",
                statuses=["open", "in_analysis", "in_progress", "waiting_customer",
                          "waiting_internal"],
                limit=10,
            )
            if not result["items"]:
                return "No active critical tickets."
            lines = [_line(t) for t in result["items"]]
            return f"Critical tickets ({result['total']}):\n" + "\n".join(lines)

        ticket = await self.tickets.require_by_code(command.code)

        if command.action == "view":
            sla = ticket.get("sla") or {}
            due = sla.get("first_response_due_at")
            return (
                f"{ticket['code']} — {ticket['title']}\n"
                f"Status: {ticket['status']}\n"
                f"Priority: {ticket['priority']}\n"
                f"Type: {ticket['type']}\n"
                f"Channel: {ticket['source_channel']}\n"
                f"Assigned to: {ticket.get('assigned_to_name') or 'unassigned'}\n"
                f"SLA: {ticket['sla_state']}"
                + (f" (first response due {due:%Y-%m-%d %H:%M UTC})" if due else "")
                + f"\nRequester: {ticket['requester']['name']}\n"
                f"Description: {ticket['description'][:200]}"
            )

        if command.action == "set_status":
            old = ticket["status"]
            updated = await self.tickets.change_status(ticket["id"], command.value, actor_id)
            return (
                f"Ticket {updated['code']} updated.\n"
                f"Previous status: {old}\n"
                f"New status: {updated['status']}\n"
                f"Tenant notified."
            )

        if command.action == "set_priority":
            old = ticket["priority"]
            updated = await self.tickets.change_priority(ticket["id"], command.value, actor_id)
            return (
                f"Ticket {updated['code']} updated.\n"
                f"Previous priority: {old}\n"
                f"New priority: {updated['priority']}"
            )

        if command.action == "reply":
            await self.tickets.add_message(
                ticket["id"],
                sender_type=SenderType.BOT,
                sender_name=sender_name,
                message=command.text,
                created_by=actor_id,
                metadata={"origin": "bot"},
            )
            return f"Reply sent on {ticket['code']}. Tenant notified."

        if command.action == "resolve":
            updated = await self.tickets.resolve(
                ticket["id"], command.text, actor_id, sender_name, sender_type=SenderType.BOT
            )
            return f"Ticket {updated['code']} resolved. Tenant notified."

        if command.action == "assign":
            user = await self.users.get_by_name(command.value)
            if not user:
                user = await self.users.get_by_email(command.value)
            if not user:
                return f"User not found: {command.value}"
            updated = await self.tickets.assign(
                ticket["id"], user["id"], user["name"], actor_id
            )
            return f"Ticket {updated['code']} assigned to {user['name']}."

        return "Unsupported command."
