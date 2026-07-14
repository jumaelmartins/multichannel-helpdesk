export type TicketStatus =
  | "open"
  | "in_analysis"
  | "in_progress"
  | "waiting_customer"
  | "waiting_internal"
  | "resolved"
  | "closed"
  | "cancelled";

export type TicketPriority = "low" | "medium" | "high" | "critical";

export type TicketType =
  | "bug"
  | "question"
  | "improvement"
  | "feature_request"
  | "incident"
  | "support";

export type Channel =
  | "manual"
  | "whatsapp"
  | "telegram"
  | "slack"
  | "teams"
  | "webhook"
  | "demo";

export type UserRole = "admin" | "agent" | "tenant_user" | "viewer";

export type SlaState = "ok" | "near_due" | "overdue" | "met";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  tenant_id: string | null;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  document: string | null;
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: string;
  tenant_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  role: string | null;
  channels: Channel[];
}

export interface Attachment {
  type: string;
  url: string;
  filename: string;
}

export interface Ticket {
  id: string;
  code: string;
  tenant_id: string;
  requester: {
    name: string;
    email: string | null;
    phone: string | null;
    channel: Channel;
  };
  title: string;
  description: string;
  type: TicketType;
  priority: TicketPriority;
  status: TicketStatus;
  source_channel: Channel;
  assigned_to: string | null;
  assigned_to_name?: string | null;
  sla: {
    first_response_due_at: string | null;
    resolution_due_at: string | null;
    first_response_at: string | null;
  };
  sla_state: SlaState;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_type: "tenant" | "agent" | "system" | "bot" | "admin";
  sender_name: string;
  sender_contact: string | null;
  channel: Channel;
  message: string;
  attachments: Attachment[];
  created_at: string;
}

export interface TicketEvent {
  id: string;
  ticket_id: string;
  event_type: string;
  old_value: string | null;
  new_value: string | null;
  description: string;
  created_by: string;
  created_at: string;
}

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  ticket_id: string | null;
  ticket_code: string | null;
  read: boolean;
  created_at: string;
}

export interface TicketList {
  items: Ticket[];
  total: number;
}

export interface DashboardStats {
  counts: Record<TicketStatus, number>;
  sla_near_due: number;
  sla_overdue: number;
  recent: Ticket[];
  critical: Ticket[];
  due_today: Ticket[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}
