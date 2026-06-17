import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Match } from "../lib/types";
import { MatchCard } from "../components/MatchCard";

type State =
  | { kind: "loading" }
  | { kind: "no_profile" }
  | { kind: "ready"; matches: Match[] }
  | { kind: "error"; message: string };

export function Matching() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    api
      .listMatches()
      .then((matches) => setState({ kind: "ready", matches }))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setState({ kind: "no_profile" });
        else setState({ kind: "error", message: "Couldn't load matches." });
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">Study partners</h1>
        <p className="text-slate text-sm mt-1">
          Ranked by a transparent compatibility score — schedule, subjects, style, goals, and intensity.
        </p>
      </div>

      {state.kind === "loading" && <p className="font-mono text-sm text-slate">Finding compatible partners…</p>}

      {state.kind === "no_profile" && (
        <Link to="/profile" className="block rounded-xl border border-amber/40 bg-amber/10 px-5 py-4 text-sm hover:bg-amber/20 transition-colors">
          <span className="font-medium">Set up your study profile →</span> matching needs your subjects, schedule, and goals.
        </Link>
      )}

      {state.kind === "error" && <p className="text-slate">{state.message} Is the API running?</p>}

      {state.kind === "ready" && state.matches.length === 0 && (
        <div className="rounded-2xl bg-surface border border-line p-8 text-center">
          <p className="font-display text-lg">No compatible partners yet</p>
          <p className="text-slate text-sm mt-1">
            Matches appear once other students with overlapping courses or subjects join. Check back soon.
          </p>
        </div>
      )}

      {state.kind === "ready" &&
        state.matches.map((m) => <MatchCard key={m.partner.user_id} match={m} />)}
    </div>
  );
}
