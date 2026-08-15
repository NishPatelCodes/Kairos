import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, setTokens } from "@/lib/api";
import type { Profile } from "@/types";

type AuthResponse = { access: string; refresh: string; user: Profile };

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      api<AuthResponse>("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      navigate("/");
    },
  });

  return (
    <AuthFrame
      title="Welcome back"
      subtitle="Pick up today's plan where you left it."
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <Field label="Email">
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </Field>
        <Field label="Password">
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        {mutation.isError && (
          <p className="text-sm text-rose">{mutation.error.message}</p>
        )}
        <Button className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Signing in…" : "Continue"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-faint">
        New here?{" "}
        <Link to="/register" className="text-gold hover:underline">
          Create an account
        </Link>
      </p>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      api<AuthResponse>("/api/auth/register/", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          display_name: displayName,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }),
      }),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      navigate("/");
    },
  });

  return (
    <AuthFrame title="Begin" subtitle="We'll build your operating system in a few minutes.">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <Field label="Name">
          <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="What should I call you?" />
        </Field>
        <Field label="Email">
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </Field>
        <Field label="Password">
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
        </Field>
        {mutation.isError && <p className="text-sm text-rose">{mutation.error.message}</p>}
        <Button className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-faint">
        Already have an account?{" "}
        <Link to="/login" className="text-gold hover:underline">
          Sign in
        </Link>
      </p>
    </AuthFrame>
  );
}

function AuthFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-full items-center justify-center bg-bg px-4">
      <div className="w-full max-w-[420px]">
        <div className="mb-10 text-center">
          <img src="/logo.svg" alt="" className="mx-auto mb-5 h-12 w-12 rounded-xl" />
          <div className="mb-6 text-[12px] tracking-[0.28em] text-gold">KAIROS</div>
          <h1 className="font-serif text-4xl text-ink">{title}</h1>
          <p className="mt-3 text-sm text-ink-muted">{subtitle}</p>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs uppercase tracking-[0.14em] text-ink-faint">{label}</span>
      {children}
    </label>
  );
}
