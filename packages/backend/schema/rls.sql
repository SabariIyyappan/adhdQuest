-- ADHDQuest — Row-Level Security policies (plan §4).
-- COPPA-safe by design: a child's rows are invisible unless the requester is the
-- owning parent or the assigned doctor. Apply after tables.sql.

alter table children              enable row level security;
alter table assignments           enable row level security;
alter table sessions              enable row level security;
alter table questions             enable row level security;
alter table session_events        enable row level security;
alter table video_recommendations enable row level security;
alter table reports               enable row level security;
alter table medication_logs       enable row level security;

-- Reusable predicate: the current user may see this child.
-- (parent owns it, or doctor is assigned to it.)
create or replace function can_access_child(cid uuid)
returns boolean language sql stable as $$
  select exists (
    select 1 from children c
    where c.id = cid
      and (c.parent_user_id = auth.uid() or c.doctor_user_id = auth.uid())
  );
$$;

-- children ------------------------------------------------------------
create policy children_select on children for select
  using (parent_user_id = auth.uid() or doctor_user_id = auth.uid());
create policy children_write on children for all
  using (parent_user_id = auth.uid())
  with check (parent_user_id = auth.uid());

-- child-scoped tables share the same access predicate ----------------
create policy assignments_access on assignments for select
  using (can_access_child(child_id));
create policy sessions_access on sessions for select
  using (can_access_child(child_id));
create policy questions_access on questions for select
  using (can_access_child((select child_id from assignments a where a.id = assignment_id)));
create policy session_events_access on session_events for select
  using (can_access_child((select child_id from sessions s where s.id = session_id)));
create policy video_recs_access on video_recommendations for select
  using (can_access_child((select child_id from sessions s where s.id = session_id)));

-- reports: parent sees the summary, doctor sees the full json.
-- Column-level projection is enforced in the REST layer / views; row access here.
create policy reports_access on reports for select
  using (can_access_child(child_id));

-- medication_logs: parent only, never the doctor at write time.
create policy medlogs_select on medication_logs for select
  using (can_access_child(child_id));
create policy medlogs_write on medication_logs for all
  using ((select parent_user_id from children c where c.id = child_id) = auth.uid())
  with check ((select parent_user_id from children c where c.id = child_id) = auth.uid());
