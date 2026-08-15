import { Check, Circle } from "lucide-react";

import { api } from "@/lib/api";
import { cn, timeLabel } from "@/lib/utils";
import type { ScheduleItem, ScheduleStatus } from "@/types";

const statusCopy: Record<ScheduleStatus, string> = {
  completed: "Completed",
  in_progress: "In progress",
  upcoming: "Upcoming",
  missed: "Missed",
  rescheduled: "Rescheduled",
};

export function ScheduleTimeline({
  items,
  onChange,
}: {
  items: ScheduleItem[];
  onChange: () => void;
}) {
  if (!items.length) {
    return (
      <div className="px-1 py-10 text-sm leading-relaxed text-ink-faint">
        Nothing on the board yet. Tell Kairos what the next few hours should look like.
      </div>
    );
  }

  return (
    <ol className="relative space-y-0">
      {items.map((item, index) => (
        <li key={item.id} className="relative flex gap-4 pb-6">
          {index < items.length - 1 && (
            <span className="absolute left-[7px] top-4 h-full w-px bg-line" />
          )}
          <StatusDot status={item.status} />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <time className="text-xs tabular-nums tracking-wide text-ink-faint">
                {timeLabel(item.start_time)} – {timeLabel(item.end_time)}
              </time>
              {item.status !== "completed" && item.status !== "rescheduled" && (
                <button
                  className="text-[11px] uppercase tracking-[0.12em] text-ink-faint hover:text-gold"
                  onClick={() =>
                    api(`/api/schedule/${item.id}/complete/`, { method: "POST" }).then(onChange)
                  }
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
