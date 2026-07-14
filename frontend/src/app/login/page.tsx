"use client";

import { Headset } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { label: "Demo Admin", email: "admin@demo.com" },
  { label: "Demo Agent", email: "agent@demo.com" },
  { label: "Demo Tenant", email: "tenant@demo.com" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function signIn(userEmail: string, userPassword: string) {
    setSubmitting(true);
    try {
      await login(userEmail, userPassword);
      router.replace("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <span className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Headset className="size-4.5" />
          </span>
          <div className="leading-tight">
            <p className="font-semibold">Multichannel Helpdesk</p>
            <p className="font-mono text-[11px] text-muted-foreground">
              support console
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign in</CardTitle>
            <CardDescription>
              Use a demo account or your credentials
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form
              className="space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                signIn(email, password);
              }}
            >
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Signing in…" : "Sign in"}
              </Button>
            </form>

            <div className="flex items-center gap-3">
              <Separator className="flex-1" />
              <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                demo access
              </span>
              <Separator className="flex-1" />
            </div>

            <div className="grid grid-cols-3 gap-2">
              {DEMO_ACCOUNTS.map((account) => (
                <Button
                  key={account.email}
                  variant="outline"
                  size="sm"
                  disabled={submitting}
                  onClick={() => signIn(account.email, "demo123")}
                >
                  {account.label.replace("Demo ", "")}
                </Button>
              ))}
            </div>
            <p className="text-center font-mono text-[11px] text-muted-foreground">
              demo password: demo123
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
