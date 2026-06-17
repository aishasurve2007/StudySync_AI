// Types mirroring the FastAPI response schemas.

export interface User {
  id: string;
  email: string;
  name: string;
  avatar: string | null;
  timezone: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ProductivityScore {
  score: number;
  task_completion: number;
  focus_ratio: number;
  consistency: number;
  active_days: number;
  window_days: number;
  total_focus_minutes: number;
  completed_tasks: number;
  created_tasks: number;
}

export interface Rewards {
  user_id: string;
  xp: number;
  level: number;
  garden_stage: string;
  next_stage: string | null;
  xp_to_next: number | null;
  updated_at: string;
}

export interface WeeklyReport {
  study_minutes: number;
  tasks_completed: number;
  focus_sessions: number;
  current_streak: number;
  active_days: number;
  consistency: number;
  consistency_pct: number;
  window_days: number;
}

export interface DashboardSummary {
  name: string;
  has_profile: boolean;
  personality_type: string | null;
  productivity: ProductivityScore;
  rewards: Rewards;
  weekly: WeeklyReport;
}

export interface CoachInsight {
  insight: string;
  source: "ai" | "fallback";
  context: Record<string, number | string | null>;
}

export type GardenStage = "Seed" | "Sprout" | "Flower" | "Tree" | "Fruit Tree";

export interface ProfileInput {
  course: string;
  year: number | null;
  subjects: string[];
  learning_style: string;
  preferred_study_time: string;
  study_environment: string;
  study_intensity: string;
  current_goal: string | null;
  daily_goal_hours: number;
  motivation_type: string | null;
  experience_level: string | null;
}

export interface Profile extends ProfileInput {
  id: string;
  user_id: string;
  goal_tags: string[];
  created_at: string;
  updated_at: string;
}

export interface AIProfile {
  id: string;
  user_id: string;
  personality_type: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  recommended_partner_type: string;
  source: "ai" | "fallback";
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  priority: "low" | "medium" | "high";
  estimated_time: number;
  deadline: string | null;
  status: "pending" | "in_progress" | "completed";
  created_at: string;
  completed_at: string | null;
}

export interface TaskPlanResponse {
  source: "ai" | "fallback";
  tasks: Task[];
}

export interface FocusSession {
  id: string;
  user_id: string;
  task_id: string | null;
  mode: "pomodoro" | "deep_work" | "stopwatch";
  duration: number;
  actual_minutes: number;
  started_at: string;
  ended_at: string | null;
  completed: boolean;
}

export interface MatchComponents {
  schedule_match: number;
  subject_match: number;
  learning_style: number;
  goal_similarity: number;
  study_intensity: number;
}

export interface Match {
  partner: { user_id: string; name: string; avatar: string | null; course: string };
  score: number;
  components: MatchComponents;
  reasons: string[];
  shared_subjects: string[];
  shared_goal_tags: string[];
}

export interface MatchExplanation {
  partner_id: string;
  score: number;
  explanation: string;
  source: "ai" | "fallback";
}

export interface RoomMember {
  user_id: string;
  name: string;
  joined_at: string;
}

export interface RoomSummary {
  id: string;
  subject: string;
  max_users: number;
  status: string;
  created_by: string;
  created_at: string;
  member_count: number;
}

export interface RoomDetail extends RoomSummary {
  members: RoomMember[];
}

export type PresenceStatus = "online" | "focusing" | "break" | "offline";

export interface PresenceMember {
  user_id: string;
  name: string;
  status: PresenceStatus;
}
