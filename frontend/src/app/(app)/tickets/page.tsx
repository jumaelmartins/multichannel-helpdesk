"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChannelBadge, CodeChip, PriorityBadge, SlaLamp, StatusBadge } from "@/components/tickets/badges";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  CHANNEL_LABEL,
  PRIORITY_LABEL,
  STATUS_LABEL,
  TYPE_LABEL,
  formatDateTime,
} from "@/lib/format";
import type { Tenant, Ticket, TicketList } from "@/lib/types";

const PAGE_SIZE = 20;
const ALL = "__all__";

function FilterSelect({
  value,
  onChange,
  placeholder,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  options: Record<string, string>;
}) {
  return (
    <Select value={value} onValueChange={(next) => next && onChange(next)}>
      <SelectTrigger size="sm" className="w-fit min-w-28">
        <SelectValue>
          {value === ALL ? (
            <span className="text-muted-foreground">{placeholder}</span>
          ) : (
            options[value]
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>{placeholder}</SelectItem>
        {Object.entries(options).map(([key, label]) => (
          <SelectItem key={key} value={key}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function NewTicketDialog({ tenants }: { tenants: Tenant[] }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    tenant_id: "",
    requester_name: "",
    requester_email: "",
    title: "",
    description: "",
    type: "support",
    priority: "medium",
  });

  const isTenantUser = user?.role === "tenant_user";

  const createTicket = useMutation({
    mutationFn: () =>
      api.post<Ticket>("/api/tickets", {
        tenant_id: isTenantUser ? undefined : form.tenant_id || undefined,
        requester: form.requester_name
          ? {
              name: form.requester_name,
              email: form.requester_email || null,
              channel: "manual",
            }
          : undefined,
        title: form.title,
        description: form.description,
        type: form.type,
        priority: form.priority,
        source_channel: "manual",
      }),
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setOpen(false);
      toast.success(`Ticket ${ticket.code} created`);
      router.push(`/tickets/${ticket.id}`);
    },
    onError: (error) => toast.error(error.message),
  });

  if (user?.role === "viewer") return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" />}>
        <Plus className="size-4" /> New ticket
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New ticket</DialogTitle>
          <DialogDescription>
            Open a support ticket on behalf of a tenant contact
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            createTicket.mutate();
          }}
        >
          {!isTenantUser && (
            <div className="space-y-1.5">
              <Label>Tenant</Label>
              <Select
                value={form.tenant_id}
                onValueChange={(tenant_id) =>
                  tenant_id && setForm({ ...form, tenant_id })
                }
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue>
                    {form.tenant_id
                      ? tenants.find((t) => t.id === form.tenant_id)?.name
                      : "Select tenant"}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {tenants.map((tenant) => (
                    <SelectItem key={tenant.id} value={tenant.id}>
                      {tenant.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="requester">Requester name</Label>
              <Input
                id="requester"
                placeholder={isTenantUser ? "Defaults to you" : "Contact name"}
                value={form.requester_name}
                onChange={(e) =>
                  setForm({ ...form, requester_name: e.target.value })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="requester-email">Requester email</Label>
              <Input
                id="requester-email"
                type="email"
                value={form.requester_email}
                onChange={(e) =>
                  setForm({ ...form, requester_email: e.target.value })
                }
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              required
              minLength={3}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              rows={4}
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select
                value={form.type}
                onValueChange={(type) => type && setForm({ ...form, type })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue>{TYPE_LABEL[form.type]}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(TYPE_LABEL).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Priority</Label>
              <Select
                value={form.priority}
                onValueChange={(priority) =>
                  priority && setForm({ ...form, priority })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue>{PRIORITY_LABEL[form.priority]}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PRIORITY_LABEL).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createTicket.isPending}>
              {createTicket.isPending ? "Creating…" : "Create ticket"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TicketsPageInner() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState(ALL);
  const [priority, setPriority] = useState(ALL);
  const [type, setType] = useState(ALL);
  const [channel, setChannel] = useState(ALL);
  const [tenantFilter, setTenantFilter] = useState(
    searchParams.get("tenant") ?? ALL,
  );
  const [page, setPage] = useState(0);

  const isInternal = user?.role !== "tenant_user";

  const { data: tenants } = useQuery({
    queryKey: ["tenants"],
    queryFn: () => api.get<Tenant[]>("/api/tenants"),
    enabled: isInternal,
  });

  const tenantName = useMemo(() => {
    const map = new Map<string, string>();
    tenants?.forEach((tenant) => map.set(tenant.id, tenant.name));
    return map;
  }, [tenants]);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    params.set("skip", String(page * PAGE_SIZE));
    params.set("limit", String(PAGE_SIZE));
    if (search) params.set("search", search);
    if (status !== ALL) params.set("status", status);
    if (priority !== ALL) params.set("priority", priority);
    if (type !== ALL) params.set("type", type);
    if (channel !== ALL) params.set("channel", channel);
    if (tenantFilter !== ALL) params.set("tenant_id", tenantFilter);
    return params.toString();
  }, [search, status, priority, type, channel, tenantFilter, page]);

  const { data, isLoading } = useQuery({
    queryKey: ["tickets", query],
    queryFn: () => api.get<TicketList>(`/api/tickets?${query}`),
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Tickets</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.total} tickets in queue` : "Loading queue…"}
          </p>
        </div>
        <NewTicketDialog tenants={tenants ?? []} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search code, title…"
            className="h-8 w-56 pl-8"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
          />
        </div>
        <FilterSelect value={status} onChange={(v) => { setStatus(v); setPage(0); }} placeholder="Status" options={STATUS_LABEL} />
        <FilterSelect value={priority} onChange={(v) => { setPriority(v); setPage(0); }} placeholder="Priority" options={PRIORITY_LABEL} />
        <FilterSelect value={type} onChange={(v) => { setType(v); setPage(0); }} placeholder="Type" options={TYPE_LABEL} />
        <FilterSelect value={channel} onChange={(v) => { setChannel(v); setPage(0); }} placeholder="Channel" options={CHANNEL_LABEL} />
        {isInternal && tenants && (
          <FilterSelect
            value={tenantFilter}
            onChange={(v) => { setTenantFilter(v); setPage(0); }}
            placeholder="Tenant"
            options={Object.fromEntries(tenants.map((t) => [t.id, t.name]))}
          />
        )}
      </div>

      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-24">Code</TableHead>
              <TableHead>Title</TableHead>
              {isInternal && <TableHead className="w-36">Tenant</TableHead>}
              <TableHead className="w-28">Priority</TableHead>
              <TableHead className="w-36">Status</TableHead>
              <TableHead className="w-24">Channel</TableHead>
              <TableHead className="w-32">Assignee</TableHead>
              <TableHead className="w-32">Created</TableHead>
              <TableHead className="w-32">SLA</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(6)].map((_, index) => (
                <TableRow key={index}>
                  <TableCell colSpan={isInternal ? 9 : 8}>
                    <Skeleton className="h-6" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.items.length ? (
              data.items.map((ticket) => (
                <TableRow
                  key={ticket.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/tickets/${ticket.id}`)}
                >
                  <TableCell>
                    <CodeChip code={ticket.code} />
                  </TableCell>
                  <TableCell className="max-w-64">
                    <span className="block truncate font-medium">
                      {ticket.title}
                    </span>
                  </TableCell>
                  {isInternal && (
                    <TableCell className="text-muted-foreground">
                      {tenantName.get(ticket.tenant_id) ?? "—"}
                    </TableCell>
                  )}
                  <TableCell>
                    <PriorityBadge priority={ticket.priority} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={ticket.status} />
                  </TableCell>
                  <TableCell>
                    <ChannelBadge channel={ticket.source_channel} />
                  </TableCell>
                  <TableCell className="truncate text-muted-foreground">
                    {ticket.assigned_to_name ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {formatDateTime(ticket.created_at)}
                  </TableCell>
                  <TableCell>
                    <SlaLamp ticket={ticket} />
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={isInternal ? 9 : 8}
                  className="py-10 text-center text-muted-foreground"
                >
                  No tickets match the current filters
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-end gap-2">
          <span className="font-mono text-xs text-muted-foreground">
            page {page + 1}/{totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

export default function TicketsPage() {
  return (
    <Suspense>
      <TicketsPageInner />
    </Suspense>
  );
}
