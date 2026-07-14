import { formatDistanceToNowStrict } from "date-fns";

import type { SlaState, Ticket } from "./types";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function timeAgo(value: string | null | undefined): string {
  if (!value) return "—";
  return `${formatDistanceToNowStrict(new Date(value))} ago`;
}

/** Human line for the SLA lamp: how long until / past first-response due. */
export function slaLabel(ticket: Ticket): string {
  const { sla, sla_state } = ticket;
  if (sla_state === "met") return "responded";
  if (!sla.first_response_due_at) return "no SLA";
  const due = new Date(sla.first_response_due_at);
  const distance = formatDistanceToNowStrict(due);
  return sla_state === "overdue" ? `${distance} overdue` : `${distance} left`;
}

export const SLA_LAMP_CLASS: Record<SlaState, string> = {
  ok: "bg-lamp-ok",
  near_due: "bg-lamp-warn",
  overdue: "bg-lamp-overdue",
  met: "bg-lamp-met",
};

export const SLA_TEXT_CLASS: Record<SlaState, string> = {
  ok: "text-lamp-ok",
  near_due: "text-lamp-warn",
  overdue: "text-lamp-overdue",
  met: "text-muted-foreground",
};

export const STATUS_LABEL: Record<string, string> = {
  open: "Open",
  in_analysis: "In analysis",
  in_progress: "In progress",
  waiting_customer: "Waiting customer",
  waiting_internal: "Waiting internal",
  resolved: "Resolved",
  closed: "Closed",
  cancelled: "Cancelled",
};

export const TYPE_LABEL: Record<string, string> = {
  bug: "Bug",
  question: "Question",
  improvement: "Improvement",
  feature_request: "Feature request",
  incident: "Incident",
  support: "Support",
};

export const PRIORITY_LABEL: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

/** Priority line bar (switchboard line) classes. */
export const PRIORITY_BAR_CLASS: Record<string, string> = {
  low: "bg-border",
  medium: "bg-chart-2",
  high: "bg-lamp-warn",
  critical: "bg-lamp-overdue",
};

export const CHANNEL_LABEL: Record<string, string> = {
  manual: "Manual",
  whatsapp: "WhatsApp",
  telegram: "Telegram",
  slack: "Slack",
  teams: "Teams",
  webhook: "Webhook",
  demo: "Demo",
};
