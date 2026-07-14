"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { CodeChip, PriorityLine, SlaLamp, StatusBadge } from "@/components/tickets/badges";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import type { DashboardStats, Ticket } from "@/lib/types";
import { cn } from "@/lib/utils";

const TILES: {
  key: keyof DashboardStats["counts"] | "sla_near_due" | "sla_overdue";
  label: string;
  accent?: string;
}[] = [
  { key: "open", label: "Open" },
  { key: "in_analysis", label: "In analysis" },
  { key: "in_progress", label: "In progress" },
  { key: "waiting_customer", label: "Waiting customer" },
  { key: "resolved", label: "Resolved" },
  { key: "sla_near_due", label: "SLA due soon", accent: "text-lamp-warn" },
  { key: "sla_overdue", label: "SLA overdue", accent: "text-lamp-overdue" },
];

function TicketMiniRow({ ticket }: { ticket: Ticket }) {
  return (
    <Link
      href={`/tickets/${ticket.id}`}
      className="relative block rounded-md px-3 py-2 pl-4 transition-colors hover:bg-accent/50"
    >
      <PriorityLine priority={ticket.priority} />
      <span className="flex items-center justify-between gap-3">
        <CodeChip code={ticket.code} />
        <SlaLamp ticket={ticket} className="shrink-0" />
      </span>
      <span className="mt-1 block truncate text-sm">{ticket.title}</span>
    </Link>
  );
}

function TicketListCard({
  title,
  tickets,
  empty,
}: {
  title: string;
  tickets: Ticket[] | undefined;
  empty: string;
}) {
  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-2">
        {!tickets ? (
          <div className="space-y-2 px-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : tickets.length ? (
          <div className="space-y-0.5">
            {tickets.map((ticket) => (
              <TicketMiniRow key={ticket.id} ticket={ticket} />
            ))}
          </div>
        ) : (
          <p className="px-3 py-4 text-sm text-muted-foreground">{empty}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardStats>("/api/dashboard/stats"),
    refetchInterval: 30_000,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Queue overview and first-response SLA lamps
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {TILES.map((tile) => {
          const value =
            tile.key === "sla_near_due" || tile.key === "sla_overdue"
              ? data?.[tile.key]
              : data?.counts?.[tile.key];
          return (
            <Card key={tile.key} className="gap-1 py-3">
              <CardContent className="px-3">
                <p className="text-[11px] leading-tight text-muted-foreground">
                  {tile.label}
                </p>
                {data === undefined ? (
                  <Skeleton className="mt-1 h-7 w-10" />
                ) : (
                  <p
                    className={cn(
                      "font-mono text-2xl font-semibold tabular-nums",
                      value ? tile.accent : undefined,
                    )}
                  >
                    {value ?? 0}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <TicketListCard
          title="Latest tickets"
          tickets={data?.recent}
          empty="No tickets yet"
        />
        <TicketListCard
          title="Critical line"
          tickets={data?.critical}
          empty="No active critical tickets"
        />
        <TicketListCard
          title="Due in 24h"
          tickets={data?.due_today}
          empty="Nothing due in the next 24h"
        />
      </div>

      {data?.recent?.length ? (
        <Card className="gap-3 py-4">
          <CardHeader className="px-4">
            <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
              Last activity
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4">
            <div className="space-y-2">
              {data.recent.slice(0, 3).map((ticket) => (
                <div key={ticket.id} className="flex items-center gap-3 text-sm">
                  <span className="font-mono text-xs text-muted-foreground">
                    {timeAgo(ticket.updated_at)}
                  </span>
                  <CodeChip code={ticket.code} />
                  <StatusBadge status={ticket.status} />
                  <span className="truncate text-muted-foreground">
                    {ticket.title}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
