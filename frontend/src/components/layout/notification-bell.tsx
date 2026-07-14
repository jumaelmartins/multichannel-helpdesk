"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import type { AppNotification } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NotificationsResponse {
  items: AppNotification[];
  unread: number;
}

export function NotificationBell() {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<NotificationsResponse>("/api/notifications"),
    refetchInterval: 30_000,
  });

  const unread = data?.unread ?? 0;

  async function markAllRead() {
    await api.post("/api/notifications/read-all");
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant="ghost" size="icon" className="relative" />}
      >
        <Bell className="size-4" />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-lamp-overdue font-mono text-[10px] font-semibold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between border-b px-3 py-2">
          <span className="text-sm font-semibold">Notifications</span>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              className="text-xs text-primary hover:underline"
            >
              Mark all read
            </button>
          )}
        </div>
        <ScrollArea className="max-h-96">
          {data?.items.length ? (
            <ul>
              {data.items.map((notification) => (
                <li
                  key={notification.id}
                  className={cn(
                    "border-b border-border/60 px-3 py-2.5 last:border-0",
                    !notification.read && "bg-accent/40",
                  )}
                >
                  <Link
                    href={
                      notification.ticket_id
                        ? `/tickets/${notification.ticket_id}`
                        : "#"
                    }
                    className="block"
                  >
                    <p className="text-sm font-medium leading-tight">
                      {notification.title}
                    </p>
                    {notification.body && (
                      <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                        {notification.body}
                      </p>
                    )}
                    <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                      {timeAgo(notification.created_at)}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-3 py-8 text-center text-sm text-muted-foreground">
              No notifications yet
            </p>
          )}
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
