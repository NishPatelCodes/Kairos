import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { AnnualGoal, MonthlyGoal } from "@/types";

export function GoalsPage() {
  const annual = useQuery({
    queryKey: ["annual"],
    queryFn: () => api<AnnualGoal[]>("/api/goals/annual/"),
  });
  const monthly = useQuery({
    queryKey: ["monthly"],
    queryFn: () => api<MonthlyGoal[]>("/api/goals/monthly/"),
  });

  const dream = annual.data?.find((g) => g.is_active) ?? annual.data?.[0];

  return (
    <div className="h-full overflow-y-auto px-6 py-8 md:px-10">
      <div className="mx-auto max-w-3xl">
        <p className="text-[11px] uppercase tracking-[0.2em] text-gold">Hierarchy</p>
        <h1 className="mt-2 font-serif text-4xl">Goals</h1>
        <p className="mt-3 max-w-xl text-sm text-ink-muted">
          Daily work should roll up. Tasks feed the month. The month feeds the year.
        </p>

        {annual.isLoading ? (
          <Skeleton className="mt-10 h-40" />
        ) : (
          <Card className="mt-10 p-6">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">1-year dream</div>
            {dream ? (
              <>
                <h2 className="mt-3 font-serif text-2xl leading-snug">{dream.title}</h2>
                {dream.description && (
                  <p className="mt-3 text-sm text-ink-muted">{dream.description}</p>
                )}
                <p className="mt-4 text-sm text-gold">{dream.days_remaining} days remaining</p>
              </>
            ) : (
              <p className="mt-3 text-sm text-ink-faint">Ask Kairos to set your year.</p>
            )}
          </Card>
        )}

        <div className="mt-8 space-y-3">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">This month</div>
          {monthly.isLoading && <Skeleton className="h-24" />}
          {(monthly.data ?? []).map((goal) => (
            <Card key={goal.id} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base text-ink">{goal.title}</h3>
                  {goal.description && (
                    <p className="mt-1 text-sm text-ink-muted">{goal.description}</p>
                  )}
                  {dream && (
                    <p className="mt-3 text-[11px] uppercase tracking-[0.12em] text-ink-faint">
                      Contributes to · {dream.title}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="tabular-nums text-lg text-ink">
                    {goal.progress_pct != null ? `${Math.round(goal.progress_pct)}%` : "—"}
                  </div>
                  {goal.metric_target != null && (
                    <div className="text-xs text-ink-faint">
                      {goal.metric_current}/{goal.metric_target} {goal.metric_unit}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-gold"
                  style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                />
              </div>
            </Card>
          ))}
          {!monthly.isLoading && !monthly.data?.length && (
            <p className="text-sm text-ink-faint">No monthly goals yet. Define them in chat.</p>
          )}
        </div>
      </div>
    </div>
  );
}
