import type { ExpertReviewMsg } from "@/lib/types";
import { FlaskConical, User, MessageSquare } from "lucide-react";
import clsx from "clsx";

interface Props {
  messages: ExpertReviewMsg[];
}

export function ExpertReviewCard({ messages }: Props) {
  if (messages.length === 0) return null;

  const channel = messages[0]?.channel || "#review";
  const lastMsg = messages[messages.length - 1];
  const isResolved = lastMsg?.status === "approved" || lastMsg?.status === "revised" || lastMsg?.status === "rejected";

  return (
    <div
      className={clsx(
        "rounded-lg border text-sm animate-scale-in overflow-hidden",
        isResolved
          ? "border-[var(--green)] bg-[var(--green-bg)]"
          : "border-[var(--orange)] bg-[var(--orange-bg)]"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-current/10">
        <MessageSquare size={13} className={isResolved ? "text-[var(--green)]" : "text-[var(--orange)]"} />
        <span className={clsx(
          "text-xs font-semibold uppercase tracking-wider",
          isResolved ? "text-[var(--green)]" : "text-[var(--orange)]"
        )}>
          Expert Review
        </span>
        <span className="text-[11px] text-[var(--text-muted)] font-mono">{channel}</span>
        {isResolved && (
          <span className="ml-auto rounded-full bg-[var(--green)] px-2 py-0.5 text-[10px] font-medium text-white">
            {lastMsg.status}
          </span>
        )}
      </div>

      {/* Conversation thread */}
      <div className="px-4 py-3 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className="flex items-start gap-2.5 animate-fade-in">
            {/* Avatar */}
            <div className={clsx(
              "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white",
              msg.role === "agent" ? "bg-[var(--accent)]" : "bg-emerald-600"
            )}>
              {msg.role === "agent" ? <FlaskConical size={12} /> : <User size={12} />}
            </div>

            {/* Message body */}
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline gap-1.5">
                <span className="text-xs font-semibold">{msg.name}</span>
                <span className="text-[10px] text-[var(--text-muted)]">{msg.title}</span>
              </div>
              <p className="text-xs leading-relaxed mt-0.5 whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}

        {/* Typing indicator when not resolved */}
        {!isResolved && (
          <div className="flex items-center gap-2 pl-8">
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] typing-dot" />
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
