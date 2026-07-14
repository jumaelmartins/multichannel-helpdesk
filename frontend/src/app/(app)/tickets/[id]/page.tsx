"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Paperclip, RotateCcw, Send } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import {
  ChannelBadge,
  CodeChip,
  PriorityBadge,
  SlaLamp,
  StatusBadge,
} from "@/components/tickets/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  PRIORITY_LABEL,
  STATUS_LABEL,
  formatDateTime,
  timeAgo,
} from "@/lib/format";
import type {
  Ticket,
  TicketEvent,
  TicketMessage,
  TicketStatus,
  User,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const ACTIVE: TicketStatus[] = [
  "open",
  "in_analysis",
  "in_progress",
  "waiting_customer",
  "waiting_internal",
];

function statusOptions(current: TicketStatus): TicketStatus[] {
  if (ACTIVE.includes(current)) {
    return [...ACTIVE.filter((status) => status !== current), "cancelled"];
  }
  if (current === "resolved") return ["closed"];
  return [];
}

const INTERNAL_SENDERS = new Set(["agent", "admin", "bot"]);

function MessageBubble({ message }: { message: TicketMessage }) {
  const internal = INTERNAL_SENDERS.has(message.sender_type);
  if (message.sender_type === "system") {
    return (
      <p className="py-1 text-center font-mono text-xs text-muted-foreground">
        {message.message}
      </p>
    );
  }
  return (
    <div className={cn("flex", internal ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg border px-3 py-2",
          internal
            ? "rounded-br-sm border-primary/20 bg-accent/60"
            : "rounded-bl-sm bg-card",
        )}
      >
        <div className="mb-1 flex items-baseline justify-between gap-4">
          <span className="text-xs font-semibold">
            {message.sender_name}
            <span className="ml-1.5 font-mono text-[10px] font-normal uppercase text-muted-foreground">
              {message.sender_type} · {message.channel}
            </span>
          </span>
          <span className="font-mono text-[10px] text-muted-foreground">
            {timeAgo(message.created_at)}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-sm">{message.message}</p>
        {message.attachments.length > 0 && (
          <div className="mt-2 space-y-1 border-t border-border/60 pt-2">
            {message.attachments.map((attachment, index) => (
              <a
                key={index}
                href={attachment.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-xs text-primary hover:underline"
              >
                <Paperclip className="size-3" />
                {attachment.filename}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5">
      <span className="shrink-0 text-xs text-muted-foreground">{label}</span>
      <span className="text-right text-xs font-medium">{value}</span>
    </div>
  );
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [reply, setReply] = useState("");
  const [resolution, setResolution] = useState("");
  const [resolveOpen, setResolveOpen] = useState(false);

  const canWork = user?.role === "admin" || user?.role === "agent";
  const isAdmin = user?.role === "admin";
  const canReply = canWork || user?.role === "tenant_user";

  const { data: ticket } = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => api.get<Ticket>(`/api/tickets/${id}`),
  });
  const { data: messages } = useQuery({
    queryKey: ["ticket-messages", id],
    queryFn: () => api.get<TicketMessage[]>(`/api/tickets/${id}/messages`),
  });
  const { data: events } = useQuery({
    queryKey: ["ticket-events", id],
    queryFn: () => api.get<TicketEvent[]>(`/api/tickets/${id}/events`),
  });
  const { data: internalUsers } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<User[]>("/api/users"),
    enabled: canWork,
  });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["ticket", id] });
    queryClient.invalidateQueries({ queryKey: ["ticket-messages", id] });
    queryClient.invalidateQueries({ queryKey: ["ticket-events", id] });
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  const act = {
    onSuccess: () => refresh(),
    onError: (error: Error) => toast.error(error.message),
  };

  const sendReply = useMutation({
    mutationFn: () =>
      api.post(`/api/tickets/${id}/messages`, { message: reply }),
    ...act,
    onSuccess: () => {
      setReply("");
      refresh();
    },
  });
  const changeStatus = useMutation({
    mutationFn: (status: string) =>
      api.post(`/api/tickets/${id}/status`, { status }),
    ...act,
  });
  const changePriority = useMutation({
    mutationFn: (priority: string) =>
      api.post(`/api/tickets/${id}/priority`, { priority }),
    ...act,
  });
  const assign = useMutation({
    mutationFn: (user_id: string | null) =>
      api.post(`/api/tickets/${id}/assign`, { user_id }),
    ...act,
  });
  const resolve = useMutation({
    mutationFn: () =>
      api.post(`/api/tickets/${id}/resolve`, { message: resolution }),
    ...act,
    onSuccess: () => {
      setResolveOpen(false);
      setResolution("");
      toast.success("Ticket resolved");
      refresh();
    },
  });
  const reopen = useMutation({
    mutationFn: () => api.post(`/api/tickets/${id}/reopen`),
    ...act,
  });

  if (!ticket) {
    return (
      <div className="mx-auto max-w-6xl space-y-4">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const options = statusOptions(ticket.status);
  const isActive = ACTIVE.includes(ticket.status);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <Link
        href="/tickets"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" /> Back to queue
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <CodeChip code={ticket.code} className="text-sm" />
            <h1 className="text-lg font-semibold tracking-tight">
              {ticket.title}
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
            <ChannelBadge channel={ticket.source_channel} />
            <SlaLamp ticket={ticket} />
          </div>
        </div>
        {canWork && (
          <div className="flex flex-wrap items-center gap-2">
            {options.length > 0 && (
              <Select
                value=""
                onValueChange={(status) => status && changeStatus.mutate(status)}
              >
                <SelectTrigger size="sm" className="w-36">
                  <SelectValue>
                    <span className="text-muted-foreground">Change status</span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {options.map((status) => (
                    <SelectItem key={status} value={status}>
                      {STATUS_LABEL[status]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {isActive && (
              <Dialog open={resolveOpen} onOpenChange={setResolveOpen}>
                <DialogTrigger render={<Button size="sm" variant="default" />}>
                  <CheckCircle2 className="size-4" /> Resolve
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Resolve {ticket.code}</DialogTitle>
                    <DialogDescription>
                      A resolution message is required — the tenant will be
                      notified.
                    </DialogDescription>
                  </DialogHeader>
                  <Textarea
                    rows={4}
                    placeholder="What was done to resolve this ticket?"
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                  />
                  <DialogFooter>
                    <Button
                      onClick={() => resolve.mutate()}
                      disabled={!resolution.trim() || resolve.isPending}
                    >
                      {resolve.isPending ? "Resolving…" : "Resolve ticket"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
            {(ticket.status === "resolved" || ticket.status === "closed") && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => reopen.mutate()}
                disabled={reopen.isPending}
              >
                <RotateCcw className="size-4" /> Reopen
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_290px]">
        <Tabs defaultValue="conversation">
          <TabsList>
            <TabsTrigger value="conversation">
              Conversation{messages ? ` (${messages.length})` : ""}
            </TabsTrigger>
            <TabsTrigger value="events">
              Events{events ? ` (${events.length})` : ""}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="conversation" className="space-y-3">
            <Card className="py-4">
              <CardContent className="space-y-3 px-4">
                <div className="rounded-md bg-muted/60 px-3 py-2">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    Description
                  </p>
                  <p className="mt-1 whitespace-pre-wrap text-sm">
                    {ticket.description || "—"}
                  </p>
                </div>
                {messages === undefined ? (
                  <Skeleton className="h-24" />
                ) : messages.length ? (
                  messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))
                ) : (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    No messages yet
                  </p>
                )}
              </CardContent>
            </Card>

            {canReply && (
              <form
                className="flex items-end gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (reply.trim()) sendReply.mutate();
                }}
              >
                <Textarea
                  rows={2}
                  placeholder="Write a reply… (tenant will be notified)"
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  className="bg-card"
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!reply.trim() || sendReply.isPending}
                >
                  <Send className="size-4" />
                </Button>
              </form>
            )}
          </TabsContent>

          <TabsContent value="events">
            <Card className="py-2">
              <CardContent className="px-4">
                {events?.length ? (
                  <ul className="divide-y divide-border/60">
                    {events.map((event) => (
                      <li key={event.id} className="flex items-baseline gap-3 py-2">
                        <span className="w-32 shrink-0 font-mono text-[11px] text-muted-foreground">
                          {formatDateTime(event.created_at)}
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm">
                            <span className="font-mono text-xs font-medium text-primary">
                              {event.event_type}
                            </span>{" "}
                            {event.description}
                          </p>
                          <p className="font-mono text-[11px] text-muted-foreground">
                            by {event.created_by}
                            {event.old_value && event.new_value
                              ? ` · ${event.old_value} → ${event.new_value}`
                              : ""}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    No events
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="space-y-4">
          <Card className="gap-2 py-4">
            <CardHeader className="px-4">
              <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                Requester
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4">
              <DetailRow label="Name" value={ticket.requester.name} />
              <DetailRow label="Email" value={ticket.requester.email ?? "—"} />
              <DetailRow label="Phone" value={ticket.requester.phone ?? "—"} />
              <DetailRow
                label="Channel"
                value={<ChannelBadge channel={ticket.requester.channel} />}
              />
            </CardContent>
          </Card>

          <Card className="gap-2 py-4">
            <CardHeader className="px-4">
              <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                SLA · first response
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4">
              <DetailRow label="State" value={<SlaLamp ticket={ticket} />} />
              <DetailRow
                label="Due"
                value={formatDateTime(ticket.sla.first_response_due_at)}
              />
              <DetailRow
                label="Responded"
                value={formatDateTime(ticket.sla.first_response_at)}
              />
            </CardContent>
          </Card>

          <Card className="gap-2 py-4">
            <CardHeader className="px-4">
              <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                Assignment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 px-4">
              {isAdmin ? (
                <Select
                  value={ticket.assigned_to ?? "__none__"}
                  onValueChange={(value) =>
                    value && assign.mutate(value === "__none__" ? null : value)
                  }
                >
                  <SelectTrigger size="sm" className="w-full">
                    <SelectValue>
                      {ticket.assigned_to_name ?? "Unassigned"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Unassigned</SelectItem>
                    {internalUsers?.map((internal) => (
                      <SelectItem key={internal.id} value={internal.id}>
                        {internal.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <DetailRow
                  label="Assignee"
                  value={ticket.assigned_to_name ?? "Unassigned"}
                />
              )}
              {isAdmin && (
                <Select
                  value={ticket.priority}
                  onValueChange={(priority) =>
                    priority && changePriority.mutate(priority)
                  }
                >
                  <SelectTrigger size="sm" className="w-full">
                    <SelectValue>
                      {PRIORITY_LABEL[ticket.priority]} priority
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PRIORITY_LABEL).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label} priority
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </CardContent>
          </Card>

          <Card className="gap-2 py-4">
            <CardHeader className="px-4">
              <CardTitle className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4">
              <DetailRow label="Created" value={formatDateTime(ticket.created_at)} />
              <DetailRow label="Updated" value={formatDateTime(ticket.updated_at)} />
              <DetailRow label="Resolved" value={formatDateTime(ticket.resolved_at)} />
              <DetailRow label="Closed" value={formatDateTime(ticket.closed_at)} />
              {ticket.tags.length > 0 && (
                <DetailRow label="Tags" value={ticket.tags.join(", ")} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
