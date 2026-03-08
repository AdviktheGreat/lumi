"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { FlaskConical, User, Hash, CheckCircle2, XCircle, RotateCcw } from "lucide-react";
import clsx from "clsx";

interface ReviewMessage {
  role: "agent" | "expert";
  name: string;
  title: string;
  text: string;
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
        text: "MDS-UPDRS Part 3 off-medication: exenatide -1.0 pts vs placebo +2.1 pts (adjusted difference: -3.5, 95% CI: -6.7 to -0.3, p=0.04). No independent replication yet, but Exenatide-PD3 Phase III (NCT04232969, n=200) is actively recruiting. Lixisenatide and NLY01 (brain-penetrant GLP-1 agonist) Phase II trials also ongoing.",
      },
      {
        role: "expert",
        name: "Dr. Sarah Chen",
        title: "Neuropharmacologist",
        text: "Effect size is modest but statistically significant. Given it's a single underpowered trial, I'll approve this for inclusion with an explicit uncertainty label. The open-label extension showed benefit persisted at 2 years, which is encouraging. Track the Phase III for definitive evidence.",
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
        text: "I've flagged a finding on PD-L1/PARP-trapping bispecific antibody feasibility for expert review. Confidence is 32%. The concept has mechanistic rationale — simultaneous PARP trapping and immune checkpoint blockade in BRCA1-deficient TNBC — but no experimental validation exists. The PARP-trapping moiety has never been successfully conjugated to an antibody scaffold.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "Interesting concept. What structural data supports a bispecific format here? PARP trapping requires the inhibitor to physically trap PARP1 on DNA — how would you achieve that from an antibody-conjugated payload? And what does your Rosetta modeling show for linker geometry?",
      },
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "Rosetta modeling suggests a PEG₈-linked talazoparib warhead on the Fab arm could maintain PARP-trapping activity (predicted IC₅₀ shift: 3.2x vs free talazoparib). The anti-PD-L1 arm uses the atezolizumab CDR scaffold. DMS analysis shows linker orientation is critical — 4/12 configurations maintain >50% trapping efficiency. CMC concern: the talazoparib-linker conjugate shows 15% aggregation at 40°C/4wk in accelerated stability.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "The 3x IC₅₀ shift is concerning but not disqualifying for proof-of-concept. I'll approve this for in silico exploration only — do NOT include as a clinical recommendation. The CMC challenges alone (dual-payload stability, 15% aggregation, conjugation-site heterogeneity) make this 3-5 years from IND-enabling studies at best. Flag clearly as exploratory and focus near-term efforts on the conventional olaparib + atezolizumab combination.",
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

function ReviewContent() {
  const searchParams = useSearchParams();
  const finding = searchParams.get("finding") || "No finding specified";
  const agent = searchParams.get("agent") || "unknown_agent";
  const confidence = parseFloat(searchParams.get("confidence") || "0");
  const reason = searchParams.get("reason") || "";
  const findingId = searchParams.get("finding_id") || "review_001";
  const chatId = searchParams.get("chat_id") || "";

  const conv = getConversation(finding);
  const channelName = searchParams.get("channel") || conv.channel;
  const mockMessages = conv.messages;

  const [visibleMessages, setVisibleMessages] = useState<ReviewMessage[]>([]);
  const [typing, setTyping] = useState(false);
  const [resolved, setResolved] = useState<"approved" | "revised" | "rejected" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const playedRef = useRef(false);

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

  const confidencePct = Math.round((isNaN(confidence) ? 0 : confidence) * 100);

  useEffect(() => {
    if (playedRef.current) return;
    playedRef.current = true;

    let cancelled = false;
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
      // Auto-resolve after conversation plays
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
    <div className="flex h-screen flex-col" style={{ fontFamily: "'Lato', 'Segoe UI', sans-serif" }}>
      {/* Header bar */}
      <header className="shrink-0 flex items-center gap-3 border-b border-gray-200 bg-white px-5 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
          <FlaskConical size={16} />
        </div>
        <div className="flex items-center gap-2">
          <Hash size={14} className="text-gray-400" />
          <span className="text-sm font-bold text-gray-900">{channelName}</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span
            className={clsx(
              "rounded-full px-2.5 py-1 text-xs font-semibold text-white",
              confidencePct >= 70 ? "bg-green-500" : confidencePct >= 50 ? "bg-yellow-500" : "bg-orange-500"
            )}
          >
            {confidencePct}% confidence
          </span>
          <span className="text-xs text-gray-500 font-mono">{findingId}</span>
        </div>
      </header>

      {/* Finding summary */}
      <div className="shrink-0 border-b border-gray-200 bg-gray-50 px-5 py-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded bg-orange-100 text-orange-600">
            <span className="text-xs font-bold">!</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 leading-snug">{finding}</p>
            <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
              <span>Agent: <span className="font-mono text-gray-700">{agent}</span></span>
              {reason && <span className="truncate">{reason}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Message thread */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto bg-white px-5 py-4">
        <div className="max-w-2xl mx-auto space-y-4">
          {visibleMessages.map((msg, i) => (
            <div
              key={i}
              className="flex items-start gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300"
            >
              {/* Avatar */}
              <div
                className={clsx(
                  "mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white",
                  msg.role === "agent" ? "bg-indigo-600" : "bg-emerald-600"
                )}
              >
                {msg.role === "agent" ? <FlaskConical size={16} /> : <User size={16} />}
              </div>

              {/* Message body */}
              <div className="min-w-0 flex-1 pt-0.5">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-bold text-gray-900">{msg.name}</span>
                  <span className="text-xs text-gray-400">{msg.title}</span>
                  <span className="text-xs text-gray-300">
                    {new Date(Date.now() - (mockMessages.length - i) * 60000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <p className="mt-1 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && !resolved && (
            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-200">
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </span>
              </div>
              <div className="pt-3">
                <span className="text-xs text-gray-400">typing...</span>
              </div>
            </div>
          )}

          {/* Resolution banner */}
          {resolved && (
            <div
              className={clsx(
                "rounded-lg border px-4 py-3 flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300",
                resolved === "approved"
                  ? "border-green-200 bg-green-50"
                  : resolved === "revised"
                    ? "border-yellow-200 bg-yellow-50"
                    : "border-red-200 bg-red-50"
              )}
            >
              {resolved === "approved" ? (
                <CheckCircle2 size={18} className="text-green-600 shrink-0" />
              ) : resolved === "rejected" ? (
                <XCircle size={18} className="text-red-600 shrink-0" />
              ) : (
                <RotateCcw size={18} className="text-yellow-600 shrink-0" />
              )}
              <div>
                <p className="text-sm font-semibold text-gray-900 capitalize">
                  Finding {resolved}
                </p>
                <p className="text-xs text-gray-500">
                  {resolved === "approved"
                    ? "Include with explicit uncertainty label. Track Phase III for definitive evidence."
                    : resolved === "revised"
                      ? "Finding sent back for revision with expert feedback."
                      : "Finding rejected. Will not be included in final report."}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="shrink-0 border-t border-gray-200 bg-gray-50 px-5 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button
            onClick={() => submitDecision("approved")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
              resolved === "approved"
                ? "bg-green-600 text-white"
                : resolved !== null
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700 active:scale-95"
            )}
          >
            <CheckCircle2 size={15} />
            Approve with caveat
          </button>
          <button
            onClick={() => submitDecision("revised")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
              resolved === "revised"
                ? "bg-yellow-500 text-white"
                : resolved !== null
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:scale-95"
            )}
          >
            <RotateCcw size={15} />
            Revise
          </button>
          <button
            onClick={() => submitDecision("rejected")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
              resolved === "rejected"
                ? "bg-red-600 text-white"
                : resolved !== null
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:scale-95"
            )}
          >
            <XCircle size={15} />
            Reject
          </button>
          {resolved && (
            <span className="ml-auto text-xs text-gray-400">
              Decision recorded. You can close this tab.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <span className="text-sm text-gray-500">Loading review...</span>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
