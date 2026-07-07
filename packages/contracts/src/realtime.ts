import type { UUID } from "./domain";

/**
 * Contract C — Realtime events on the Butterbase channel `child:{child_id}:session`.
 * Person A defines the channel; Person B publishes; Person C subscribes.
 */

/** A YouTube micro-lesson surfaced during a replan. */
export interface VideoRecommendation {
  youtube_id: string;
  title: string;
  thumbnail_url: string;
  duration_seconds: number;
  url: string;
}

/** Emitted when Pipeline 1 finishes and the game is playable. */
export interface GameReadyEvent {
  event: "game_ready";
  game_url: string;
  level_count: number;
}

/** Emitted mid-session when Pipeline 2 replans a struggling level. */
export interface ReplanEvent {
  event: "replan";
  trigger_level: number;
  strategy: "prerequisite_inject" | "simpler_variant" | "reorder" | "confidence_builder";
  explanation: string;
  video: VideoRecommendation | null;
}

/** Emitted when the session ends and Pipeline 3's report is ready. */
export interface SessionEndEvent {
  event: "session_end";
  session_id: UUID;
  report_id: UUID;
}

export type SessionChannelEvent = GameReadyEvent | ReplanEvent | SessionEndEvent;

/** Channel name helper — keep in sync with the durable-actor + frontend subscriptions. */
export const sessionChannel = (childId: UUID): string => `child:${childId}:session`;
