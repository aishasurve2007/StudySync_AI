import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import type { FocusSession, Task } from "../lib/types";

const MODES = [
  { id: "pomodoro", label: "Pomodoro", default: 25 },
  { id: "deep_work", label: "Deep work", default: 50 },
  { id: "stopwatch", label: "Stopwatch", default: 0 },
];

const R = 70;
const CIRC = 2 * Math.PI * R;

function mmss(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function Focus() {
  const [mode, setMode] = useState("pomodoro");
  const [duration, setDuration] = useState(25); // planned minutes
  const [taskId, setTaskId] = useState<string>("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [sessions, setSessions] = useState<FocusSession[]>([]);

  const [session, setSession] = useState<FocusSession | null>(null);
  const [elapsed, setElapsed] = useState(0); // seconds
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<FocusSession | null>(null);
  const intervalRef = useRef<number | null>(null);

  const isTimed = mode !== "stopwatch";
  const total = duration * 60;

  const refresh = useCallback(() => {
    api.listTasks().then((t) => setTasks(t.filter((x) => x.status !== "completed"))).catch(() => {});
    api.listSessions().then((s) => setSessions(s.slice(0, 6))).catch(() => {});
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  function pickMode(id: string, def: number) {
    setMode(id);
    setDuration(def || 25);
  }

  const finish = useCallback(async () => {
    if (!session) return;
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    setRunning(false);
    const minutes = isTimed ? Math.min(Math.round(elapsed / 60), duration) : Math.round(elapsed / 60);
    const done = await api.completeFocus(session.id, minutes);
    setResult(done);
    setSession(null);
    setElapsed(0);
    refresh();
  }, [session, isTimed, elapsed, duration, refresh]);

  // tick
  useEffect(() => {
    if (!running) return;
    intervalRef.current = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => { if (intervalRef.current) window.clearInterval(intervalRef.current); };
  }, [running]);

  // auto-finish timed sessions at zero
  useEffect(() => {
    if (running && isTimed && elapsed >= total) finish();
  }, [running, isTimed, elapsed, total, finish]);

  async function start() {
    setResult(null);
    const s = await api.startFocus({ mode, duration: isTimed ? duration : 0, task_id: taskId || null });
    setSession(s);
    setElapsed(0);
    setRunning(true);
  }

  const remaining = isTimed ? Math.max(total - elapsed, 0) : elapsed;
  const progress = isTimed ? Math.min(elapsed / total, 1) : (elapsed % 60) / 60;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">Focus</h1>
        <p className="text-slate text-sm mt-1">Run a session. Finish it fully and it counts toward your score and garden.</p>
      </div>

      <div className="rounded-2xl bg-surface border border-line shadow-card p-8 flex flex-col items-center">
        {/* timer ring */}
        <div className="relative" style={{ width: 180, height: 180 }}>
          <svg width="180" height="180" className="-rotate-90">
            <circle cx="90" cy="90" r={R} fill="none" stroke="#E5E8E0" strokeWidth="10" />
            <motion.circle
              cx="90" cy="90" r={R} fill="none" stroke="#2E9E6B" strokeWidth="10" strokeLinecap="round"
              strokeDasharray={CIRC}
              animate={{ strokeDashoffset: CIRC * (1 - progress) }}
              transition={{ duration: 0.4, ease: "linear" }}
            />
          </svg>
          <div className="absolute inset-0 grid place-items-center">
            <div className="text-center">
              <div className="font-mono text-4xl">{mmss(remaining)}</div>
              <div className="text-xs text-slate capitalize">{mode.replace("_", " ")}</div>
            </div>
          </div>
        </div>

        {!session ? (
          <div className="w-full max-w-sm mt-6 space-y-4">
            <div className="grid grid-cols-3 gap-2">
              {MODES.map((m) => (
                <button key={m.id} onClick={() => pickMode(m.id, m.default)}
                  className={`h-10 rounded-lg text-sm transition-colors ${mode === m.id ? "bg-ink text-paper" : "border border-line hover:border-ink"}`}>
                  {m.label}
                </button>
              ))}
            </div>
            {isTimed && (
              <label className="block">
                <span className="text-sm font-medium">Minutes</span>
                <input type="number" min={1} max={180} value={duration} onChange={(e) => setDuration(Number(e.target.value))}
                  className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth" />
              </label>
            )}
            <label className="block">
              <span className="text-sm font-medium">Link a task (optional)</span>
              <select value={taskId} onChange={(e) => setTaskId(e.target.value)}
                className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth">
                <option value="">None</option>
                {tasks.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
              </select>
            </label>
            <button onClick={start} className="w-full h-11 rounded-lg bg-growth text-white font-medium hover:bg-growth/90">
              Start session
            </button>
          </div>
        ) : (
          <div className="flex gap-3 mt-6">
            <button onClick={() => setRunning((r) => !r)}
              className="h-11 px-6 rounded-lg border border-line hover:border-ink">
              {running ? "Pause" : "Resume"}
            </button>
            <button onClick={finish} className="h-11 px-6 rounded-lg bg-ink text-paper hover:bg-ink/90">
              Finish session
            </button>
          </div>
        )}

        {result && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className={`mt-5 text-sm ${result.completed ? "text-growth" : "text-amber"}`}>
            {result.completed
              ? `Session complete — ${result.actual_minutes} min credited. +20 XP 🌱`
              : `Ended early (${result.actual_minutes} min) — not counted toward your score.`}
          </motion.p>
        )}
      </div>

      {/* recent sessions */}
      {sessions.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-display text-lg">Recent sessions</h2>
          {sessions.map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded-xl bg-surface border border-line p-4 text-sm">
              <span className="capitalize">{s.mode.replace("_", " ")}</span>
              <span className="font-mono text-slate">{s.actual_minutes} min</span>
              <span className={s.completed ? "text-growth" : "text-slate"}>{s.completed ? "completed" : "partial"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
