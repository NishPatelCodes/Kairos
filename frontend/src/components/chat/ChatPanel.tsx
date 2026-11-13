import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { timeLabel } from "@/lib/utils";
import type { ChatMessage, ScheduleItem } from "@/types";

export function ChatPanel({
  messages,
  streaming,
  busy,
  onSend,
}: {
  messages: ChatMessage[];
  streaming: string;
  busy: boolean;
  onSend: (text: string) => void;
}) {
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const submit = () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    onSend(text);
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="mx-auto max-w-2xl space-y-6">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {streaming && (
            <MessageBubble
              message={{ id: "stream", role: "assistant", content: streaming }}
            />
          )}
          {busy && !streaming && (
            <div className="flex gap-1 pl-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold/80" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold/50 [animation-delay:120ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold/30 [animation-delay:240ms]" />
            </div>
          )}
          <div ref={bottom} />
        </div>
      </div>
      <div className="border-t border-line p-4 md:px-8">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-line bg-bg-elevated p-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder="Tell Kairos what you're doing next…"
            className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-faint"
          />
          <Button size="icon" onClick={submit} disabled={busy || !draft.trim()} className="shrink-0">
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>
        <p className="mx-auto mt-2 max-w-2xl text-center text-[11px] text-ink-faint">
          Enter to send · Shift+Enter for a new line
        </p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[80%] rounded-2xl rounded-br-md bg-bg-hover px-4 py-3 text-sm leading-relaxed text-ink"
            : "max-w-[92%] text-sm leading-relaxed text-ink/90"
        }
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="chat-md">
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          </div>
        )}
        {message.metadata?.blocks?.map((block, index) => {
          if (block.item) return <ScheduleCard key={`${message.id}-${index}`} item={block.item} />;
          if (block.items?.length) {
            return (
              <div key={`${message.id}-${index}`} className="mt-3 space-y-2">
                {block.items.map((item) => (
                  <ScheduleCard key={item.id} item={item} />
                ))}
              </div>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}

function ScheduleCard({ item }: { item: ScheduleItem }) {
  return (
    <div className="mt-3 max-w-sm rounded-xl border border-line bg-bg-elevated px-4 py-3">
      <div className="text-xs tabular-nums text-gold">
        {timeLabel(item.start_time)} – {timeLabel(item.end_time)}
      </div>
      <div className="mt-1 text-sm text-ink">{item.title}</div>
      {item.goal_title && (
        <div className="mt-1 text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          {item.goal_title}
        </div>
      )}
    </div>
  );
}
