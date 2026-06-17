import { io, type Socket } from "socket.io-client";
import { getToken } from "./api";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// One socket per room view. The JWT is passed in `auth` and validated by the
// server's connect handler; a bad/absent token rejects the connection.
export function createSocket(): Socket {
  return io(BASE_URL, {
    auth: { token: getToken() },
    transports: ["websocket", "polling"],
    autoConnect: true,
  });
}
