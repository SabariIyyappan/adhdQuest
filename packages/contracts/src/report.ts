import type { OperationType } from "./domain";

/**
 * Contract E — Report JSON schema.
 * Person B generates it; Person A stores it (reports.report_json); Person C renders it.
 */

export interface AttentionArcPoint {
  minute: number;
  errors: number;
}

export interface ConceptPerformance {
  concept: OperationType | string;
  avg_time_seconds?: number;
  fail_rate: number;
  replan_triggered?: boolean;
}

export interface NextSessionRecommendations {
  suggested_duration_minutes: number;
  prioritize_concepts: string[];
  start_with_concept: string;
}

export interface MedicationCorrelation {
  time_delta_minutes: number;
  medication: string;
  observed_effect: string;
}

export interface SessionReport {
  session_summary: {
    total_minutes: number;
    levels_completed: number;
    levels_total: number;
    completion_rate: number;
    replan_count: number;
    videos_watched: number;
  };
  attention_arc: AttentionArcPoint[];
  concept_performance: ConceptPerformance[];
  bottleneck_concept: string;
  bottleneck_centrality_score: number;
  /** Plain-English narrative visible to the parent. */
  parent_summary: string;
  /** Full clinical narrative visible only to the doctor. */
  doctor_narrative: string;
  next_session_recommendations: NextSessionRecommendations;
  /** Null when no medication was logged for the session. */
  medication_correlation: MedicationCorrelation | null;
}
