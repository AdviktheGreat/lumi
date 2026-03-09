"use client";

import { useEffect, useState, useRef } from "react";
import { FlaskConical, User, Hash, CheckCircle2, XCircle, RotateCcw, X } from "lucide-react";
import clsx from "clsx";

interface ReviewMessage {
  role: "agent" | "expert";
  name: string;
  title: string;
  text: string;
}

export interface ReviewData {
  finding: string;
  agent: string;
  confidence: number;
  reason: string;
  findingId: string;
  chatId: string;
}

const CONVERSATIONS: Record<string, { channel: string; messages: ReviewMessage[] }> = {
  glp1r: {
    channel: "neuro-repurposing",
    messages: [
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "I've flagged a clinical finding for your review. The evidence suggests GLP-1R agonists may be disease-modifying in Parkinson's, but confidence is low (38%). The primary evidence is a single Phase II trial with 62 participants (Athauda et al., 2017).",
      },
      {
        role: "expert",
        name: "Dr. Sarah Chen",
        title: "Neuropharmacologist",
        text: "The Athauda 2017 exenatide trial showed motor improvement at 60 weeks, but it was open-label initially. What was the effect size in the placebo-controlled phase? And are there any replication studies underway?",
      },
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "MDS-UPDRS Part 3 off-medication: exenatide -1.0 pts vs placebo +2.1 pts (adjusted difference: -3.5, 95% CI: -6.7 to -0.3, p=0.04). No independent replication yet, but Exenatide-PD3 Phase III (NCT04232969, n=200) is actively recruiting.",
      },
      {
        role: "expert",
        name: "Dr. Sarah Chen",
        title: "Neuropharmacologist",
        text: "Effect size is modest but statistically significant. I'll approve this for inclusion with an explicit uncertainty label. Track the Phase III for definitive evidence.",
      },
    ],
  },
  parp: {
    channel: "tnbc-combination-therapy",
    messages: [
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "I've flagged a finding on PD-L1/PARP-trapping bispecific antibody feasibility for expert review. Confidence is 32%. No experimental validation exists for this format.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "What structural data supports a bispecific format here? PARP trapping requires the inhibitor to physically trap PARP1 on DNA — how would you achieve that from an antibody-conjugated payload?",
      },
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "Rosetta modeling suggests a PEG\u2088-linked talazoparib warhead on the Fab arm could maintain PARP-trapping activity (predicted IC\u2085\u2080 shift: 3.2x). 4/12 linker configurations maintain >50% trapping efficiency. CMC concern: 15% aggregation at 40\u00b0C/4wk.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "I'll approve for in silico exploration only — do NOT include as a clinical recommendation. Focus near-term efforts on the conventional olaparib + atezolizumab combination.",
      },
    ],
  },
};

function getConversation(finding: string): { channel: string; messages: ReviewMessage[] } {
  const f = finding.toLowerCase();
  if (f.includes("parp") || f.includes("bispecific") || f.includes("brca") || f.includes("tnbc")) {
    return CONVERSATIONS.parp;
  }
  return CONVERSATIONS.glp1r;
}

interface Props {
  review: ReviewData;
  onClose: () => void;
}

export function ReviewPanel({ review, onClose }: Props) {
  const { finding, agent, confidence, reason, findingId, chatId } = review;
  const conv = getConversation(finding);
  const channelName = conv.channel;
  const mockMessages = conv.messages;

  const [visibleMessages, setVisibleMessages] = useState<ReviewMessage[]>([]);
  const [typing, setTyping] = useState(false);
  const [resolved, setResolved] = useState<"approved" | "revised" | "rejected" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const confidencePct = Math.round((isNaN(confidence) ? 0 : confidence) * 100);

  async function submitDecision(decision: "approved" | "revised" | "rejected") {
    setSubmitting(true);
    setResolved(decision);
    if (chatId) {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";
        await fetch(`${apiBase}/chats/${chatId}/review/${findingId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            status: decision === "revised" ? "rejected" : decision,
            feedback: decision === "revised" ? "Sent back for revision" : "",
          }),
        });
      } catch (err) {
        console.error("Failed to submit review decision:", err);
      }
    }
    setSubmitting(false);
  }

  useEffect(() => {
    let cancelled = false;
    setVisibleMessages([]);
    setTyping(false);
    setResolved(null);
    async function playConversation() {
      for (let i = 0; i < mockMessages.length; i++) {
        if (cancelled) return;
        setTyping(true);
        await new Promise((r) => setTimeout(r, i === 0 ? 1500 : 2500));
        if (cancelled) return;
        setTyping(false);
        setVisibleMessages((prev) => [...prev, mockMessages[i]]);
        await new Promise((r) => setTimeout(r, 500));
      }
      if (!cancelled) {
        await new Promise((r) => setTimeout(r, 1000));
        if (!cancelled) setResolved("approved");
      }
    }
    playConversation();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [visibleMessages, typing, resolved]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
        <div className="flex items-center gap-1.5 min-w-0">
          <Hash size={12} className="shrink-0 text-[var(--text-muted)]" />
          <span className="text-xs font-semibold text-[var(--text)] truncate">{channelName}</span>
          <span
            className={clsx(
              "shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-semibold text-white ml-1",
              confidencePct >= 70 ? "bg-[var(--green)]" : "bg-[var(--orange)]"
            )}
          >
            {confidencePct}%
          </span>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 rounded-md p-1 text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text)] transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      {/* Finding summary */}
      <div className="shrink-0 border-b border-[var(--border)] bg-[var(--orange-bg)] px-4 py-2.5">
        <p className="text-[11px] font-medium text-[var(--text)] leading-snug line-clamp-3">{finding}</p>
        <div className="mt-1 flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
          <span className="font-mono">{agent}</span>
          <span>&mdash;</span>
          <span className="truncate">{reason.split(".")[0]}</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3">
        <div className="space-y-3">
          {visibleMessages.map((msg, i) => (
            <div key={i} className="flex items-start gap-2 animate-slide-up">
              <div
                className={clsx(
                  "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white",
                  msg.role === "agent" ? "bg-[var(--accent)]" : "bg-emerald-600"
                )}
              >
                {msg.role === "agent" ? <FlaskConical size={10} /> : <User size={10} />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-[11px] font-semibold text-[var(--text)]">{msg.name}</span>
                  <span className="text-[9px] text-[var(--text-muted)]">{msg.title}</span>
                </div>
                <p className="mt-0.5 text-[11px] leading-relaxed text-[var(--text-secondary)]">{msg.text}</p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && !resolved && (
            <div className="flex items-start gap-2 animate-fade-in">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--bg-hover)]">
                <span className="flex items-center gap-0.5">
                  <span className="h-1 w-1 rounded-full bg-[var(--text-muted)] typing-dot" />
                  <span className="h-1 w-1 rounded-full bg-[var(--text-muted)] typing-dot" />
                  <span className="h-1 w-1 rounded-full bg-[var(--text-muted)] typing-dot" />
                </span>
              </div>
              <span className="pt-1.5 text-[10px] text-[var(--text-muted)]">typing...</span>
            </div>
          )}

          {/* Resolution banner */}
          {resolved && (
            <div
              className={clsx(
                "rounded-lg border px-3 py-2 flex items-center gap-2 animate-scale-in",
                resolved === "approved"
                  ? "border-[var(--green)] bg-[var(--green-bg)]"
                  : resolved === "revised"
                    ? "border-[var(--orange)] bg-[var(--orange-bg)]"
                    : "border-[var(--red)] bg-[var(--red-bg)]"
              )}
            >
              {resolved === "approved" ? (
                <CheckCircle2 size={13} className="text-[var(--green)] shrink-0" />
              ) : resolved === "rejected" ? (
                <XCircle size={13} className="text-[var(--red)] shrink-0" />
              ) : (
                <RotateCcw size={13} className="text-[var(--orange)] shrink-0" />
              )}
              <div>
                <p className="text-[11px] font-semibold text-[var(--text)] capitalize">Finding {resolved}</p>
                <p className="text-[10px] text-[var(--text-muted)]">
                  {resolved === "approved"
                    ? "Included with uncertainty label."
                    : resolved === "revised"
                      ? "Sent back for revision."
                      : "Will not be included in report."}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="shrink-0 border-t border-[var(--border)] px-3 py-2.5 flex flex-wrap gap-1.5">
        <button
          onClick={() => submitDecision("approved")}
          disabled={resolved !== null || submitting}
          className={clsx(
            "flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[10px] font-semibold transition-all",
            resolved === "approved"
              ? "bg-[var(--green)] text-white"
              : resolved !== null
                ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                : "bg-[var(--green)] text-white hover:brightness-110 active:scale-95"
          )}
        >
          <CheckCircle2 size={11} />
          Approve
        </button>
        <button
          onClick={() => submitDecision("revised")}
          disabled={resolved !== null || submitting}
          className={clsx(
            "flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[10px] font-semibold transition-all",
            resolved === "revised"
              ? "bg-[var(--orange)] text-white"
              : resolved !== null
                ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                : "border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] active:scale-95"
          )}
        >
          <RotateCcw size={11} />
          Revise
        </button>
        <button
          onClick={() => submitDecision("rejected")}
          disabled={resolved !== null || submitting}
          className={clsx(
            "flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[10px] font-semibold transition-all",
            resolved === "rejected"
              ? "bg-[var(--red)] text-white"
              : resolved !== null
                ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                : "border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] active:scale-95"
          )}
        >
          <XCircle size={11} />
          Reject
        </button>
      </div>
    </div>
  );
}
