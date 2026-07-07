import type { Difficulty, OperationType, UUID } from "./domain";

/**
 * Contract A — PDF Upload → Pipeline 1 webhook.
 * Person A (Butterbase) fires this; Person B (RocketRide) receives it.
 */
export interface Pipeline1Request {
  child_id: UUID;
  assignment_id: UUID;
  /** Presigned Butterbase storage URL for the uploaded PDF. */
  pdf_storage_url: string;
  child_profile: {
    grade: number;
    attention_baseline_minutes: number;
  };
}

/** One entry mapping a game level back to its source homework question. */
export interface LevelMapEntry {
  level_index: number;
  question_id: UUID;
  topic: OperationType;
  difficulty: Difficulty;
}

/**
 * Contract B — Pipeline 1 output.
 * Person B writes it; Person A stores it; Person C reads it.
 */
export interface Pipeline1Result {
  session_id: UUID;
  /** Live Daytona preview URL of the generated game. */
  game_url: string;
  sandbox_id: string;
  level_map: LevelMapEntry[];
  estimated_session_minutes: number;
}
