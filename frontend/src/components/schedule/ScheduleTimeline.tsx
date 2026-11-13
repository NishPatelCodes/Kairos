import { Check, Circle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn, timeLabel } from "@/lib/utils";
import type { MonthlyGoal, ScheduleItem, ScheduleStatus } from "@/types";

const statusCopy: Record<ScheduleStatus, string> = {
  completed: "Completed",
  in_progress: "In progress",
  upcoming: "Upcoming",
  missed: "Missed",
  rescheduled: "Rescheduled",
};

type MetricHint = {
  goalId: number;
  unit: string;
  target: number;
  current: number;
};

function metricFor(item: ScheduleItem, monthly: MonthlyGoal[]): MetricHint | null {
  if (item.kind === "break") return null;
  if (item.monthly_goal && item.goal_metric_target) {
    return {
      goalId: item.monthly_goal,
      unit: item.goal_metric_unit || "units",
      target: item.goal_metric_target,
      current: item.goal_metric_current ?? 0,
    };
  }
  const title = item.title.toLowerCase();
  const match = monthly.find((goal) => {
    if (goal.metric_target == null) return false;
    const name = goal.title.toLowerCase();
    return name.includes(title) || title.includes(name);
  });
  if (!match || match.metric_target == null) return null;
  return {
    goalId: match.id,
    unit: match.metric_unit || "units",
    target: match.metric_target,
    current: match.metric_current ?? 0,
  };
}

export function ScheduleTimeline({
  items,
  monthly = [],
  onChange,
}: {
  items: ScheduleItem[];
  monthly?: MonthlyGoal[];
  onChange: () => void;
}) {
  const [pending, setPending] = useState<{ item: ScheduleItem; metric: MetricHint } | null>(null);
  const [amount, setAmount] = useState("");
  const [saving, setSaving] = useState(false);

  const visible = items.filter((item) => item.status !== "rescheduled");

  const complete = async (item: ScheduleItem, progressAmount?: number, goalId?: number) => {
    setSaving(true);
    try {
      const body: Record<string, number> = {};
      if (progressAmount != null) body.progress_amount = progressAmount;
      if (goalId != null) body.goal_id = goalId;
      await api(`/api/schedule/${item.id}/complete/`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setPending(null);
      onChange();
    } finally {
      setSaving(false);
    }
  };

  const onDone = (item: ScheduleItem) => {
    const metric = metricFor(item, monthly);
    if (metric) {
      setAmount("");
      setPending({ item, metric });
      return;
    }
    void complete(item);
  };

  if (!visible.length) {
    return (
      <div className="px-1 py-10 text-sm leading-relaxed text-ink-faint">
        Nothing on the board yet. Tell Kairos what the next few hours should look like.
      </div>
    );
  }

  return (
    <>
      <ol className="relative space-y-0">
        {visible.map((item, index) => (
          <li key={item.id} className="relative flex gap-4 pb-6">
            {index < visible.length - 1 && (
              <span className="absolute left-[7px] top-4 h-full w-px bg-line" />
            )}
            <StatusDot status={item.status} />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <time className="text-xs tabular-nums tracking-wide text-ink-faint">
                  {timeLabel(item.start_time)} – {timeLabel(item.end_time)}
                </time>
                {item.status !== "completed" && (
                  <button
                    className="text-[11px] uppercase tracking-[0.12em] text-ink-faint hover:text-gold"
                    onClick={() => onDone(item)}
                  >
                    Done
                  </button>
                )}
              </div>
              <div
                className={cn(
                  "mt-1 text-[15px] text-ink",
                  item.status === "completed" && "text-ink-muted line-through decoration-white/20",
                  item.status === "missed" && "text-rose",
                )}
              >
                {item.title}
              </div>
              <div className="mt-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-ink-faint">
                <span>{statusCopy[item.status]}</span>
                {item.goal_title && (
                  <>
                    <span className="text-white/20">·</span>
                    <span className="truncate text-gold/80">{item.goal_title}</span>
                  </>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>

      {pending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-sm rounded-2xl border border-line bg-bg-elevated p-5">
            <div className="text-[11px] uppercase tracking-[0.16em] text-ink-faint">Session complete</div>
            <h3 className="mt-2 text-lg text-ink">{pending.item.title}</h3>
            <p className="mt-2 text-sm text-ink-muted">
              How many {pending.metric.unit || "units"} did you finish in this block?
            </p>
            <Input
              className="mt-4"
              type="number"
              min={0}
              step="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={`e.g. 2 ${pending.metric.unit}`}
              autoFocus
            />
            <p className="mt-2 text-xs text-ink-faint">
              Currently {pending.metric.current}/{pending.metric.target} {pending.metric.unit}
            </p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <Button variant="ghost" onClick={() => setPending(null)} disabled={saving}>
                Cancel
              </Button>
              <Button
                variant="outline"
                onClick={() => complete(pending.item, 0, pending.metric.goalId)}
                disabled={saving}
              >
                Just mark done
              </Button>
              <Button
                onClick={() => complete(pending.item, Number(amount) || 0, pending.metric.goalId)}
                disabled={saving || amount === ""}
              >
                {saving ? "Saving…" : "Add progress"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function StatusDot({ status }: { status: ScheduleStatus }) {
  if (status === "completed") {
    return (
      <span className="relative z-10 mt-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-gold text-bg">
        <Check className="h-2.5 w-2.5" />
      </span>
    );
  }
  if (status === "in_progress") {
    return <span className="pulse-gold relative z-10 mt-0.5 h-4 w-4 rounded-full bg-gold" />;
  }
  if (status === "missed") {
    return <span className="relative z-10 mt-0.5 h-4 w-4 rounded-full border border-rose/70" />;
  }
  return (
    <span className="relative z-10 mt-0.5 flex h-4 w-4 items-center justify-center text-ink-faint">
      <Circle className="h-3.5 w-3.5" />
    </span>
  );
}
