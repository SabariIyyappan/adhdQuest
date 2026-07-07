/**
 * Durable session actor (plan §7 · Person A).
 *
 * One instance per active child session. Serializes gameplay events so concurrent
 * game actions never race, maintains the per-level fail counter, and fires the
 * Pipeline 2 (replan) and Pipeline 3 (report) webhooks at the right moments.
 */

import type { SessionEvent } from "@adhdquest/contracts";
import { ACTIVE_SESSION_TTL_SECONDS, type ActiveSessionState } from "../config/kv_keys";

const FAIL_THRESHOLD = 3;

export interface ActorEnv {
  /** POST a JSON body to a pipeline webhook. */
  fireWebhook(url: string, body: unknown): Promise<void>;
  pipeline2Url: string;
  pipeline3Url: string;
  /** Persist state back to KV with the standard TTL. */
  saveState(state: ActiveSessionState): Promise<void>;
  /** Grade-derived attention baseline in seconds, for the replan trigger context. */
  attentionBaselineSeconds: number;
  childId: string;
  sessionId: string;
  conceptForLevel(levelIndex: number): string;
}

/**
 * Fold a single event into session state and return any side effects triggered.
 * Pure w.r.t. state mutation; performs I/O only through {@link ActorEnv}.
 */
export async function handleEvent(
  state: ActiveSessionState,
  event: SessionEvent,
  env: ActorEnv,
): Promise<void> {
  switch (event.event_type) {
    case "level_start":
      // Moving to a new level resets that level's fail counter (plan §6 Feature 2).
      if (event.level_index !== state.current_level) {
        state.current_level = event.level_index;
        state.fail_count_by_level[event.level_index] = 0;
      }
      break;

    case "level_fail": {
      const count = (state.fail_count_by_level[event.level_index] ?? 0) + 1;
      state.fail_count_by_level[event.level_index] = count;
      if (count >= FAIL_THRESHOLD) {
        await triggerReplan(state, event.level_index, env);
      }
      break;
    }

    case "level_complete":
      state.fail_count_by_level[event.level_index] = 0;
      break;

    case "session_end":
      await triggerReport(env);
      break;

    default:
      break; // replan_triggered / video_watched are informational
  }

  await env.saveState(state);
}

async function triggerReplan(
  state: ActiveSessionState,
  levelIndex: number,
  env: ActorEnv,
): Promise<void> {
  state.replan_count += 1;
  await env.fireWebhook(env.pipeline2Url, {
    child_id: env.childId,
    session_id: env.sessionId,
    current_level_index: levelIndex,
    concept_tag: env.conceptForLevel(levelIndex),
    time_elapsed_seconds: state.attention_seconds_elapsed,
    attention_baseline_seconds: env.attentionBaselineSeconds,
  });
}

async function triggerReport(env: ActorEnv): Promise<void> {
  await env.fireWebhook(env.pipeline3Url, {
    event: "session_end",
    child_id: env.childId,
    session_id: env.sessionId,
  });
}

/** Fresh state for a newly created session. */
export function initialState(sandboxId: string): ActiveSessionState {
  return {
    sandbox_id: sandboxId,
    current_level: 0,
    fail_count_by_level: {},
    replan_count: 0,
    session_start_epoch: Date.now(),
    attention_seconds_elapsed: 0,
  };
}

export { FAIL_THRESHOLD, ACTIVE_SESSION_TTL_SECONDS };
