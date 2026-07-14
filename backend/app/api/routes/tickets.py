from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    CurrentUser,
    DbDep,
    assert_ticket_visible,
    require_roles,
    scoped_tenant_id,
)
from app.api.schemas.ticket import (
    AssignRequest,
    PriorityChangeRequest,
    ResolveRequest,
    StatusChangeRequest,
    TicketCreateRequest,
    TicketMessageRequest,
    TicketUpdateRequest,
)
from app.application.services.ticket_service import TicketService
from app.core.exceptions import DomainValidationError, NotFoundError
from app.domain.enums import SenderType, UserRole
from app.infra.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/tickets", tags=["tickets"])

can_create = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT, UserRole.TENANT_USER))
can_work = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))
admin_only = Depends(require_roles(UserRole.ADMIN))

ROLE_TO_SENDER = {
    UserRole.ADMIN: SenderType.ADMIN,
    UserRole.AGENT: SenderType.AGENT,
    UserRole.TENANT_USER: SenderType.TENANT,
}


@router.post("", status_code=201, dependencies=[can_create])
async def create_ticket(body: TicketCreateRequest, db: DbDep, user: CurrentUser):
    data = body.model_dump()
    if user["role"] == UserRole.TENANT_USER:
        data["tenant_id"] = user.get("tenant_id")
    if not data.get("tenant_id"):
        raise DomainValidationError("tenant_id is required")
    if not data.get("requester"):
        data["requester"] = {
            "name": user["name"],
            "email": user["email"],
            "phone": None,
            "channel": data.get("source_channel", "manual"),
        }
    return await TicketService(db).create_ticket(data, created_by=user["email"])


@router.get("")
async def list_tickets(
    db: DbDep,
    user: CurrentUser,
    tenant_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    type: str | None = None,
    channel: str | None = None,
    assigned_to: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return await TicketService(db).list_tickets(
        skip=skip,
        limit=limit,
        tenant_id=scoped_tenant_id(user, tenant_id),
        status=status,
        priority=priority,
        ticket_type=type,
        channel=channel,
        assigned_to=assigned_to,
        search=search,
    )


@router.get("/code/{code}")
async def get_ticket_by_code(code: str, db: DbDep, user: CurrentUser):
    ticket = await TicketService(db).require_by_code(code)
    assert_ticket_visible(user, ticket)
    return ticket


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, db: DbDep, user: CurrentUser):
    ticket = await TicketService(db).get_ticket(ticket_id)
    assert_ticket_visible(user, ticket)
    return ticket


@router.patch("/{ticket_id}", dependencies=[admin_only])
async def update_ticket(ticket_id: str, body: TicketUpdateRequest, db: DbDep):
    service = TicketService(db)
    await service.get_ticket(ticket_id)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise DomainValidationError("No fields to update")
    ticket = await service.tickets.update(ticket_id, updates)
    return service._with_sla_state(ticket)


@router.get("/{ticket_id}/messages")
async def list_messages(ticket_id: str, db: DbDep, user: CurrentUser):
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    assert_ticket_visible(user, ticket)
    return await service.list_messages(ticket_id)


@router.post("/{ticket_id}/messages", status_code=201, dependencies=[can_create])
async def add_message(ticket_id: str, body: TicketMessageRequest, db: DbDep, user: CurrentUser):
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    assert_ticket_visible(user, ticket)
    return await service.add_message(
        ticket_id,
        sender_type=ROLE_TO_SENDER[user["role"]],
        sender_name=user["name"],
        sender_contact=user["email"],
        message=body.message,
        attachments=[a.model_dump() for a in body.attachments],
        created_by=user["email"],
    )


@router.get("/{ticket_id}/events")
async def list_events(ticket_id: str, db: DbDep, user: CurrentUser):
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    assert_ticket_visible(user, ticket)
    return await service.list_events(ticket_id)


@router.post("/{ticket_id}/status", dependencies=[can_work])
async def change_status(ticket_id: str, body: StatusChangeRequest, db: DbDep, user: CurrentUser):
    return await TicketService(db).change_status(ticket_id, body.status, actor=user["email"])


@router.post("/{ticket_id}/priority", dependencies=[admin_only])
async def change_priority(
    ticket_id: str, body: PriorityChangeRequest, db: DbDep, user: CurrentUser
):
    return await TicketService(db).change_priority(ticket_id, body.priority, actor=user["email"])


@router.post("/{ticket_id}/assign", dependencies=[admin_only])
async def assign_ticket(ticket_id: str, body: AssignRequest, db: DbDep, user: CurrentUser):
    assigned_name = None
    if body.user_id:
        assignee = await UserRepository(db).get(body.user_id)
        if not assignee:
            raise NotFoundError("Assignee user not found")
        assigned_name = assignee["name"]
    return await TicketService(db).assign(
        ticket_id, body.user_id, assigned_name, actor=user["email"]
    )


@router.post("/{ticket_id}/resolve", dependencies=[can_work])
async def resolve_ticket(ticket_id: str, body: ResolveRequest, db: DbDep, user: CurrentUser):
    return await TicketService(db).resolve(
        ticket_id,
        body.message,
        actor=user["email"],
        sender_name=user["name"],
        sender_type=ROLE_TO_SENDER[user["role"]],
    )


@router.post("/{ticket_id}/reopen", dependencies=[can_work])
async def reopen_ticket(ticket_id: str, db: DbDep, user: CurrentUser):
    return await TicketService(db).reopen(ticket_id, actor=user["email"])
