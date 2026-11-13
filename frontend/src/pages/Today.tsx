import { useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useMemo, useState } from "react";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { ContextPanel } from "@/components/context/ContextPanel";
import { ResizableToday } from "@/components/layout/ResizableToday";
import { ScheduleTimeline } from "@/components/schedule/ScheduleTimeline";
import { Skeleton } from "@/components/ui/skeleton";
import { api, streamChat } from "@/lib/api";
import { formatMinutes, greeting } from "@/lib/utils";
import type {
  AnnualGoal,
  ChatMessage,
  Conversation,
  DailyProgress,
  MonthlyGoal,
  Profile,
  ScheduleItem,
} from "@/types";

export function TodayPage() {
  const queryClient = useQueryClient();
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);

  const me = useQuery({ queryKey: ["me"], queryFn: () => api<Profile>("/api/auth/me/") });
  const annual = useQuery({
    queryKey: ["annual"],
    queryFn: () => api<AnnualGoal[]>("/api/goals/annual/"),
  });
  const monthly = useQuery({
    queryKey: ["monthly"],
    queryFn: () => api<MonthlyGoal[]>("/api/goals/monthly/"),
  });
  const schedule = useQuery({
    queryKey: ["schedule"],
    queryFn: () => api<ScheduleItem[]>("/api/schedule/"),
  });
  const daily = useQuery({
    queryKey: ["progress-daily"],
    queryFn: () => api<DailyProgress>("/api/progress/daily/"),
  });
  const conversation = useQuery({
    queryKey: ["conversation"],
    queryFn: async () => {
      await api<Conversation>("/api/ai/startup/", { method: "POST" });
      return api<Conversation>("/api/conversations/today/");
    },
  });

  const activeAnnual = annual.data?.find((g) => g.is_active) ?? annual.data?.[0];
  const messages = conversation.data?.messages ?? [];
  const focus = useMemo(() => {
    const active = schedule.data?.find((i) => i.status === "in_progress");
    return active?.title ?? schedule.data?.find((i) => i.status === "upcoming")?.title;
  }, [schedule.data]);

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ["schedule"] });
    queryClient.invalidateQueries({ queryKey: ["progress-daily"] });
    queryClient.invalidateQueries({ queryKey: ["monthly"] });
    queryClient.invalidateQueries({ queryKey: ["annual"] });
    queryClient.invalidateQueries({ queryKey: ["me"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const send = async (text: string) => {
    const optimistic: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
    };
    queryClient.setQueryData<Conversation>(["conversation"], (current) =>
      current ? { ...current, messages: [...current.messages, optimistic] } : current,
    );
    setBusy(true);
    setStreaming("");
    let acc = "";
    try {
      await streamChat(text, (event, data) => {
        if (event === "token") {
          acc += String(data.content ?? "");
          setStreaming(acc);
        }
        if (event === "done") {
          setStreaming("");
          queryClient.invalidateQueries({ queryKey: ["conversation"] });
          refreshAll();
        }
        if (event === "error" && !acc) {
          setStreaming("");
        }
      });
    } finally {
      setBusy(false);
      setStreaming("");
      queryClient.invalidateQueries({ queryKey: ["conversation"] });
    }
  };

  const loading = me.isLoading || conversation.isLoading;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="shrink-0 border-b border-line px-6 py-5 md:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.2em] text-gold">{greeting()}</div>
            <h1 className="mt-1 font-serif text-3xl text-ink">{format(new Date(), "EEEE, MMMM d")}</h1>
            <p className="mt-2 text-sm text-ink-muted">
              {focus ? (
                <>
                  Your focus: <span className="text-ink">{focus}</span>
                </>
              ) : (
                "Open the next few hours with Kairos."
              )}
            </p>
          </div>
          {daily.data && (
            <div className="flex gap-6 text-sm">
              <HeaderStat label="Tasks" value={String(daily.data.planned_count)} />
              <HeaderStat label="Planned" value={formatMinutes(daily.data.planned_minutes)} />
              <HeaderStat label="Done" value={formatMinutes(daily.data.completed_minutes)} />
            </div>
          )}
        </div>
      </header>

      <div className="max-h-56 shrink-0 overflow-y-auto border-b border-line px-6 py-4 lg:hidden">
        <div className="mb-3 text-[11px] uppercase tracking-[0.18em] text-ink-faint">Today's schedule</div>
        <ScheduleTimeline items={schedule.data ?? []} monthly={monthly.data ?? []} onChange={refreshAll} />
      </div>

      <ResizableToday
        schedule={
          <>
            <div className="mb-5 text-[11px] uppercase tracking-[0.18em] text-ink-faint">Today's schedule</div>
            {schedule.isLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-14" />
                <Skeleton className="h-14" />
                <Skeleton className="h-14" />
              </div>
            ) : (
              <ScheduleTimeline items={schedule.data ?? []} monthly={monthly.data ?? []} onChange={refreshAll} />
            )}
          </>
        }
        chat={
          loading ? (
            <div className="space-y-4 p-8">
              <Skeleton className="h-24" />
              <Skeleton className="h-16" />
            </div>
          ) : (
            <ChatPanel messages={messages} streaming={streaming} busy={busy} onSend={send} />
          )
        }
        context={
          <ContextPanel
            annual={activeAnnual}
            monthly={monthly.data ?? []}
            daily={daily.data}
            onGoalChange={refreshAll}
          />
        }
      />
    </div>
  );
}

function HeaderStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.14em] text-ink-faint">{label}</div>
      <div className="mt-1 tabular-nums text-ink">{value}</div>
    </div>
  );
}
