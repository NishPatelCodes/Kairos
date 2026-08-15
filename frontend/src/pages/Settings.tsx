import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Profile } from "@/types";

export function SettingsPage() {
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: () => api<Profile>("/api/auth/me/") });
  const [form, setForm] = useState({
    display_name: "",
    timezone: "",
    peak_energy: "morning" as Profile["peak_energy"],
    work_start: "",
    work_end: "",
    preferred_block_minutes: 90,
  });

  useEffect(() => {
    if (!me.data) return;
    setForm({
      display_name: me.data.display_name || "",
      timezone: me.data.timezone || "",
      peak_energy: me.data.peak_energy,
      work_start: me.data.preferences?.work_start?.slice(0, 5) || "",
      work_end: me.data.preferences?.work_end?.slice(0, 5) || "",
      preferred_block_minutes: me.data.preferences?.preferred_block_minutes || 90,
    });
  }, [me.data]);

  const save = useMutation({
    mutationFn: () =>
      api("/api/auth/me/", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: form.display_name,
          timezone: form.timezone,
          peak_energy: form.peak_energy,
          preferences: {
            work_start: form.work_start || null,
            work_end: form.work_end || null,
            preferred_block_minutes: Number(form.preferred_block_minutes),
          },
        }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });

  return (
    <div className="h-full overflow-y-auto px-6 py-8 md:px-10">
      <div className="mx-auto max-w-xl">
        <p className="text-[11px] uppercase tracking-[0.2em] text-gold">Account</p>
        <h1 className="mt-2 font-serif text-4xl">Settings</h1>
        <Card className="mt-8 space-y-5 p-6">
          <Field label="Name">
            <Input
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
            />
          </Field>
          <Field label="Timezone">
            <Input
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            />
          </Field>
          <Field label="Peak energy">
            <select
              className="h-11 w-full rounded-lg border border-line bg-bg-elevated px-3 text-sm"
              value={form.peak_energy}
              onChange={(e) =>
                setForm({ ...form, peak_energy: e.target.value as Profile["peak_energy"] })
              }
            >
              <option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option>
              <option value="evening">Evening</option>
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Work start">
              <Input
                type="time"
                value={form.work_start}
                onChange={(e) => setForm({ ...form, work_start: e.target.value })}
              />
            </Field>
            <Field label="Work end">
              <Input
                type="time"
                value={form.work_end}
                onChange={(e) => setForm({ ...form, work_end: e.target.value })}
              />
            </Field>
          </div>
          <Field label="Preferred focus block (minutes)">
            <Input
              type="number"
              min={25}
              max={180}
              value={form.preferred_block_minutes}
              onChange={(e) =>
                setForm({ ...form, preferred_block_minutes: Number(e.target.value) })
              }
            />
          </Field>
          {save.isError && <p className="text-sm text-rose">{save.error.message}</p>}
          {save.isSuccess && <p className="text-sm text-sage">Saved.</p>}
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </Card>
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
