import { motion } from "framer-motion";
import type { AIProfile } from "../lib/types";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
};

export function PersonalityCard({ profile }: { profile: AIProfile }) {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="rounded-2xl bg-ink text-paper p-7 shadow-card"
    >
      <motion.div variants={item} className="flex items-center gap-2 text-sprout text-xs font-mono uppercase tracking-wider">
        Your learning personality
        <span className="rounded-full bg-paper/10 px-2 py-0.5 text-paper/60">
          {profile.source === "ai" ? "AI" : "rule-based"}
        </span>
      </motion.div>

      <motion.h3 variants={item} className="font-display text-3xl mt-2">
        {profile.personality_type}
      </motion.h3>

      <motion.div variants={item} className="grid sm:grid-cols-2 gap-5 mt-6">
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-sprout/80">Strengths</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {profile.strengths.length === 0 && <span className="text-paper/50 text-sm">—</span>}
            {profile.strengths.map((s) => (
              <span key={s} className="rounded-full bg-growth/25 text-sprout px-3 py-1 text-sm">{s}</span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-amber/80">Watch-outs</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {profile.weaknesses.length === 0 && <span className="text-paper/50 text-sm">—</span>}
            {profile.weaknesses.map((w) => (
              <span key={w} className="rounded-full bg-amber/20 text-amber px-3 py-1 text-sm">{w}</span>
            ))}
          </div>
        </div>
      </motion.div>

      {profile.recommended_partner_type && (
        <motion.p variants={item} className="mt-6 text-paper/80">
          <span className="text-paper/50">Best study partner: </span>
          {profile.recommended_partner_type}
        </motion.p>
      )}

      {profile.recommendations.length > 0 && (
        <motion.ul variants={item} className="mt-4 space-y-2">
          {profile.recommendations.map((r) => (
            <li key={r} className="flex gap-2 text-sm text-paper/80">
              <span className="text-sprout">→</span>
              <span>{r}</span>
            </li>
          ))}
        </motion.ul>
      )}
    </motion.div>
  );
}
