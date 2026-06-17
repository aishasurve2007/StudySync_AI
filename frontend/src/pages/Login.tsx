import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between bg-ink text-paper p-12">
        <span className="font-display text-2xl text-sprout">StudySync</span>
        <div>
          <h1 className="font-display text-4xl leading-tight">
            Study with intent.<br />Watch it grow.
          </h1>
          <p className="mt-4 text-paper/70 max-w-sm">
            Track focus, find compatible study partners, and grow a garden that
            reflects your consistency.
          </p>
        </div>
        <span className="font-mono text-xs text-paper/40">v0.1</span>
      </div>

      <div className="flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-sm"
        >
          <h2 className="font-display text-2xl">Welcome back</h2>
          <p className="text-slate text-sm mt-1">Sign in to your garden.</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <Field label="Email" type="email" value={email} onChange={setEmail} autoFocus />
            <Field label="Password" type="password" value={password} onChange={setPassword} />

            {error && <p className="text-sm text-[#C0392B]">{error}</p>}

            <button
              type="submit"
              disabled={busy}
              className="w-full h-11 rounded-lg bg-growth text-white font-medium hover:bg-growth/90 transition-colors disabled:opacity-60"
            >
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-sm text-slate mt-6">
            New here?{" "}
            <Link to="/register" className="text-growth font-medium hover:underline">
              Create an account
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export function Field({
  label, type = "text", value, onChange, autoFocus,
}: {
  label: string; type?: string; value: string; onChange: (v: string) => void; autoFocus?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">{label}</span>
      <input
        type={type}
        value={value}
        autoFocus={autoFocus}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full h-11 rounded-lg border border-line bg-surface px-3 text-ink placeholder:text-slate/50 focus:border-growth"
        required
      />
    </label>
  );
}
