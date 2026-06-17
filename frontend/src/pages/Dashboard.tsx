import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import type { CoachInsight, DashboardSummary } from "../lib/types";
import { GardenStage } from "../components/GardenStage";

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [coach, setCoach] = useState<CoachInsight | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setError("Couldn't load your dashboard."));
    api.coachInsight().then(setCoach).catch(() => { /* coach is optional */ });
  }, []);

  if (error) {
    return <p className="text-slate">{error} Is the API running?</p>;
  }
  if (!data) {
    return <p className="font-mono text-sm text-slate">Loading your garden…</p>;
  }

  const { rewards, productivity, weekly } = data;
  const progress =
    rewards.xp_to_next != null && rewards.next_stage
      ? rewards.xp / (rewards.xp + rewards.xp_to_next)
      : 1;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-slate text-sm">Welcome back,</p>
        <h1 className="font-display text-3xl">{data.name}</h1>
      </div>

      {!data.has_profile && (
        <Link
          to="/profile"
          className="block rounded-xl border border-amber/40 bg-amber/10 px-5 py-4 text-sm hover:bg-amber/20 transition-colors"
        >
          <span className="font-medium">Set up your study profile →</span> unlock
          partner matching and a personalized AI plan.
        </Link>
      )}

      <div className="grid md:grid-cols-3 gap-5">
        {/* Garden — the signature card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:col-span-1 rounded-2xl bg-surface border border-line shadow-card p-6 flex flex-col items-center"
        >
          <GardenStage stage={rewards.garden_stage} />
          <p className="font-display text-xl mt-2">{rewards.garden_stage}</p>
          <p className="font-mono text-sm text-slate">{rewards.xp} XP · Level {rewards.level}</p>
          <div className="w-full mt-4">
            <div className="h-2 rounded-full bg-line overflow-hidden">
              <motion.div
                className="h-full bg-growth"
                initial={{ width: 0 }}
                animate={{ width: `${Math.round(progress * 100)}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
            <p className="text-xs text-slate mt-2">
              {rewards.next_stage
                ? `${rewards.xp_to_next} XP to ${rewards.next_stage}`
                : "Fully grown — nice work!"}
            </p>
          </div>
        </motion.div>

        {/* Productivity + weekly stats */}
        <div className="md:col-span-2 grid sm:grid-cols-2 gap-5">
          <Stat label="Productivity" value={`${productivity.score}`} suffix="/100"
                hint="rolling 7-day score" big />
          <Stat label="Current streak" value={`${weekly.current_streak}`}
                suffix={weekly.current_streak === 1 ? " day" : " days"} hint="consecutive active days" big />
          <Stat label="Focus this week" value={`${weekly.study_minutes}`} suffix=" min"
                hint={`${weekly.focus_sessions} sessions`} />
          <Stat label="Consistency" value={`${weekly.consistency_pct}`} suffix="%"
                hint={`${weekly.active_days}/7 active days`} />
        </div>
      </div>

      {/* Coach insight */}
      {coach && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-2xl bg-ink text-paper p-6 shadow-card"
        >
          <div className="flex items-center gap-2 text-sprout text-xs font-mono uppercase tracking-wider">
            Study coach
            <span className="rounded-full bg-paper/10 px-2 py-0.5 text-paper/60">
              {coach.source === "ai" ? "AI" : "tip"}
            </span>
          </div>
          <p className="font-display text-lg mt-2 leading-snug">{coach.insight}</p>
        </motion.div>
      )}
    </div>
  );
}

function Stat({
  label, value, suffix, hint, big,
}: {
  label: string; value: string; suffix?: string; hint?: string; big?: boolean;
}) {
  return (
    <div className="rounded-2xl bg-surface border border-line shadow-card p-5">
      <p className="text-sm text-slate">{label}</p>
      <p className={`font-mono ${big ? "text-4xl" : "text-2xl"} text-ink mt-1`}>
        {value}
        <span className="text-slate text-base">{suffix}</span>
      </p>
      {hint && <p className="text-xs text-slate mt-1">{hint}</p>}
    </div>
  );
}
