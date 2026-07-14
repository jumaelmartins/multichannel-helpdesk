"use client";

import { useMutation } from "@tanstack/react-query";
import { TerminalSquare } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ConsoleLine {
  kind: "command" | "reply" | "error";
  text: string;
  at: string;
}

const QUICK_COMMANDS = [
  "/chamados abertos",
  "/chamados criticos",
  "/ver HD-0001",
  "/status HD-0001 em_analise",
  "/responder HD-0001 Estamos analisando sua solicitação.",
  "/resolver HD-0001 Ajuste realizado. Pode validar novamente.",
];

export default function BotPlaygroundPage() {
  const [lines, setLines] = useState<ConsoleLine[]>([
    {
      kind: "reply",
      text:
        "Internal bot console. Manage tickets without leaving the keyboard.\n" +
        "Try /chamados abertos — or any command below.",
      at: new Date().toLocaleTimeString(),
    },
  ]);
  const [command, setCommand] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const run = useMutation({
    mutationFn: (input: string) =>
      api.post<{ reply: string }>("/api/bot/command", { command: input }),
    onSuccess: (data) =>
      setLines((previous) => [
        ...previous,
        { kind: "reply", text: data.reply, at: new Date().toLocaleTimeString() },
      ]),
    onError: (error) =>
      setLines((previous) => [
        ...previous,
        { kind: "error", text: error.message, at: new Date().toLocaleTimeString() },
      ]),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [lines]);

  function submit(input: string) {
    const trimmed = input.trim();
    if (!trimmed) return;
    setLines((previous) => [
      ...previous,
      { kind: "command", text: trimmed, at: new Date().toLocaleTimeString() },
    ]);
    setCommand("");
    run.mutate(trimmed);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <TerminalSquare className="size-4.5 text-primary" /> Bot console
        </h1>
        <p className="text-sm text-muted-foreground">
          The same command handler that powers Telegram/WhatsApp internal bots —
          exposed here as a playground.
        </p>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {QUICK_COMMANDS.map((quick) => (
          <button
            key={quick}
            onClick={() => submit(quick)}
            className="rounded-md border bg-card px-2 py-1 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
          >
            {quick}
          </button>
        ))}
      </div>

      <Card className="py-0">
        <CardContent className="p-0">
          <div
            ref={scrollRef}
            className="h-[26rem] space-y-3 overflow-y-auto px-4 py-4 font-mono text-sm"
          >
            {lines.map((line, index) => (
              <div key={index}>
                <p className="text-[10px] text-muted-foreground">{line.at}</p>
                {line.kind === "command" ? (
                  <p className="text-primary">
                    <span className="select-none text-muted-foreground">❯ </span>
                    {line.text}
                  </p>
                ) : (
                  <pre
                    className={cn(
                      "whitespace-pre-wrap rounded-md border bg-muted/50 px-3 py-2 text-xs leading-relaxed",
                      line.kind === "error" && "border-destructive/40 text-destructive",
                    )}
                  >
                    {line.text}
                  </pre>
                )}
              </div>
            ))}
            {run.isPending && (
              <p className="animate-pulse text-xs text-muted-foreground">
                bot is thinking…
              </p>
            )}
          </div>
          <form
            className="flex gap-2 border-t p-3"
            onSubmit={(event) => {
              event.preventDefault();
              submit(command);
            }}
          >
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="/status HD-0001 em_analise"
              className="bg-muted/40 font-mono text-sm"
              autoFocus
            />
            <Button type="submit" disabled={run.isPending}>
              Run
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
