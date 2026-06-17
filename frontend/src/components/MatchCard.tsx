import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../lib/api";
import type { Match, MatchExplanation } from "../lib/types";

const COMPONENTS: { key: keyof Match["components"]; label: string }[] = [
  { key: "schedule_match", label: "Schedule" },
  { key: "subject_match", label: "Subjects" },
  { key: "learning_style", label: "Style" },
  { key: "goal_similarity", label: "Goals" },
  { key: "study_intensity", label: "Intensity" },
];

function scoreColor(score: number): string {
  if (score >= 70) return "text-growth";
  if (score >= 40) return "text-amber";
  return "text-slate";
}

export function MatchCard({ match }: { match: Match }) {
  const [explanation, setExplanation] = useState<MatchExplanation | null>(null);
  const [loading, setLoading] = useState(false);

  async function explain() {
    if (explanation) return;
    setLoading(true);
    try {
      setExplanation(await api.matchExplanation(match.partner.user_id));
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-surface border border-line shadow-card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-display text-xl">{match.partner.name}</p>
          <p className="text-sm text-slate">{match.partner.course}</p>
        </div>
        <div className="text-right">
          <span className={`font-mono text-3xl ${scoreColor(match.score)}`}>{match.score}</span>
          <span className="text-slate text-sm">% match</span>
        </div>
      </div>

      {/* component breakdown */}
      <div className="mt-4 grid grid-cols-5 gap-2">
        {COMPONENTS.map((c) => (
          <div key={c.key}>
            <div className="h-16 bg-line rounded-md flex items-end overflow-hidden">
              <motion.div className="w-full bg-growth/70"
                initial={{ height: 0 }} animate={{ height: `${match.components[c.key] * 100}%` }}
                transition={{ duration: 0.5 }} />
            </div>
            <p className="text-[10px] text-slate text-center mt-1">{c.label}</p>
          </div>
        ))}
      </div>

      {(match.shared_subjects.length > 0 || match.shared_goal_tags.length > 0) && (
        <div className="flex flex-wrap gap-2 mt-4">
          {match.shared_subjects.map((s) => (
            <span key={`s-${s}`} className="rounded-full bg-growth/15 text-growth px-3 py-1 text-xs">{s}</span>
          ))}
          {match.shared_goal_tags.map((g) => (
            <span key={`g-${g}`} className="rounded-full bg-amber/15 text-amber px-3 py-1 text-xs">{g}</span>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between gap-4">
        <p className="text-sm text-slate flex-1">{match.reasons.join(" · ")}</p>
        <button onClick={explain}
          className="shrink-0 h-9 px-4 rounded-lg border border-growth text-growth text-sm font-medium hover:bg-growth/10">
          {loading ? "Thinking…" : "Why we match"}
        </button>
      </div>

      <AnimatePresence>
        {explanation && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            className="overflow-hidden">
            <div className="mt-4 rounded-xl bg-ink text-paper p-4">
              <div className="flex items-center gap-2 text-sprout text-[10px] font-mono uppercase tracking-wider">
                Why you match
                <span className="rounded-full bg-paper/10 px-2 py-0.5 text-paper/60">
                  {explanation.source === "ai" ? "AI" : "summary"}
                </span>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed">{explanation.explanation}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
