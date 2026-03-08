"use client";

import { useState } from "react";
import type { ClarifyQuestion } from "@/lib/types";
import { MessageCircleQuestion, ArrowRight, SkipForward } from "lucide-react";
import clsx from "clsx";

interface Props {
  questions: ClarifyQuestion[];
  onSubmit: (answers: Record<string, string>) => void;
  onSkip: () => void;
}

export function ClarifyCard({ questions, onSubmit, onSkip }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function handleChange(id: string, value: string) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  function handleSubmit() {
    setSubmitting(true);
    onSubmit(answers);
  }

  const hasAnswers = Object.values(answers).some((v) => v.trim());

  return (
    <div className="msg-assistant animate-fade-in">
      <div className="msg-assistant-avatar">
        <MessageCircleQuestion size={14} />
      </div>

      <div className="msg-assistant-content">
        <div className="rounded-xl border border-[var(--accent)] border-opacity-30 bg-[var(--accent-light)] overflow-hidden animate-scale-in">
          {/* Header */}
          <div className="px-4 py-3 border-b border-[var(--accent)] border-opacity-20">
            <p className="text-sm font-medium text-[var(--text)]">
              A few questions to refine the analysis
            </p>
            <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
              Answer what you can, or skip to proceed with defaults.
            </p>
          </div>

          {/* Questions */}
          <div className="px-4 py-3 space-y-3">
            {questions.map((q, i) => (
              <div
                key={q.id}
                className="animate-slide-up"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  {q.question}
                </label>
                <input
                  type="text"
                  value={answers[q.id] || ""}
                  onChange={(e) => handleChange(q.id, e.target.value)}
                  placeholder={q.placeholder}
                  disabled={submitting}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm outline-none transition-all focus:border-[var(--border-focus)] focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-opacity-20 placeholder:text-[var(--text-muted)] disabled:opacity-50"
                />
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-[var(--accent)] border-opacity-20">
            <button
              onClick={onSkip}
              disabled={submitting}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] transition-all hover:bg-[var(--bg-hover)] hover:text-[var(--text)] disabled:opacity-50"
            >
              <SkipForward size={12} />
              Skip
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !hasAnswers}
              className={clsx(
                "flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-xs font-medium text-white transition-all",
                "bg-[var(--accent)] hover:bg-[var(--accent-dark)] hover:scale-[1.02] active:scale-[0.98]",
                "disabled:opacity-40",
                submitting && "animate-pulse"
              )}
            >
              Proceed
              <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
