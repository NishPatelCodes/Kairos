export type Profile = {
  email: string;
  display_name: string;
  timezone: string;
  onboarding_completed: boolean;
  peak_energy: "morning" | "afternoon" | "evening";
  typical_weekday: string;
  blockers: string;
  preferences: {
    work_start: string | null;
    work_end: string | null;
    preferred_block_minutes: number;
    break_every_minutes: number;
    break_duration_minutes: number;
  };
};

export type AnnualGoal = {
  id: number;
  title: string;
  description: string;
  target_date: string;
  is_active: boolean;
  days_remaining: number;
};

export type MonthlyGoal = {
  id: number;
  annual_goal: number | null;
  title: string;
  description: string;
  metric_target: number | null;
  metric_current: number;
  metric_unit: string;
  month: string;
  priority: number;
  status: "active" | "completed" | "paused";
  progress_pct: number | null;
};

export type ScheduleStatus = "upcoming" | "in_progress" | "completed" | "missed" | "rescheduled";

export type ScheduleItem = {
  id: number;
  monthly_goal: number | null;
  goal_title: string | null;
  goal_metric_unit: string | null;
  goal_metric_target: number | null;
  goal_metric_current: number | null;
  title: string;
  notes: string;
  date: string;
  start_time: string;
  end_time: string;
  status: ScheduleStatus;
  kind: "focus" | "break" | "fixed" | "habit" | "flexible";
  is_fixed: boolean;
  created_by: string;
  duration_minutes: number;
};

export type ChatMessage = {
  id: number | string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: {
    blocks?: Array<{ type: string; item?: ScheduleItem; items?: ScheduleItem[] }>;
    tools?: string[];
  };
  created_at?: string;
};

export type Conversation = {
  id: number;
  date: string;
  kind: "daily" | "onboarding";
  messages: ChatMessage[];
};

export type DailyProgress = {
  date: string;
  planned_count: number;
  completed_count: number;
  missed_count: number;
  planned_minutes: number;
  completed_minutes: number;
  completion_rate: number;
};

export type MonthlyProgress = {
  month: string;
  overall_pct: number;
  expected_pct: number;
  velocity: string;
  focus_minutes: number;
  planned_minutes: number;
  completed_count: number;
  planned_count: number;
  goals: Array<{
    id: number;
    title: string;
    progress_pct: number | null;
    metric_current: number;
    metric_target: number | null;
    metric_unit: string;
    status: string;
  }>;
};

export type WeeklyProgress = {
  start: string;
  end: string;
  days: DailyProgress[];
  completed_tasks: number;
  planned_tasks: number;
  missed_tasks: number;
  focus_minutes: number;
  completion_rate: number;
};

export type Dashboard = {
  daily: DailyProgress;
  weekly: WeeklyProgress;
  monthly: MonthlyProgress;
};
