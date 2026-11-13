import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Minus, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { MonthlyGoal } from "@/types";

export function GoalProgressControl({
  goal,
  compact = false,
  onSaved,
}: {
  goal: MonthlyGoal;
  compact?: boolean;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState(String(goal.metric_current ?? 0));

  useEffect(() => {
    setDraft(String(goal.metric_current ?? 0));
  }, [goal.metric_current]);

  const save = useMutation({
    mutationFn: (metric_current: number) =>
      api<MonthlyGoal>(`/api/goals/monthly/${goal.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ metric_current }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monthly"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      onSaved?.();
    },
  });

  if (goal.metric_target == null) {
    return <span className="tabular-nums text-ink-faint">{compact ? "—" : "No metric"}</span>;
  }

  const commit = (value: number) => {
    const next = Math.max(0, value);
    setDraft(String(next));
    save.mutate(next);
  };

  const current = Number(draft);
  const pct = Math.round(Math.min(100, (current / goal.metric_target) * 100));

  return (
    <div className={compact ? "flex items-center gap-1" : "space-y-2"}>
      <div className="flex items-center gap-1">
        <button
          className="flex h-6 w-6 items-center justify-center rounded border border-line text-ink-faint hover:text-ink"
          onClick={() => commit((Number.isFinite(current) ? current : 0) - 1)}
          aria-label="Decrease progress"
        >
          <Minus className="h-3 w-3" />
        </button>
        <input
          className="h-6 w-14 rounded border border-line bg-bg px-1 text-center text-xs tabular-nums outline-none focus:border-gold/50"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={() => commit(Number(draft) || 0)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit(Number(draft) || 0);
          }}
        />
        <button
          className="flex h-6 w-6 items-center justify-center rounded border border-line text-ink-faint hover:text-ink"
          onClick={() => commit((Number.isFinite(current) ? current : 0) + 1)}
          aria-label="Increase progress"
        >
          <Plus className="h-3 w-3" />
        </button>
      </div>
      {!compact && (
        <div className="text-xs text-ink-faint">
          {pct}% · {goal.metric_target} {goal.metric_unit}
        </div>
      )}
      {compact && (
        <span className="text-[11px] tabular-nums text-ink-faint">
          {goal.metric_unit || "done"}
        </span>
      )}
    </div>
  );
}
