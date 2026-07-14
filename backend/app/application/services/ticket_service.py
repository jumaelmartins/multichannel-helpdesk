from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.application.services.notification_service import NotificationService
from app.application.services.sla import compute_sla_state, first_response_due
from app.application.services.status_flow import assert_transition
from app.application.services.ticket_codes import format_ticket_code
from app.core.exceptions import DomainValidationError, NotFoundError
from app.domain.enums import EventType, SenderType, SlaState, TicketPriority, TicketStatus
from app.infra.database.repositories.base import utcnow
from app.infra.database.repositories.ticket_event_repository import TicketEventRepository
from app.infra.database.repositories.ticket_message_repository import TicketMessageRepository
from app.infra.database.repositories.ticket_repository import TicketRepository

INTERNAL_SENDERS = {SenderType.AGENT, SenderType.ADMIN, SenderType.BOT}


class TicketService:
    def __init__(self, db: AsyncDatabase):
        self.tickets = TicketRepository(db)
        self.messages = TicketMessageRepository(db)
        self.events = TicketEventRepository(db)
        self.notifications = NotificationService(db)

    # ------------------------------------------------------------------ helpers

    def _with_sla_state(self, ticket: dict[str, Any]) -> dict[str, Any]:
        sla = ticket.get("sla") or {}
        state = compute_sla_state(
            created_at=ticket["created_at"],
            first_response_due_at=sla.get("first_response_due_at"),
            first_response_at=sla.get("first_response_at"),
            now=datetime.now(UTC),
        )
        if ticket["status"] in (TicketStatus.CLOSED, TicketStatus.CANCELLED) and state in (
            SlaState.OK,
            SlaState.NEAR_DUE,
            SlaState.OVERDUE,
        ):
            state = SlaState.MET if sla.get("first_response_at") else state
        ticket["sla_state"] = state
        return ticket

    async def _record_event(
        self,
        ticket_id: str,
        event_type: EventType,
        description: str,
        created_by: str = "system",
        old_value: str | None = None,
        new_value: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.events.insert(
            {
                "ticket_id": ticket_id,
                "event_type": event_type,
                "old_value": old_value,
                "new_value": new_value,
                "description": description,
                "created_by": created_by,
                "metadata": metadata or {},
            }
        )

    async def _require(self, ticket_id: str) -> dict[str, Any]:
        ticket = await self.tickets.get(ticket_id)
        if not ticket:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket

    async def require_by_code(self, code: str) -> dict[str, Any]:
        ticket = await self.tickets.get_by_code(code)
        if not ticket:
            raise NotFoundError(f"Ticket {code} not found")
        return self._with_sla_state(ticket)

    # ------------------------------------------------------------------ create

    async def create_ticket(self, data: dict[str, Any], created_by: str) -> dict[str, Any]:
        now = utcnow()
        sequence = await self.tickets.next_code_sequence()
        code = format_ticket_code(sequence)
        priority = TicketPriority(data["priority"])
        doc = {
            "code": code,
            "tenant_id": data["tenant_id"],
            "requester": data["requester"],
            "title": data["title"],
            "description": data.get("description", ""),
            "type": data["type"],
            "priority": priority,
            "status": TicketStatus.OPEN,
            "source_channel": data.get("source_channel", "manual"),
            "assigned_to": data.get("assigned_to"),
            "sla": {
                "first_response_due_at": first_response_due(priority, now),
                "resolution_due_at": None,
                "first_response_at": None,
            },
            "tags": data.get("tags", []),
            "metadata": data.get("metadata", {}),
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "closed_at": None,
        }
        ticket = await self.tickets.insert(doc)
        await self._record_event(
            ticket["id"],
            EventType.TICKET_CREATED,
            f"Ticket {code} created",
            created_by=created_by,
            new_value=str(TicketStatus.OPEN),
        )
        await self.notifications.notify_internal(
            f"New ticket {code}", ticket["title"], ticket
        )
        await self.notifications.notify_tenant(
            f"Ticket {code} received", "We received your request and will respond soon.", ticket
        )
        return self._with_sla_state(ticket)

    # ------------------------------------------------------------------ read

    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return self._with_sla_state(await self._require(ticket_id))

    async def list_tickets(
        self, skip: int = 0, limit: int = 50, **filter_kwargs
    ) -> dict[str, Any]:
        filters = TicketRepository.build_filters(**filter_kwargs)
        items = await self.tickets.find(
            filters, sort=[("created_at", -1)], skip=skip, limit=limit
        )
        total = await self.tickets.count(filters)
        return {"items": [self._with_sla_state(t) for t in items], "total": total}

    async def list_events(self, ticket_id: str) -> list[dict[str, Any]]:
        await self._require(ticket_id)
        return await self.events.list_for_ticket(ticket_id)

    async def list_messages(self, ticket_id: str) -> list[dict[str, Any]]:
        await self._require(ticket_id)
        return await self.messages.list_for_ticket(ticket_id)

    # ------------------------------------------------------------------ messages

    async def add_message(
        self,
        ticket_id: str,
        sender_type: SenderType,
        sender_name: str,
        message: str,
        channel: str | None = None,
        sender_contact: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        ticket = await self._require(ticket_id)
        msg = await self.messages.insert(
            {
                "ticket_id": ticket_id,
                "sender_type": sender_type,
                "sender_name": sender_name,
                "sender_contact": sender_contact,
                "channel": channel or ticket["source_channel"],
                "message": message,
                "attachments": attachments or [],
                "metadata": metadata or {},
            }
        )
        await self._record_event(
            ticket_id,
            EventType.MESSAGE_ADDED,
            f"Message added by {sender_name} ({sender_type})",
            created_by=created_by or sender_name,
        )

        updates: dict[str, Any] = {}
        sla = ticket.get("sla") or {}
        if sender_type in INTERNAL_SENDERS and not sla.get("first_response_at"):
            sla["first_response_at"] = utcnow()
            updates["sla"] = sla
            await self._record_event(
                ticket_id,
                EventType.SLA_UPDATED,
                "First response registered",
                created_by=created_by or sender_name,
            )

        reopened = False
        if sender_type == SenderType.TENANT and ticket["status"] in (
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
        ):
            updates["status"] = TicketStatus.OPEN
            updates["resolved_at"] = None
            updates["closed_at"] = None
            reopened = True

        if updates:
            ticket = await self.tickets.update(ticket_id, updates) or ticket

        if reopened:
            await self._record_event(
                ticket_id,
                EventType.TICKET_REOPENED,
                "Ticket reopened after tenant reply",
                created_by=sender_name,
                old_value=str(TicketStatus.RESOLVED),
                new_value=str(TicketStatus.OPEN),
            )

        if notify:
            if sender_type == SenderType.TENANT:
                title = f"Tenant replied on {ticket['code']}"
                if reopened:
                    title = f"Ticket {ticket['code']} reopened by tenant reply"
                await self.notifications.notify_internal(title, message, ticket)
            elif sender_type in INTERNAL_SENDERS:
                await self.notifications.notify_tenant(
                    f"New reply on {ticket['code']}", message, ticket
                )
                await self._record_event(
                    ticket_id,
                    EventType.NOTIFICATION_SENT,
                    f"Reply sent to tenant via {ticket['source_channel']}",
                    created_by=created_by or sender_name,
                )
        return msg

    # ------------------------------------------------------------------ mutations

    async def change_status(
        self, ticket_id: str, new_status: TicketStatus, actor: str
    ) -> dict[str, Any]:
        ticket = await self._require(ticket_id)
        current = TicketStatus(ticket["status"])
        if new_status == TicketStatus.RESOLVED:
            raise DomainValidationError("Use the resolve action (a resolution message is required)")
        assert_transition(current, new_status)

        updates: dict[str, Any] = {"status": new_status}
        reopening = current in (TicketStatus.RESOLVED, TicketStatus.CLOSED)
        if new_status == TicketStatus.CLOSED:
            updates["closed_at"] = utcnow()
        if reopening:
            updates["resolved_at"] = None
            updates["closed_at"] = None

        ticket = await self.tickets.update(ticket_id, updates)
        await self._record_event(
            ticket_id,
            EventType.TICKET_REOPENED if reopening else EventType.STATUS_CHANGED,
            f"Status changed from {current} to {new_status}",
            created_by=actor,
            old_value=str(current),
            new_value=str(new_status),
        )
        if reopening:
            await self.notifications.notify_internal(
                f"Ticket {ticket['code']} reopened", f"Reopened by {actor}", ticket
            )
        else:
            await self.notifications.notify_tenant(
                f"Ticket {ticket['code']} status updated",
                f"Status changed to {new_status}",
                ticket,
            )
        return self._with_sla_state(ticket)

    async def change_priority(
        self, ticket_id: str, new_priority: TicketPriority, actor: str
    ) -> dict[str, Any]:
        ticket = await self._require(ticket_id)
        current = TicketPriority(ticket["priority"])
        if current == new_priority:
            return self._with_sla_state(ticket)

        updates: dict[str, Any] = {"priority": new_priority}
        sla = ticket.get("sla") or {}
        if not sla.get("first_response_at"):
            sla["first_response_due_at"] = first_response_due(new_priority, ticket["created_at"])
            updates["sla"] = sla

        ticket = await self.tickets.update(ticket_id, updates)
        await self._record_event(
            ticket_id,
            EventType.PRIORITY_CHANGED,
            f"Priority changed from {current} to {new_priority}",
            created_by=actor,
            old_value=str(current),
            new_value=str(new_priority),
        )
        if "sla" in updates:
            await self._record_event(
                ticket_id, EventType.SLA_UPDATED, "SLA recalculated after priority change",
                created_by=actor,
            )
        if new_priority in (TicketPriority.HIGH, TicketPriority.CRITICAL):
            await self.notifications.notify_internal(
                f"Ticket {ticket['code']} priority raised to {new_priority}",
                ticket["title"],
                ticket,
            )
        return self._with_sla_state(ticket)

    async def assign(
        self,
        ticket_id: str,
        assigned_to: str | None,
        assigned_to_name: str | None,
        actor: str,
    ) -> dict[str, Any]:
        ticket = await self._require(ticket_id)
        previous = ticket.get("assigned_to_name") or ticket.get("assigned_to")
        ticket = await self.tickets.update(
            ticket_id, {"assigned_to": assigned_to, "assigned_to_name": assigned_to_name}
        )
        await self._record_event(
            ticket_id,
            EventType.ASSIGNED,
            f"Ticket assigned to {assigned_to_name or 'nobody'}",
            created_by=actor,
            old_value=previous,
            new_value=assigned_to_name,
        )
        return self._with_sla_state(ticket)

    async def resolve(self, ticket_id: str, message: str, actor: str, sender_name: str,
                      sender_type: SenderType = SenderType.AGENT) -> dict[str, Any]:
        if not message or not message.strip():
            raise DomainValidationError("A resolution message is required")
        ticket = await self._require(ticket_id)
        current = TicketStatus(ticket["status"])
        assert_transition(current, TicketStatus.RESOLVED)

        await self.add_message(
            ticket_id,
            sender_type=sender_type,
            sender_name=sender_name,
            message=message,
            created_by=actor,
            notify=False,
        )
        ticket = await self.tickets.update(
            ticket_id, {"status": TicketStatus.RESOLVED, "resolved_at": utcnow()}
        )
        await self._record_event(
            ticket_id,
            EventType.TICKET_RESOLVED,
            "Ticket resolved",
            created_by=actor,
            old_value=str(current),
            new_value=str(TicketStatus.RESOLVED),
        )
        await self.notifications.notify_tenant(
            f"Ticket {ticket['code']} resolved", message, ticket
        )
        return self._with_sla_state(ticket)

    async def reopen(self, ticket_id: str, actor: str) -> dict[str, Any]:
        ticket = await self._require(ticket_id)
        current = TicketStatus(ticket["status"])
        assert_transition(current, TicketStatus.OPEN)
        ticket = await self.tickets.update(
            ticket_id,
            {"status": TicketStatus.OPEN, "resolved_at": None, "closed_at": None},
        )
        await self._record_event(
            ticket_id,
            EventType.TICKET_REOPENED,
            "Ticket reopened",
            created_by=actor,
            old_value=str(current),
            new_value=str(TicketStatus.OPEN),
        )
        await self.notifications.notify_internal(
            f"Ticket {ticket['code']} reopened", f"Reopened by {actor}", ticket
        )
        return self._with_sla_state(ticket)

    # ------------------------------------------------------------------ dashboard

    async def dashboard_stats(self, tenant_id: str | None = None) -> dict[str, Any]:
        base: dict[str, Any] = {"tenant_id": tenant_id} if tenant_id else {}
        counts = {}
        for status in TicketStatus:
            counts[str(status)] = await self.tickets.count({**base, "status": status})

        active = ["open", "in_analysis", "in_progress", "waiting_customer", "waiting_internal"]
        now = datetime.now(UTC)
        unresponded = await self.tickets.find(
            {**base, "status": {"$in": active}, "sla.first_response_at": None},
            sort=[("sla.first_response_due_at", 1)],
            limit=500,
        )
        near_due, overdue, due_today = [], [], []
        for raw in unresponded:
            ticket = self._with_sla_state(raw)
            state = ticket["sla_state"]
            due = (ticket.get("sla") or {}).get("first_response_due_at")
            if state == SlaState.OVERDUE:
                overdue.append(ticket)
            elif state == SlaState.NEAR_DUE:
                near_due.append(ticket)
            if due and now <= due <= now + timedelta(hours=24):
                due_today.append(ticket)

        recent = await self.tickets.find(base, sort=[("created_at", -1)], limit=5)
        critical = await self.tickets.find(
            {**base, "priority": "critical", "status": {"$in": active}},
            sort=[("created_at", -1)],
            limit=5,
        )
        return {
            "counts": counts,
            "sla_near_due": len(near_due),
            "sla_overdue": len(overdue),
            "recent": [self._with_sla_state(t) for t in recent],
            "critical": [self._with_sla_state(t) for t in critical],
            "due_today": due_today[:5],
        }
