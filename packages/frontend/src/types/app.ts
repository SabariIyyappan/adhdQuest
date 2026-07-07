export type UploadStep = 'idle' | 'uploading' | 'extracting' | 'generating' | 'ready' | 'error';

export interface AppNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  duration?: number; // ms to auto-dismiss
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface MedicationLogEntry {
  id: string;
  child_id: string;
  logged_at: string;
  medication_name: string;
  dose_mg: number;
}

export interface ChildProfile {
  id: string;
  parent_user_id: string;
  name: string;
  grade: number;
  attention_baseline_minutes: number;
  doctor_user_id?: string;
  created_at: string;
}
