import { motion } from "framer-motion";
import type { GardenStage as Stage } from "../lib/types";

// The signature element: a small garden that visibly grows with the user's XP.
// Each stage adds to the previous one (soil -> sprout -> bud -> tree -> fruit).

const STAGES: Stage[] = ["Seed", "Sprout", "Flower", "Tree", "Fruit Tree"];

function stageIndex(stage: string): number {
  const i = STAGES.indexOf(stage as Stage);
  return i === -1 ? 0 : i;
}

const grow = {
  hidden: { scaleY: 0, opacity: 0 },
  show: { scaleY: 1, opacity: 1, transition: { duration: 0.6, ease: "easeOut" } },
};

export function GardenStage({ stage, size = 160 }: { stage: string; size?: number }) {
  const idx = stageIndex(stage);
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label={`Garden stage: ${stage}`}
    >
      {/* pot */}
      <path d="M38 96 L82 96 L78 116 L42 116 Z" fill="#C8794A" />
      <rect x="34" y="90" width="52" height="9" rx="2" fill="#D98A5B" />
      {/* soil */}
      <ellipse cx="60" cy="92" rx="22" ry="4" fill="#3B2A22" />

      {/* stem (Sprout+) */}
      {idx >= 1 && (
        <motion.rect
          x="58" y="58" width="4" height="34" rx="2" fill="#2E9E6B"
          variants={grow} initial="hidden" animate="show" style={{ originY: 1 }}
        />
      )}
      {/* leaves (Sprout+) */}
      {idx >= 1 && (
        <motion.g variants={grow} initial="hidden" animate="show" style={{ originY: 1 }}>
          <path d="M60 74 C48 70 44 60 46 54 C56 56 60 66 60 74 Z" fill="#8FD0A8" />
          <path d="M60 70 C72 66 76 56 74 50 C64 52 60 62 60 70 Z" fill="#2E9E6B" />
        </motion.g>
      )}
      {/* flower bud (Flower+) */}
      {idx >= 2 && (
        <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.3, duration: 0.5 }}>
          <circle cx="60" cy="50" r="7" fill="#DE9B36" />
          <circle cx="60" cy="50" r="3" fill="#fff" />
        </motion.g>
      )}
      {/* tree canopy (Tree+) */}
      {idx >= 3 && (
        <motion.g initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2, duration: 0.5 }} style={{ originX: 0.5, originY: 0.6 }}>
          <circle cx="60" cy="40" r="22" fill="#2E9E6B" />
          <circle cx="44" cy="48" r="14" fill="#3BAA77" />
          <circle cx="76" cy="48" r="14" fill="#3BAA77" />
        </motion.g>
      )}
      {/* fruit (Fruit Tree) */}
      {idx >= 4 && (
        <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
          <circle cx="50" cy="44" r="4" fill="#DE5B4B" />
          <circle cx="70" cy="38" r="4" fill="#DE5B4B" />
          <circle cx="62" cy="52" r="4" fill="#DE5B4B" />
        </motion.g>
      )}
    </svg>
  );
}
