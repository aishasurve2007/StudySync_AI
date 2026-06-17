import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { api, ApiError } from "../lib/api";
import type { AIProfile, ProfileInput } from "../lib/types";
import { Field } from "./Login";
import { PersonalityCard } from "../components/PersonalityCard";

const LEARNING_STYLES = ["reading", "video", "practice", "notes", "group"];
const STUDY_TIMES = ["morning", "afternoon", "evening", "night"];
const ENVIRONMENTS = ["quiet", "discussion", "accountability"];
const INTENSITIES = ["casual", "regular", "intensive"];
const MOTIVATIONS = ["achievement", "social", "deadline", "growth"];
const EXPERIENCE = ["beginner", "intermediate", "advanced"];

const EMPTY: ProfileInput = {
  course: "",
  year: null,
  subjects: [],
  learning_style: "practice",
  preferred_study_time: "evening",
  study_environment: "quiet",
  study_intensity: "regular",
  current_goal: "",
  daily_goal_hours: 2,
  motivation_type: "achievement",
  experience_level: "intermediate",
};

export function Profile() {
  const [form, setForm] = useState<ProfileInput>(EMPTY);
  const [isEditing, setIsEditing] = useState(false);
  const [subjectDraft, setSubjectDraft] = useState("");
  const [personality, setPersonality] = useState<AIProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const revealRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setForm({
          course: p.course, year: p.year, subjects: p.subjects,
          learning_style: p.learning_style, preferred_study_time: p.preferred_study_time,
          study_environment: p.study_environment, study_intensity: p.study_intensity,
          current_goal: p.current_goal ?? "", daily_goal_hours: p.daily_goal_hours,
          motivation_type: p.motivation_type, experience_level: p.experience_level,
        });
        setIsEditing(true);
        return api.getPersonality().then(setPersonality).catch(() => {});
      })
      .catch(() => setIsEditing(false))
      .finally(() => setLoaded(true));
  }, []);

  function set<K extends keyof ProfileInput>(key: K, value: ProfileInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function addSubject(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const v = subjectDraft.trim();
      if (v && !form.subjects.includes(v)) set("subjects", [...form.subjects, v]);
      setSubjectDraft("");
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.subjects.length === 0) {
      setError("Add at least one subject.");
      return;
    }
    setBusy(true);
    try {
      const payload: ProfileInput = { ...form, current_goal: form.current_goal || null };
      if (isEditing) await api.updateProfile(payload);
      else await api.createProfile(payload);
      setIsEditing(true);
      const p = await api.generatePersonality();
      setPersonality(p);
      setTimeout(() => revealRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your profile.");
    } finally {
      setBusy(false);
    }
  }

  if (!loaded) return <p className="font-mono text-sm text-slate">Loading…</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">Your study profile</h1>
        <p className="text-slate text-sm mt-1">
          This is how you study — it powers your personality and partner matches.
        </p>
      </div>

      <form onSubmit={onSubmit} className="rounded-2xl bg-surface border border-line shadow-card p-6 space-y-5">
        <div className="grid sm:grid-cols-2 gap-5">
          <Field label="Course" value={form.course} onChange={(v) => set("course", v)} />
          <label className="block">
            <span className="text-sm font-medium text-ink">Year of study</span>
            <input
              type="number" min={1} max={12} value={form.year ?? ""}
              onChange={(e) => set("year", e.target.value ? Number(e.target.value) : null)}
              className="mt-1 w-full h-11 rounded-lg border border-line bg-surface px-3 focus:border-growth"
            />
          </label>
        </div>

        {/* subjects chip input */}
        <div>
          <span className="text-sm font-medium text-ink">Subjects</span>
          <div className="mt-1 flex flex-wrap gap-2 rounded-lg border border-line bg-surface p-2 min-h-[44px]">
            {form.subjects.map((s) => (
              <span key={s} className="inline-flex items-center gap-1 rounded-full bg-growth/15 text-growth px-3 py-1 text-sm">
                {s}
                <button type="button" onClick={() => set("subjects", form.subjects.filter((x) => x !== s))} className="text-growth/70 hover:text-growth">×</button>
              </span>
            ))}
            <input
              value={subjectDraft}
              onChange={(e) => setSubjectDraft(e.target.value)}
              onKeyDown={addSubject}
              placeholder={form.subjects.length ? "" : "Type a subject, press Enter"}
              className="flex-1 min-w-[140px] bg-transparent outline-none text-sm px-1"
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-5">
          <Select label="Learning style" value={form.learning_style} options={LEARNING_STYLES} onChange={(v) => set("learning_style", v)} />
          <Select label="Preferred study time" value={form.preferred_study_time} options={STUDY_TIMES} onChange={(v) => set("preferred_study_time", v)} />
          <Select label="Study environment" value={form.study_environment} options={ENVIRONMENTS} onChange={(v) => set("study_environment", v)} />
          <Select label="Study intensity" value={form.study_intensity} options={INTENSITIES} onChange={(v) => set("study_intensity", v)} />
          <Select label="Motivation" value={form.motivation_type ?? ""} options={MOTIVATIONS} onChange={(v) => set("motivation_type", v)} />
          <Select label="Experience level" value={form.experience_level ?? ""} options={EXPERIENCE} onChange={(v) => set("experience_level", v)} />
        </div>

        <div className="grid sm:grid-cols-2 gap-5">
          <Field label="Current goal" value={form.current_goal ?? ""} onChange={(v) => set("current_goal", v)} />
          <label className="block">
            <span className="text-sm font-medium text-ink">Daily goal (hours)</span>
            <input
              type="number" min={0.5} max={24} step={0.5} value={form.daily_goal_hours}
              onChange={(e) => set("daily_goal_hours", Number(e.target.value))}
              className="mt-1 w-full h-11 rounded-lg border border-line bg-surface px-3 focus:border-growth"
            />
          </label>
        </div>

        {error && <p className="text-sm text-[#C0392B]">{error}</p>}

        <button
          type="submit" disabled={busy}
          className="h-11 px-6 rounded-lg bg-growth text-white font-medium hover:bg-growth/90 transition-colors disabled:opacity-60"
        >
          {busy ? "Saving & analyzing…" : isEditing ? "Update & regenerate personality" : "Save & reveal my personality"}
        </button>
      </form>

      <div ref={revealRef}>
        {personality && <PersonalityCard profile={personality} />}
      </div>
    </div>
  );
}

function Select({
  label, value, options, onChange,
}: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full h-11 rounded-lg border border-line bg-surface px-3 capitalize focus:border-growth"
      >
        {options.map((o) => (
          <option key={o} value={o} className="capitalize">{o}</option>
        ))}
      </select>
    </label>
  );
}
