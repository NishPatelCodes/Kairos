import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-11 w-full rounded-lg border border-line bg-bg-elevated px-3 text-sm text-ink placeholder:text-ink-faint outline-none transition focus:border-line-strong focus:ring-1 focus:ring-gold/40",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-[88px] w-full rounded-xl border border-line bg-bg-elevated px-3 py-3 text-sm text-ink placeholder:text-ink-faint outline-none transition focus:border-line-strong focus:ring-1 focus:ring-gold/40",
        className,
      )}
      {...props}
    />
  );
}
