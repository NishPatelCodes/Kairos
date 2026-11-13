import { Link } from "react-router-dom";

import { GoalProgressControl } from "@/components/goals/GoalProgressControl";
import { formatMinutes } from "@/lib/utils";
import type { AnnualGoal, DailyProgress, MonthlyGoal } from "@/types";

export function ContextPanel({
  annual,
  monthly,
  daily,
  onGoalChange,
}: {
  annual?: AnnualGoal;
  monthly: MonthlyGoal[];
  daily?: DailyProgress;
  onGoalChange?: () => void;
}) {
  return (
    <div className="space-y-8">
      <section>
        <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">1-year vision</div>
        {annual ? (
          <>
            <p className="mt-3 font-serif text-xl leading-snug text-ink">{annual.title}</p>
            <p className="mt-2 text-xs text-gold">{annual.days_remaining} days remaining</p>
          </>
        ) : (
          <p className="mt-3 text-sm text-ink-faint">Set your year during onboarding.</p>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">This month</div>
          <Link to="/goals" className="text-[11px] text-gold hover:underline">
            Manage
          </Link>
        </div>
        <div className="space-y-4">
          {monthly.length === 0 && (
            <p className="text-sm text-ink-faint">No monthly goals yet.</p>
          )}
          {monthly.map((goal) => (
            <div key={goal.id}>
              <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
                <span className="truncate text-ink">{goal.title}</span>
                <span className="tabular-nums text-ink-faint">
                  {goal.progress_pct != null ? `${Math.round(goal.progress_pct)}%` : "—"}
                </span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-gold"
                  style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                />
              </div>
              {goal.metric_target != null && (
                <div className="mt-2">
                  <GoalProgressControl goal={goal} compact onSaved={onGoalChange} />
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {daily && (
        <section>
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">Today</div>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <Stat label="Planned" value={formatMinutes(daily.planned_minutes)} />
            <Stat label="Completed" value={formatMinutes(daily.completed_minutes)} />
            <Stat label="Adherence" value={`${Math.round(daily.completion_rate)}%`} />
            <Stat label="Missed" value={String(daily.missed_count)} />
          </dl>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-bg px-3 py-2.5">
      <dt className="text-[11px] uppercase tracking-[0.12em] text-ink-faint">{label}</dt>
      <dd className="mt-1 tabular-nums text-ink">{value}</dd>
    </div>
  );
}
