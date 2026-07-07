-- ADHDQuest — Butterbase Postgres schema (declarative).
-- Person A owns migrations exclusively. Others call REST endpoints only.
-- Mirrors plan §4. Apply this before rls.sql.

create extension if not exists "pgcrypto";

-- Children profiles, each owned by a parent, optionally shared with a doctor.
create table if not exists children (
  id                          uuid primary key default gen_random_uuid(),
  parent_user_id              uuid not null references auth.users (id),
  name                        text not null,
  grade                       int  not null,
  attention_baseline_minutes  int  not null default 15,
  doctor_user_id              uuid references auth.users (id),
  created_at                  timestamptz not null default now()
);

-- One uploaded PDF homework assignment.
create table if not exists assignments (
  id                          uuid primary key default gen_random_uuid(),
  child_id                    uuid not null references children (id) on delete cascade,
  pdf_storage_key             text not null,           -- S3/R2 key in Butterbase storage
  subject                     text,
  grade                       int,
  total_questions             int,
  avg_difficulty              float,
  estimated_attention_load    text check (estimated_attention_load in ('light','moderate','heavy')),
  created_at                  timestamptz not null default now()
);

-- One play session generated from an assignment.
create table if not exists sessions (
  id                          uuid primary key default gen_random_uuid(),
  child_id                    uuid not null references children (id) on delete cascade,
  assignment_id               uuid not null references assignments (id) on delete cascade,
  sandbox_id                  text,                    -- Daytona sandbox ID
  game_url                    text,
  status                      text not null default 'generating'
                                check (status in ('generating','active','replanning','complete')),
  started_at                  timestamptz not null default now(),
  ended_at                    timestamptz
);

-- Extracted homework questions, each mapped to a game level.
create table if not exists questions (
  id                          uuid primary key default gen_random_uuid(),
  assignment_id               uuid not null references assignments (id) on delete cascade,
  raw_text                    text not null,
  topic                       text,
  operation_type              text,
  difficulty                  int check (difficulty between 1 and 5),
  level_index                 int
);

-- Append-only stream of gameplay events (Contract D).
create table if not exists session_events (
  id                          uuid primary key default gen_random_uuid(),
  session_id                  uuid not null references sessions (id) on delete cascade,
  event_type                  text not null
                                check (event_type in ('level_start','level_complete','level_fail',
                                                      'replan_triggered','video_watched','session_end')),
  level_index                 int,
  timestamp                   timestamptz not null default now(),
  payload                     jsonb not null default '{}'::jsonb
);

-- YouTube micro-lessons surfaced during replans.
create table if not exists video_recommendations (
  id                          uuid primary key default gen_random_uuid(),
  session_id                  uuid not null references sessions (id) on delete cascade,
  level_index                 int,
  youtube_id                  text not null,
  title                       text,
  duration_seconds            int,
  concept_tag                 text,
  watched                     bool not null default false
);

-- Structured post-session reports (Contract E).
create table if not exists reports (
  id                          uuid primary key default gen_random_uuid(),
  child_id                    uuid not null references children (id) on delete cascade,
  session_id                  uuid not null references sessions (id) on delete cascade,
  report_json                 jsonb not null,          -- full report — doctor-visible
  summary_text                text,                    -- parent-visible narrative
  created_at                  timestamptz not null default now()
);

-- Optional parent-entered medication timing, for correlation analysis.
create table if not exists medication_logs (
  id                          uuid primary key default gen_random_uuid(),
  child_id                    uuid not null references children (id) on delete cascade,
  logged_at                   timestamptz not null,
  medication_name             text,
  dose_mg                     float
);

create index if not exists idx_assignments_child   on assignments (child_id);
create index if not exists idx_sessions_child       on sessions (child_id);
create index if not exists idx_questions_assignment on questions (assignment_id);
create index if not exists idx_events_session       on session_events (session_id);
create index if not exists idx_reports_child        on reports (child_id);
create index if not exists idx_medlogs_child        on medication_logs (child_id);
