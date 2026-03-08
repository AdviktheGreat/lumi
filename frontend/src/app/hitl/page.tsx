"use client";

import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { AlertTriangle, CheckCircle2, XCircle, Send } from "lucide-react";
import clsx from "clsx";

function HitlReviewContent() {
  const params = useSearchParams();
  const finding = params.get("finding") || "";
  const agentId = params.get("agent") || "";
  const confidence = parseFloat(params.get("confidence") || "0");
  const reason = params.get("reason") || "";
  const confidencePct = Math.round(confidence * 100);

  const [decision, setDecision] = useState<"approved" | "rejected" | null>(null);
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit() {
    setSubmitted(true);
    // In a real app this would POST to the backend
    // For now it just shows the confirmation
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)]">
        <div className="max-w-lg text-center animate-scale-in">
          {decision === "approved" ? (
            <CheckCircle2 size={48} className="mx-auto text-[var(--green)] mb-4" />
          ) : (
            <XCircle size={48} className="mx-auto text-[var(--red)] mb-4" />
          )}
          <h1 className="text-xl font-semibold text-[var(--text)] mb-2">
            Finding {decision === "approved" ? "Approved" : "Rejected"}
          </h1>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            Your review has been recorded. You can close this tab.
          </p>
          {notes && (
            <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3 text-left">
              <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Your notes</p>
              <p className="text-sm text-[var(--text-secondary)]">{notes}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-6">
      <div className="w-full max-w-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--orange-bg)]">
            <AlertTriangle size={20} className="text-[var(--orange)]" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-[var(--text)]">Human-in-the-Loop Review</h1>
            <p className="text-xs text-[var(--text-muted)]">A finding requires expert review before inclusion in the report</p>
          </div>
        </div>

        {/* Finding card */}
        <div className="rounded-xl border border-[var(--orange)] border-opacity-40 bg-[var(--bg-card)] overflow-hidden mb-6 shadow-sm">
          {/* Meta bar */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border)] bg-[var(--orange-bg)] bg-opacity-30">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-[var(--text-secondary)]">{agentId}</span>
            </div>
            <span className={clsx(
              "rounded-full px-2.5 py-0.5 text-[11px] font-semibold text-white",
              confidencePct >= 50 ? "bg-[var(--orange)]" : "bg-[var(--red)]"
            )}>
              {confidencePct}% confidence
            </span>
          </div>

          {/* Finding text */}
          <div className="px-5 py-4">
            <p className="text-sm leading-relaxed text-[var(--text)]">{finding}</p>
          </div>

          {/* Reason */}
          <div className="px-5 py-3 border-t border-[var(--border)] bg-[var(--bg)]">
            <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Flag Reason</p>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{reason}</p>
          </div>
        </div>

        {/* Decision */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5 space-y-4">
          <p className="text-xs font-medium text-[var(--text)]">Your Decision</p>

          <div className="flex gap-3">
            <button
              onClick={() => setDecision("approved")}
              className={clsx(
                "flex-1 flex items-center justify-center gap-2 rounded-lg border py-3 text-sm font-medium transition-all",
                decision === "approved"
                  ? "border-[var(--green)] bg-[var(--green-bg)] text-[var(--green)]"
                  : "border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--green)] hover:text-[var(--green)]"
              )}
            >
              <CheckCircle2 size={16} />
              Approve with caveat
            </button>
            <button
              onClick={() => setDecision("rejected")}
              className={clsx(
                "flex-1 flex items-center justify-center gap-2 rounded-lg border py-3 text-sm font-medium transition-all",
                decision === "rejected"
                  ? "border-[var(--red)] bg-[var(--red-bg)] text-[var(--red)]"
                  : "border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--red)] hover:text-[var(--red)]"
              )}
            >
              <XCircle size={16} />
              Reject
            </button>
          </div>

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add reviewer notes (optional)..."
            rows={3}
            className="w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--bg)] px-4 py-3 text-sm outline-none transition-all focus:border-[var(--border-focus)] focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-opacity-20 placeholder:text-[var(--text-muted)]"
          />

          <button
            onClick={handleSubmit}
            disabled={!decision}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--accent)] py-3 text-sm font-medium text-white transition-all disabled:opacity-30 hover:bg-[var(--accent-dark)]"
          >
            <Send size={14} />
            Submit Review
          </button>
        </div>
      </div>
    </div>
  );
}

export default function HitlPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)]">
        <p className="text-sm text-[var(--text-muted)]">Loading review...</p>
      </div>
    }>
      <HitlReviewContent />
    </Suspense>
  );
}
