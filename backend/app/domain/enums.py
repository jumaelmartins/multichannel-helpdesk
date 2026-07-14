from enum import StrEnum


class TicketType(StrEnum):
    BUG = "bug"
    QUESTION = "question"
    IMPROVEMENT = "improvement"
    FEATURE_REQUEST = "feature_request"
    INCIDENT = "incident"
    SUPPORT = "support"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_ANALYSIS = "in_analysis"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_INTERNAL = "waiting_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Channel(StrEnum):
    MANUAL = "manual"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    DEMO = "demo"


class UserRole(StrEnum):
    ADMIN = "admin"
    AGENT = "agent"
    TENANT_USER = "tenant_user"
    VIEWER = "viewer"


class SenderType(StrEnum):
    TENANT = "tenant"
    AGENT = "agent"
    SYSTEM = "system"
    BOT = "bot"
    ADMIN = "admin"


class EventType(StrEnum):
    TICKET_CREATED = "ticket_created"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    ASSIGNED = "assigned"
    MESSAGE_ADDED = "message_added"
    SLA_UPDATED = "sla_updated"
    TICKET_RESOLVED = "ticket_resolved"
    TICKET_REOPENED = "ticket_reopened"
    NOTIFICATION_SENT = "notification_sent"


class TenantStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SlaState(StrEnum):
    OK = "ok"
    NEAR_DUE = "near_due"
    OVERDUE = "overdue"
    MET = "met"
