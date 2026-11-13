import { useEffect, useRef, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";

type Layout = {
  schedule: number;
  context: number;
};

const DEFAULT: Layout = { schedule: 300, context: 320 };
const KEY = "kairos.today-panels";

function readLayout(): Layout {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return DEFAULT;
    const parsed = JSON.parse(raw) as Layout;
    return {
      schedule: Math.min(480, Math.max(220, parsed.schedule || DEFAULT.schedule)),
      context: Math.min(480, Math.max(220, parsed.context || DEFAULT.context)),
    };
  } catch {
    return DEFAULT;
  }
}

export function ResizableToday({
  schedule,
  chat,
  context,
}: {
  schedule: ReactNode;
  chat: ReactNode;
  context: ReactNode;
}) {
  const layout = useRef<Layout>(readLayout());
  const shell = useRef<HTMLDivElement>(null);
  const left = useRef<HTMLElement>(null);
  const right = useRef<HTMLElement>(null);

  useEffect(() => {
    if (left.current) left.current.style.width = `${layout.current.schedule}px`;
    if (right.current) right.current.style.width = `${layout.current.context}px`;
  }, []);

  const persist = () => {
    localStorage.setItem(KEY, JSON.stringify(layout.current));
  };

  const drag = (side: "schedule" | "context", event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const start = layout.current[side];
    const move = (e: globalThis.PointerEvent) => {
      const dx = e.clientX - startX;
      const next = side === "schedule" ? start + dx : start - dx;
      const clamped = Math.min(480, Math.max(220, next));
      layout.current[side] = clamped;
      const el = side === "schedule" ? left.current : right.current;
      if (el) el.style.width = `${clamped}px`;
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      persist();
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };

  return (
    <div ref={shell} className="flex min-h-0 flex-1">
      <section
        ref={left}
        className="hidden min-h-0 shrink-0 overflow-y-auto border-r border-line p-6 lg:block"
        style={{ width: layout.current.schedule }}
      >
        {schedule}
      </section>
      <button
        type="button"
        aria-label="Resize schedule"
        className="hidden w-1.5 shrink-0 cursor-col-resize bg-transparent hover:bg-gold/50 lg:block"
        onPointerDown={(e) => drag("schedule", e)}
      />
      <section className="min-h-0 min-w-[280px] flex-1">{chat}</section>
      <button
        type="button"
        aria-label="Resize context"
        className="hidden w-1.5 shrink-0 cursor-col-resize bg-transparent hover:bg-gold/50 xl:block"
        onPointerDown={(e) => drag("context", e)}
      />
      <section
        ref={right}
        className="hidden min-h-0 shrink-0 overflow-y-auto p-6 xl:block"
        style={{ width: layout.current.context }}
      >
        {context}
      </section>
    </div>
  );
}
