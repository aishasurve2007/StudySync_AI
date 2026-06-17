import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api, ApiError } from "../lib/api";
import type { RoomSummary } from "../lib/types";

export function Rooms() {
  const [rooms, setRooms] = useState<RoomSummary[]>([]);
  const [subject, setSubject] = useState("");
  const [maxUsers, setMaxUsers] = useState(8);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const refresh = () => api.listRooms().then(setRooms).catch(() => {});
  useEffect(() => { refresh(); }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!subject.trim()) return;
    try {
      const room = await api.createRoom({ subject: subject.trim(), max_users: maxUsers });
      navigate(`/rooms/${room.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create the room.");
    }
  }

  async function join(id: string) {
    try {
      await api.joinRoom(id);
      navigate(`/rooms/${id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't join the room.");
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">Study rooms</h1>
        <p className="text-slate text-sm mt-1">Study alongside others in real time. Presence updates live.</p>
      </div>

      <form onSubmit={create} className="rounded-2xl bg-surface border border-line shadow-card p-6">
        <h2 className="font-display text-lg">Start a room</h2>
        <div className="grid sm:grid-cols-[1fr_auto_auto] gap-3 mt-4 items-end">
          <label className="block">
            <span className="text-sm font-medium">Subject</span>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Machine Learning"
              className="mt-1 w-full h-11 rounded-lg border border-line px-3 focus:border-growth" />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Max</span>
            <input type="number" min={2} max={50} value={maxUsers} onChange={(e) => setMaxUsers(Number(e.target.value))}
              className="mt-1 w-20 h-11 rounded-lg border border-line px-3 focus:border-growth" />
          </label>
          <button className="h-11 px-5 rounded-lg bg-growth text-white font-medium hover:bg-growth/90">Create</button>
        </div>
        {error && <p className="text-sm text-[#C0392B] mt-3">{error}</p>}
      </form>

      <div className="space-y-3">
        <h2 className="font-display text-lg">Active rooms <span className="text-slate font-sans text-sm">({rooms.length})</span></h2>
        {rooms.length === 0 && <p className="text-slate text-sm">No active rooms — start one above.</p>}
        {rooms.map((r) => (
          <motion.div key={r.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between rounded-xl bg-surface border border-line p-4">
            <div>
              <p className="font-medium">{r.subject}</p>
              <p className="text-xs text-slate font-mono">{r.member_count}/{r.max_users} members</p>
            </div>
            <button onClick={() => join(r.id)}
              disabled={r.member_count >= r.max_users}
              className="h-9 px-4 rounded-lg border border-growth text-growth text-sm font-medium hover:bg-growth/10 disabled:opacity-40 disabled:border-line disabled:text-slate">
              {r.member_count >= r.max_users ? "Full" : "Join"}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
