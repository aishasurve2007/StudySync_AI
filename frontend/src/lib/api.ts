// Typed API client. One fetch wrapper attaches the JWT and parses errors;
// endpoint helpers below give callers a typed surface.
import type {
  AIProfile,
  AuthResponse,
  CoachInsight,
  DashboardSummary,
  FocusSession,
  Match,
  MatchExplanation,
  Profile,
  ProfileInput,
  RoomDetail,
  RoomSummary,
  Task,
  TaskPlanResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "studysync_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 204) return undefined as T;

  let body: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!res.ok) {
    const detail =
      (body as { detail?: string })?.detail ?? `Request failed (${res.status})`;
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Request failed");
  }
  return body as T;
}

export const api = {
  // --- auth ---
  register: (data: { email: string; password: string; name: string; timezone: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => request<AuthResponse["user"]>("/auth/me"),

  // --- dashboard / coach ---
  dashboard: () => request<DashboardSummary>("/dashboard"),
  coachInsight: () => request<CoachInsight>("/coach/insight"),

  // --- profile ---
  getProfile: () => request<Profile>("/profiles/me"),
  createProfile: (data: ProfileInput) =>
    request<Profile>("/profiles", { method: "POST", body: JSON.stringify(data) }),
  updateProfile: (data: ProfileInput) =>
    request<Profile>("/profiles", { method: "PUT", body: JSON.stringify(data) }),

  // --- AI personality ---
  generatePersonality: () => request<AIProfile>("/ai/personality", { method: "POST" }),
  getPersonality: () => request<AIProfile>("/ai/personality"),

  // --- tasks ---
  planTasks: (data: { goal: string; deadline_days: number }) =>
    request<TaskPlanResponse>("/tasks/plan", { method: "POST", body: JSON.stringify(data) }),
  createTask: (data: { title: string; priority?: string; estimated_time?: number }) =>
    request<Task>("/tasks", { method: "POST", body: JSON.stringify(data) }),
  listTasks: () => request<Task[]>("/tasks"),
  completeTask: (id: string) => request<Task>(`/tasks/${id}/complete`, { method: "POST" }),

  // --- focus ---
  startFocus: (data: { mode: string; duration: number; task_id?: string | null }) =>
    request<FocusSession>("/focus/start", { method: "POST", body: JSON.stringify(data) }),
  completeFocus: (id: string, actual_minutes: number) =>
    request<FocusSession>(`/focus/${id}/complete`, { method: "POST", body: JSON.stringify({ actual_minutes }) }),
  listSessions: () => request<FocusSession[]>("/focus/sessions"),

  // --- matching ---
  listMatches: (limit = 10) => request<Match[]>(`/matches?limit=${limit}`),
  matchExplanation: (partnerId: string) =>
    request<MatchExplanation>(`/matches/${partnerId}/explanation`),

  // --- rooms ---
  listRooms: () => request<RoomSummary[]>("/rooms"),
  createRoom: (data: { subject: string; max_users: number }) =>
    request<RoomDetail>("/rooms", { method: "POST", body: JSON.stringify(data) }),
  getRoom: (id: string) => request<RoomDetail>(`/rooms/${id}`),
  joinRoom: (id: string) => request<RoomDetail>(`/rooms/${id}/join`, { method: "POST" }),
  leaveRoom: (id: string) => request<{ left: boolean }>(`/rooms/${id}/leave`, { method: "POST" }),
};
