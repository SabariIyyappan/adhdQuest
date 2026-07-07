import type { ISODateTime, UUID } from "./domain";

/**
 * Contract D — Session event payload (game → Butterbase).
 * Person B defines what the game emits; Person A stores it; Person C displays it.
 */

export type SessionEventType =
  | "level_start"
  | "level_complete"
  | "level_fail"
  | "replan_triggered"
  | "video_watched"
  | "session_end";

export interface SessionEvent {
  session_id: UUID;
  event_type: SessionEventType;
  level_index: number;
  timestamp: ISODateTime;
  payload: SessionEventPayload;
}

/** Loose bag of per-event metrics — fields present depend on event_type. */
export interface SessionEventPayload {
  time_on_level_seconds?: number;
  fail_count?: number;
  score?: number;
  video_id?: string;
  [key: string]: unknown;
}
