import { cn } from "@/lib/utils";
import {
  CHANNEL_LABEL,
  PRIORITY_BAR_CLASS,
  PRIORITY_LABEL,
  SLA_LAMP_CLASS,
  SLA_TEXT_CLASS,
  STATUS_LABEL,
  slaLabel,
} from "@/lib/format";
import type { Ticket, TicketPriority, TicketStatus } from "@/lib/types";

const STATUS_DOT: Record<TicketStatus, string> = {
  open: "bg-chart-2",
  in_analysis: "bg-chart-3",
  in_progress: "bg-primary",
  waiting_customer: "bg-chart-3",
  waiting_internal: "bg-chart-3",
  resolved: "bg-lamp-ok",
  closed: "bg-lamp-met",
  cancelled: "bg-lamp-met",
};

export function CodeChip({ code, className }: { code: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex whitespace-nowrap rounded-sm bg-muted px-1.5 py-0.5 font-mono text-xs font-medium text-secondary-foreground",
        className,
      )}
    >
      {code}
    </span>
  );
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-sm border border-border/80 px-2 py-0.5 text-xs font-medium text-secondary-foreground">
      <span className={cn("size-1.5 rounded-full", STATUS_DOT[status])} />
      {STATUS_LABEL[status]}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-secondary-foreground">
      <span className={cn("h-3 w-[3px] rounded-full", PRIORITY_BAR_CLASS[priority])} />
      {PRIORITY_LABEL[priority]}
    </span>
  );
}

export function ChannelBadge({ channel }: { channel: string }) {
  return (
    <span className="font-mono text-xs text-muted-foreground">
      {CHANNEL_LABEL[channel] ?? channel}
    </span>
  );
}

/** Switchboard lamp: colored dot + remaining/overdue time for first response. */
export function SlaLamp({ ticket, className }: { ticket: Ticket; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-mono text-xs",
        SLA_TEXT_CLASS[ticket.sla_state],
        className,
      )}
    >
      <span
        className={cn(
          "size-2 rounded-full",
          SLA_LAMP_CLASS[ticket.sla_state],
          ticket.sla_state === "overdue" && "animate-pulse",
        )}
      />
      {slaLabel(ticket)}
    </span>
  );
}

/** Thin left line whose color encodes priority — one per ticket row/card. */
export function PriorityLine({ priority }: { priority: TicketPriority }) {
  return (
    <span
      aria-hidden
      className={cn(
        "absolute inset-y-2 left-0 w-[3px] rounded-full",
        PRIORITY_BAR_CLASS[priority],
      )}
    />
  );
}
