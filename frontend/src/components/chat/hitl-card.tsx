import type { HitlRequest } from "@/lib/types";
import { ExternalLink } from "lucide-react";
import clsx from "clsx";

interface Props {
  hitl: HitlRequest;
  reviewUrl?: string;
}

export function HitlCard({ hitl, reviewUrl }: Props) {
  const isPending = hitl.status === "pending";
  const isApproved = hitl.status === "approved";

  return (
    <div
      className={clsx(
        "rounded-lg border px-4 py-3 text-sm transition-all duration-500 animate-scale-in",
        isPending
          ? "border-[var(--orange)] bg-[var(--orange-bg)] animate-glow-pulse"
          : isApproved
            ? "border-[var(--green)] bg-[var(--green-bg)]"
            : "border-[var(--red)] bg-[var(--red-bg)]"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-1.5">
        <span className={clsx(
          "text-xs font-semibold uppercase tracking-wider transition-colors duration-300",
          isPending ? "text-[var(--orange)]" : isApproved ? "text-[var(--green)]" : "text-[var(--red)]"
        )}>
          {isPending ? "HITL Review Required" : `HITL ${hitl.status}`}
        </span>
        <span
          className={clsx(
            "rounded-full px-2 py-0.5 text-[10px] font-semibold text-white transition-all duration-300",
            isPending
              ? "bg-[var(--orange)]"
              : isApproved
                ? "bg-[var(--green)]"
                : "bg-[var(--red)]"
          )}
        >
          {hitl.confidence_score !== undefined
            ? `${Math.round(hitl.confidence_score * 100)}% confidence`
            : hitl.status}
        </span>
      </div>

      {/* Finding */}
      <p className="text-xs leading-relaxed mb-1.5">{hitl.finding}</p>

      {/* Agent + reason */}
      <div className="flex items-start gap-2 text-[11px] opacity-80">
        <span className="font-mono">{hitl.agent_id}</span>
        <span>&mdash;</span>
        <span>{hitl.reason}</span>
      </div>

      {/* Pending — review button + routing indicator */}
      {isPending && (
        <div className="mt-2.5 flex items-center gap-3">
          {reviewUrl && (
            <a
              href={reviewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-md bg-[var(--orange)] px-3 py-1.5 text-[11px] font-semibold text-white transition-all hover:brightness-110 active:scale-95"
            >
              <ExternalLink size={12} />
              View Review
            </a>
          )}
          <span className="flex items-center gap-2">
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
            </span>
            <span className="text-[11px] text-[var(--orange)]">Routing to domain expert...</span>
          </span>
        </div>
      )}
    </div>
  );
}
