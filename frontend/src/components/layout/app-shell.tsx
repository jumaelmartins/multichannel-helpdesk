"use client";

import {
  Building2,
  Headset,
  LayoutDashboard,
  LogOut,
  TerminalSquare,
  Ticket as TicketIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { NotificationBell } from "@/components/layout/notification-bell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: UserRole[];
}

const NAV: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    roles: ["admin", "agent", "tenant_user", "viewer"],
  },
  {
    href: "/tickets",
    label: "Tickets",
    icon: TicketIcon,
    roles: ["admin", "agent", "tenant_user", "viewer"],
  },
  {
    href: "/tenants",
    label: "Tenants",
    icon: Building2,
    roles: ["admin", "agent", "viewer"],
  },
  {
    href: "/bot",
    label: "Bot console",
    icon: TerminalSquare,
    roles: ["admin", "agent"],
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="font-mono text-sm text-muted-foreground">
          loading console…
        </span>
      </div>
    );
  }

  const items = NAV.filter((item) => item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen w-full">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-56 flex-col border-r bg-sidebar md:flex">
        <div className="flex items-center gap-2.5 border-b px-4 py-4">
          <span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Headset className="size-4" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold">Multichannel</p>
            <p className="font-mono text-[11px] text-muted-foreground">
              helpdesk console
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-2 py-3">
          <p className="px-2 pb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Operations
          </p>
          {items.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                )}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0 leading-tight">
              <p className="truncate text-sm font-medium">{user.name}</p>
              <p className="truncate font-mono text-[11px] text-muted-foreground">
                {user.role}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              title="Sign out"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col md:pl-56">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-6">
          <div className="flex items-center gap-2 md:hidden">
            <Headset className="size-4 text-primary" />
            <span className="text-sm font-semibold">Helpdesk</span>
          </div>
          <nav className="flex gap-1 md:hidden">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md p-2",
                  pathname.startsWith(item.href)
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground",
                )}
              >
                <item.icon className="size-4" />
              </Link>
            ))}
          </nav>
          <div className="hidden font-mono text-xs text-muted-foreground md:block">
            {new Date().toLocaleDateString("en-GB", {
              weekday: "short",
              day: "2-digit",
              month: "short",
            })}
          </div>
          <NotificationBell />
        </header>

        <main className="flex-1 px-4 py-5 md:px-6">{children}</main>
      </div>
    </div>
  );
}
