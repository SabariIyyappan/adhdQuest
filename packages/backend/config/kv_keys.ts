/**
 * Butterbase KV key conventions (plan §4). Single source of truth so the durable
 * actor, pipelines, and functions all agree on key layout and TTLs.
 */

/** Live per-session state. TTL = 2h (auto-expires if the child abandons). */
export const activeSessionKey = (childId: string): string => `session:${childId}:active`;
export const ACTIVE_SESSION_TTL_SECONDS = 2 * 60 * 60;

/** Permanent mapping from child to their Cognee dataset name. No TTL. */
export const cogneeDatasetKey = (childId: string): string => `child:${childId}:cognee_dataset`;

/** Shape stored under {@link activeSessionKey}. */
export interface ActiveSessionState {
  sandbox_id: string;
  current_level: number;
  fail_count_by_level: Record<number, number>;
  replan_count: number;
  session_start_epoch: number;
  attention_seconds_elapsed: number;
}
