/**
 * Butterbase AI-gateway model routing (plan §3).
 *
 * Cheap/fast model for extraction & classification; strong model for generation,
 * replan reasoning, and report synthesis. Pipelines reference tasks by name so the
 * concrete model can change here without touching pipeline code.
 */

export type ModelTier = "fast" | "strong";

export type AiTask =
  | "assignment_metadata" // Pipeline 1 — score cognitive load
  | "game_spec" // Pipeline 1 — generate game spec
  | "replan_strategy" // Pipeline 2 — decide replan
  | "report_synthesis"; // Pipeline 3 — parent + doctor narrative

export const TASK_TIER: Record<AiTask, ModelTier> = {
  assignment_metadata: "fast",
  game_spec: "strong",
  replan_strategy: "strong",
  report_synthesis: "strong",
};

/** Concrete model per tier, overridable via env. Uses current Claude model IDs. */
export const TIER_MODEL: Record<ModelTier, string> = {
  fast: process.env.AI_MODEL_FAST ?? "claude-haiku-4-5-20251001",
  strong: process.env.AI_MODEL_STRONG ?? "claude-sonnet-5",
};

export const modelForTask = (task: AiTask): string => TIER_MODEL[TASK_TIER[task]];
