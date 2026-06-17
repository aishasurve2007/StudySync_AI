import { useEffect, useState, type FormEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, ApiError } from "../lib/api";
import type { Task } from "../lib/types";

const PRIORITY_STYLE: Record<string, string> = {
  high: "bg-[#DE5B4B]/15 text-[#C0392B]",
  medium: "bg-amber/15 text-amber",
  low: "bg-slate/15 text-slate",
};

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goal, setGoal] = useState("");
  const [deadline, setDeadline] = useState(14);
  const [quickTitle, setQuickTitle] = useState("");
  const [planSource, setPlanSource] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => api.listTasks().then(setTasks).catch(() => {});
  useEffect(() => { refresh(); }, []);

  async function generatePlan(e: FormEvent) {
    e.preventDefault();
    if (!goal.trim()) return;
    setBusy(true); setError(null);
    try {
      const res = await api.planTasks({ goal: goal.trim(), deadline_days: deadline });
      setPlanSource(res.source);
      setGoal("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate a plan.");
    } finally {
      setBusy(false);
    }
  }

  async function quickAdd(e: FormEvent) {
    e.preventDefault();
    if (!quickTitle.trim()) return;
    await api.createTask({ title: quickTitle.trim() });
    setQuickTitle("");
    refresh();
  }

  async function complete(id: string) {
    await api.completeTask(id);
    refresh();
  }

  const pending = tasks.filter((t) => t.status !== "completed");
  const done = tasks.filter((t) => t.status === "completed");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">Tasks</h1>
        <p className="text-slate text-sm mt-1">Plan with AI, or add your own. Completing tasks grows your garden.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {/* AI planner */}
        <form onSubmit={generatePlan} className="rounded-2xl bg-surface border border-line shadow-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="font-display text-lg">AI study plan</h2>
            {planSource && (
              <span className="rounded-full bg-growth/15 text-growth px-2 py-0.5 text-xs font-mono">
                {planSource === "ai" ? "AI generated" : "rule-based"}
              </span>
            )}
          </div>
          <label className="block">
            <span className="text-sm font-medium">Goal</span>
            <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="e.g. Prepare ML interview"
              className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth" />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Deadline (days)</span>
            <input type="number" min={1} max={365} value={deadline} onChange={(e) => setDeadline(Number(e.target.value))}
              className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth" />
          </label>
          {error && <p className="text-sm text-[#C0392B]">{error}</p>}
          <button disabled={busy} className="h-11 px-5 rounded-lg bg-growth text-white font-medium hover:bg-growth/90 disabled:opacity-60">
            {busy ? "Planning…" : "Generate plan"}
          </button>
        </form>

        {/* quick add */}
        <form onSubmit={quickAdd} className="rounded-2xl bg-surface border border-line shadow-card p-6 space-y-4">
          <h2 className="font-display text-lg">Quick add</h2>
          <label className="block">
            <span className="text-sm font-medium">Task</span>
            <input value={quickTitle} onChange={(e) => setQuickTitle(e.target.value)} placeholder="e.g. Read chapter 3"
              className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth" />
          </label>
          <button className="h-11 px-5 rounded-lg border border-growth text-growth font-medium hover:bg-growth/10">
            Add task
          </button>
        </form>
      </div>

      {/* lists */}
      <div className="space-y-3">
        <h2 className="font-display text-lg">To do <span className="text-slate font-sans text-sm">({pending.length})</span></h2>
        {pending.length === 0 && <p className="text-slate text-sm">Nothing pending — plan something above.</p>}
        <AnimatePresence>
          {pending.map((t) => (
            <motion.div key={t.id} layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -20 }}
              className="flex items-center gap-3 rounded-xl bg-surface border border-line p-4">
              <button onClick={() => complete(t.id)} aria-label="Complete task"
                className="w-6 h-6 rounded-full border-2 border-line hover:border-growth transition-colors shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="truncate">{t.title}</p>
                <p className="text-xs text-slate font-mono">{t.estimated_time} min</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs capitalize ${PRIORITY_STYLE[t.priority]}`}>{t.priority}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {done.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-display text-lg text-slate">Done <span className="font-sans text-sm">({done.length})</span></h2>
          {done.map((t) => (
            <div key={t.id} className="flex items-center gap-3 rounded-xl bg-surface/60 border border-line p-4 opacity-70">
              <span className="w-6 h-6 rounded-full bg-growth grid place-items-center text-white text-sm shrink-0">✓</span>
              <p className="flex-1 line-through text-slate truncate">{t.title}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
