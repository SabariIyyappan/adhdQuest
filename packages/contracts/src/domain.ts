/**
 * Shared domain vocabulary referenced across every contract.
 * Keep this small and stable — it is imported by all three packages.
 */

/** Math operation a question exercises. Drives game-mechanic assignment. */
export type OperationType =
  | "addition"
  | "subtraction"
  | "multiplication"
  | "division"
  | "fractions"
  | "decimals"
  | "word_problem";

/** Question difficulty on a 1 (easiest) — 5 (hardest) scale. */
export type Difficulty = 1 | 2 | 3 | 4 | 5;

/** Game mechanic rendered for a level. See Feature 1 mechanic-assignment logic. */
export type GameMechanic = "maze" | "matching" | "quest" | "speed_round" | "puzzle";

/** Coarse cognitive-load bucket for an assignment. */
export type AttentionLoad = "light" | "moderate" | "heavy";

/** Lifecycle of a play session (mirrors sessions.status in Postgres). */
export type SessionStatus = "generating" | "active" | "replanning" | "complete";

/** Roles carried in the auth JWT; gate RLS + which report fields are visible. */
export type UserRole = "parent" | "doctor";

/** UUID string alias for readability at call sites. */
export type UUID = string;

/** ISO-8601 timestamp string. */
export type ISODateTime = string;
