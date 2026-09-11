/**
 * MEDHA Frontend Therapist Types & Contracts
 * ===========================================
 *
 * Strongly-typed TypeScript interfaces matching the MEDHA backend API contracts
 * for Therapist Results, Specialist Predictions, Clinical Insights,
 * Recommendations, Dynamic Safety Protocols, and Patient Context.
 */

export interface CaseSummary {
  case_id: string;
  victim_id: string;
  user_id: string;
  status: string;
  current_timepoint: number;
  patient_name: string;
  patient_email: string;
  case_type?: string;
  case_created_at: string;
}

export interface SessionSummary {
  session_id: string;
  session_identifier: string;
  timepoint: number;
  status: string;
  closed_at?: string | null;
  created_at: string;
}

export interface SpecialistPredictionsResponse {
  struct_pred: number | null;
  text_pred: number | null;
  voice_pred: number | null;
  behav_pred: number | null;
  struct_available: boolean;
  text_available: boolean;
  voice_available: boolean;
  behav_available: boolean;
  behav_blocked: boolean;
  behav_block_reason: string;
}

export interface ConversationSummary {
  important_facts: string[];
  current_concerns: string[];
  recent_events: string[];
  support_context: string[];
  preferences: string[];
  ongoing_topics: string[];
  unresolved_topics: string[];
  important_observations: string[];
  updated_at?: string | null;
}

export interface CheckinResponseItem {
  question_id: string;
  question_text: string;
  response_text?: string | null;
  intent?: string | null;
  timestamp?: string | null;
}

export interface PatientContextResponse {
  conversation_summary?: ConversationSummary | null;
  checkin_responses: CheckinResponseItem[];
}

export interface CaseResultResponse {
  case_id: string;
  victim_id: string;
  user_id: string;
  session_id?: string | null;
  timepoint?: number | null;
  results_available: boolean;
  fusion_dds_prediction: number | null;
  temporal_risk_score: number | null;
  future_escalation_flag: number | null;
  triage_level: string;
  specialists: SpecialistPredictionsResponse;
  predicted_at?: string | null;
  result_record_created_at?: string | null;
  patient_context?: PatientContextResponse | null;
}

export interface CheckinQuestionItemResponse {
  question_id: string;
  question_text: string;
  domain?: string | null;
  answer?: Record<string, any> | null;
  answer_status: string;
  answered_at?: string | null;
}

export interface CheckinSummaryResponse {
  checkin_id: string;
  timepoint: number;
  status: string;
  started_at: string;
  completed_at?: string | null;
  questions: CheckinQuestionItemResponse[];
}

export interface BehaviourSummaryResponse {
  timepoint: number;
  app_interaction_duration?: number | null;
  checkin_completion_rate?: number | null;
  missed_checkin_count?: number | null;
  computed_at: string;
}

export interface AlertSummaryResponse {
  id: string;
  event_type: string;
  severity: string;
  status: string;
  detected_at: string;
  handled_by?: string | null;
  handled_at?: string | null;
}

export interface AlertHandleRequest {
  status: 'handled' | 'resolved' | 'dismissed' | 'active' | string;
  resolution_note?: string;
}

export interface AlertHandleResponse extends AlertSummaryResponse {}

export interface InsightFactorItem {
  factor: string;
  description: string;
  type: 'trend' | 'text' | 'voice' | 'behaviour' | 'structured' | 'temporal' | 'context' | 'activity' | string;
}

export interface InsightSignalsSummary {
  text_distress?: number | null;
  voice_distress?: number | null;
  behavioural_risk?: number | null;
  structured_risk?: number | null;
  temporal_risk?: number | null;
}

export interface InsightContextSummary {
  threat_event: boolean;
  protection_issue: boolean;
  financial_hardship: boolean;
  rehabilitation_issue: boolean;
  investigation_delay: boolean;
  compensation_delay: boolean;
}

export interface InsightActivitySummary {
  checkins: number;
  journal_entries: number;
  voice_interactions: number;
  text_interactions: number;
}

export interface CaseInsightsResponse {
  case_id: string;
  victim_id: string;
  session_id?: string | null;
  timepoint?: number | null;
  results_available: boolean;
  trend_available: boolean;
  risk_level?: string | null;
  triage_level?: string | null;
  fused_risk_score?: number | null;
  summary: string;
  factors: InsightFactorItem[];
  trend_explanation: string;
  disclaimer: string;
  signals: InsightSignalsSummary;
  context: InsightContextSummary;
  recent_activity: InsightActivitySummary;
  generated_at: string;
}

export interface RecommendationItem {
  id: string;
  category: string;
  priority: 'IMMEDIATE' | 'URGENT' | 'PRIORITY' | 'INCREASED' | 'ROUTINE' | string;
  reason: string;
  action: string;
}

export interface SelfHelpResourceItem {
  id: string;
  type: string;
  title: string;
  category: string;
  description: string;
}

export interface SafetyProtocolResponse {
  alert_id: string;
  case_id: string;
  session_id?: string | null;
  alert_triggered: boolean;
  priority: string;
  alert_type: string;
  title: string;
  message: string;
  recommended_action: string;
  cta: string;
  reason: string;
  source: string;
  reason_codes: string[];
  status: string;
  timestamp: string;
}

export interface CaseRecommendationsResponse {
  case_id: string;
  victim_id: string;
  session_id?: string | null;
  timepoint?: number | null;
  results_available: boolean;
  risk_level?: string | null;
  triage_level?: string | null;
  fused_risk_score?: number | null;
  recommendations: RecommendationItem[];
  self_help_resources: SelfHelpResourceItem[];
  safety_protocol?: SafetyProtocolResponse | null;
  disclaimer: string;
  generated_at: string;
}
