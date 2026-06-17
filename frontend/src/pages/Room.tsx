import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import type { Socket } from "socket.io-client";
import { api } from "../lib/api";
import { createSocket } from "../lib/socket";
import { useAuth } from "../context/AuthContext";
import type { PresenceMember, PresenceStatus, RoomDetail } from "../lib/types";

const STATUS_META: Record<PresenceStatus, { label: string; dot: string; text: string }> = {
  online: { label: "Online", dot: "bg-growth", text: "text-growth" },
  focusing: { label: "Focusing", dot: "bg-amber", text: "text-amber" },
  break: { label: "On break", dot: "bg-slate", text: "text-slate" },
  offline: { label: "Offline", dot: "bg-line", text: "text-slate" },
};
const SETTABLE: PresenceStatus[] = ["online", "focusing", "break"];

export function Room() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [members, setMembers] = useState<PresenceMember[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    api.getRoom(id).then(setRoom).catch(() => {});

    const socket = createSocket();
    socketRef.current = socket;

    socket.on("connect", () => {
      setConnected(true);
      socket.emit("join_room", { room_id: id });
    });
    socket.on("disconnect", () => setConnected(false));
    socket.on("presence", (data: { room_id: string; members: PresenceMember[] }) => {
      if (data.room_id === id) setMembers(data.members);
    });

    return () => {
      socket.emit("leave_room", { room_id: id });
      socket.disconnect();
    };
  }, [id]);

  function setStatus(status: PresenceStatus) {
    socketRef.current?.emit("set_status", { room_id: id, status });
  }

  async function leave() {
    socketRef.current?.emit("leave_room", { room_id: id });
    socketRef.current?.disconnect();
    await api.leaveRoom(id).catch(() => {});
    navigate("/rooms");
  }

  const myStatus = members.find((m) => m.user_id === user?.id)?.status ?? "online";

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/rooms")} className="text-sm text-slate hover:text-ink">← All rooms</button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl">{room?.subject ?? "Room"}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-growth" : "bg-line"}`} />
            <span className="text-sm text-slate">{connected ? "Live" : "Connecting…"}</span>
          </div>
        </div>
        <button onClick={leave} className="h-10 px-4 rounded-lg border border-line text-slate hover:text-ink hover:border-ink text-sm">
          Leave room
        </button>
      </div>

      {/* my status */}
      <div className="rounded-2xl bg-surface border border-line shadow-card p-5">
        <p className="text-sm font-medium mb-3">Your status</p>
        <div className="flex gap-2">
          {SETTABLE.map((s) => (
            <button key={s} onClick={() => setStatus(s)}
              className={`h-10 px-4 rounded-lg text-sm capitalize transition-colors ${
                myStatus === s ? "bg-ink text-paper" : "border border-line hover:border-ink"
              }`}>
              {STATUS_META[s].label}
            </button>
          ))}
        </div>
      </div>

      {/* live presence */}
      <div className="space-y-3">
        <h2 className="font-display text-lg">
          In the room <span className="text-slate font-sans text-sm">({members.length})</span>
        </h2>

        {members.length === 0 && (
          <p className="text-slate text-sm">
            {connected
              ? "Waiting for members…"
              : "Not connected. Make sure the backend is running as " }
            {!connected && <code className="font-mono text-xs bg-line/60 px-1.5 py-0.5 rounded">uvicorn app.main:socket_app</code>}
          </p>
        )}

        <AnimatePresence>
          {members.map((m) => (
            <motion.div key={m.user_id} layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="flex items-center gap-3 rounded-xl bg-surface border border-line p-4">
              <span className="w-9 h-9 rounded-full bg-growth/15 text-growth grid place-items-center font-medium">
                {m.name.charAt(0).toUpperCase()}
              </span>
              <span className="flex-1 font-medium">
                {m.name}{m.user_id === user?.id && <span className="text-slate font-normal"> (you)</span>}
              </span>
              <span className={`flex items-center gap-1.5 text-sm ${STATUS_META[m.status].text}`}>
                <span className={`w-2 h-2 rounded-full ${STATUS_META[m.status].dot}`} />
                {STATUS_META[m.status].label}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>

        <p className="text-xs text-slate pt-2">
          Tip: open this room in a second browser (or an incognito window with another account) to watch presence update live.
        </p>
      </div>
    </div>
  );
}
