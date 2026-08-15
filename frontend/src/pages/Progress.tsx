import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatMinutes } from "@/lib/utils";
import type { Dashboard } from "@/types";

export function ProgressPage() {
  const dash = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/api/progress/dashboard/"),
  });

  if (dash.isLoading) {
    return (
      <div className="grid gap-4 p-8 md:grid-cols-3">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  const data = dash.data;
  if (!data) {
    return <p className="p-8 text-ink-faint">Could not load progress.</p>;
  }

  const chart = data.weekly.days.map((day) => ({
    name: day.date.slice(5),
    completed: Math.round(day.completed_minutes / 60 * 10) / 10,
    planned: Math.round(day.planned_minutes / 60 * 10) / 10,
  }));

  return (
    <div className="h-full overflow-y-auto px-6 py-8 md:px-10">
      <div className="mx-auto max-w-5xl">
        <p className="text-[11px] uppercase tracking-[0.2em] text-gold">Analytics</p>
        <h1 className="mt-2 font-serif text-4xl">Progress</h1>
        <p className="mt-3 text-sm text-ink-muted">Every chart answers a useful question.</p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Metric
            label="Monthly progress"
            value={`${Math.round(data.monthly.overall_pct)}%`}
            hint={`${data.monthly.velocity} vs expected ${Math.round(data.monthly.expected_pct)}%`}
          />
          <Metric
            label="Focus time this week"
            value={formatMinutes(data.weekly.focus_minutes)}
            hint={`${data.weekly.completed_tasks} blocks completed`}
          />
          <Metric
            label="Goal velocity"
            value={data.monthly.velocity}
            hint={`${data.weekly.missed_tasks} missed this week`}
          />
        </div>

        <Card className="mt-6 p-6">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">
            Planned vs completed hours
          </div>
          <div className="mt-6 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chart}>
                <defs>
                  <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#c4a574" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#c4a574" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#111113",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 12,
                    color: "#fafafa",
                  }}
                />
                <Area type="monotone" dataKey="planned" stroke="#3f3f46" fill="transparent" strokeWidth={1.5} />
                <Area type="monotone" dataKey="completed" stroke="#c4a574" fill="url(#goldFill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="mt-6 p-6">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">Monthly goals</div>
          <div className="mt-5 space-y-5">
            {data.monthly.goals.map((goal) => (
              <div key={goal.id}>
                <div className="mb-2 flex justify-between text-sm">
                  <span>{goal.title}</span>
                  <span className="tabular-nums text-ink-muted">
                    {Math.round(goal.progress_pct || 0)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gold"
                    style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                  />
                </div>
              </div>
            ))}
            {!data.monthly.goals.length && (
              <p className="text-sm text-ink-faint">Set monthly goals to see velocity here.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card className="p-5">
      <div className="text-[11px] uppercase tracking-[0.14em] text-ink-faint">{label}</div>
      <div className="mt-3 font-serif text-4xl text-ink">{value}</div>
      <div className="mt-2 text-xs text-ink-muted">{hint}</div>
    </Card>
  );
}
