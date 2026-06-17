import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";
import { Field } from "./Login";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      await register(name, email, password);
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
            Plant the seed today.
          </h1>
          <p className="mt-4 text-paper/70 max-w-sm">
            Build a study routine that compounds. Your consistency grows a garden
            you can actually see.
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
          <h2 className="font-display text-2xl">Create your account</h2>
          <p className="text-slate text-sm mt-1">Start growing in under a minute.</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <Field label="Name" value={name} onChange={setName} autoFocus />
            <Field label="Email" type="email" value={email} onChange={setEmail} />
            <Field label="Password" type="password" value={password} onChange={setPassword} />

            {error && <p className="text-sm text-[#C0392B]">{error}</p>}

            <button
              type="submit"
              disabled={busy}
              className="w-full h-11 rounded-lg bg-growth text-white font-medium hover:bg-growth/90 transition-colors disabled:opacity-60"
            >
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>

          <p className="text-sm text-slate mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-growth font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
