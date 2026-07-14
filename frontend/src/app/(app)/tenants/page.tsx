"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Ticket as TicketIcon, Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import type { Contact, Tenant } from "@/lib/types";

function TenantFormDialog({
  open,
  onOpenChange,
  tenant,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: Tenant | null;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(tenant?.name ?? "");
  const [document, setDocument] = useState(tenant?.document ?? "");

  const save = useMutation({
    mutationFn: () =>
      tenant
        ? api.patch<Tenant>(`/api/tenants/${tenant.id}`, { name, document })
        : api.post<Tenant>("/api/tenants", { name, document }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenants"] });
      onOpenChange(false);
      toast.success(tenant ? "Tenant updated" : "Tenant created");
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{tenant ? "Edit tenant" : "New tenant"}</DialogTitle>
          <DialogDescription>
            {tenant
              ? `Editing ${tenant.name} (${tenant.slug})`
              : "Slug is generated from the name"}
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="tenant-name">Name</Label>
            <Input
              id="tenant-name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tenant-document">Document (CNPJ)</Label>
            <Input
              id="tenant-document"
              placeholder="00.000.000/0001-00"
              value={document}
              onChange={(e) => setDocument(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={save.isPending}>
              {save.isPending ? "Saving…" : "Save tenant"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ContactsDialog({
  tenant,
  onOpenChange,
}: {
  tenant: Tenant | null;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: contacts } = useQuery({
    queryKey: ["contacts", tenant?.id],
    queryFn: () => api.get<Contact[]>(`/api/contacts?tenant_id=${tenant?.id}`),
    enabled: !!tenant,
  });

  return (
    <Dialog open={!!tenant} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Contacts — {tenant?.name}</DialogTitle>
          <DialogDescription>
            People who can open tickets through external channels
          </DialogDescription>
        </DialogHeader>
        {contacts === undefined ? (
          <Skeleton className="h-24" />
        ) : contacts.length ? (
          <ul className="divide-y divide-border/60">
            {contacts.map((contact) => (
              <li key={contact.id} className="py-2.5">
                <p className="text-sm font-medium">{contact.name}</p>
                <p className="font-mono text-xs text-muted-foreground">
                  {[contact.email, contact.phone].filter(Boolean).join(" · ") ||
                    "no contact info"}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No contacts registered
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function TenantsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Tenant | null>(null);
  const [contactsFor, setContactsFor] = useState<Tenant | null>(null);

  const { data: tenants, isLoading } = useQuery({
    queryKey: ["tenants"],
    queryFn: () => api.get<Tenant[]>("/api/tenants"),
  });

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Tenants</h1>
          <p className="text-sm text-muted-foreground">
            Client companies served by this helpdesk
          </p>
        </div>
        {isAdmin && (
          <Button
            size="sm"
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="size-4" /> New tenant
          </Button>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Name</TableHead>
              <TableHead className="w-40">Slug</TableHead>
              <TableHead className="w-44">Document</TableHead>
              <TableHead className="w-24">Status</TableHead>
              <TableHead className="w-36">Created</TableHead>
              <TableHead className="w-44 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(3)].map((_, index) => (
                <TableRow key={index}>
                  <TableCell colSpan={6}>
                    <Skeleton className="h-6" />
                  </TableCell>
                </TableRow>
              ))
            ) : tenants?.length ? (
              tenants.map((tenant) => (
                <TableRow key={tenant.id}>
                  <TableCell className="font-medium">{tenant.name}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {tenant.slug}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {tenant.document ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={
                        tenant.status === "active"
                          ? "text-lamp-ok"
                          : "text-muted-foreground"
                      }
                    >
                      {tenant.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {formatDateTime(tenant.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setContactsFor(tenant)}
                        title="View contacts"
                      >
                        <Users className="size-3.5" />
                      </Button>
                      <Link
                        href={`/tickets?tenant=${tenant.id}`}
                        title="View tickets"
                        className={buttonVariants({ variant: "ghost", size: "sm" })}
                      >
                        <TicketIcon className="size-3.5" />
                      </Link>
                      {isAdmin && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditing(tenant);
                            setFormOpen(true);
                          }}
                        >
                          Edit
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                  No tenants yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {formOpen && (
        <TenantFormDialog
          key={editing?.id ?? "new"}
          open={formOpen}
          onOpenChange={setFormOpen}
          tenant={editing}
        />
      )}
      <ContactsDialog
        tenant={contactsFor}
        onOpenChange={(open) => !open && setContactsFor(null)}
      />
    </div>
  );
}
