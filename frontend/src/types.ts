export interface FoundryState {
  user_intent: string;
  user_query: string;
  iteration_count: number;
  max_iterations: number;
  is_approved: boolean;
  is_halted: boolean;
  current_agent: string | null;
  current_draft: string | null;
  draft_versions: DraftVersion[];
  current_version: number;
  agent_notes: AgentNote[];
  safety_review: SafetyReview | null;
  clinical_review: ClinicalReview | null;
  started_at: string;
  last_updated: string;
  final_protocol: string | null;
  human_feedback: string | null;
  human_edited_draft: string | null;
  awaiting_human_approval: boolean;
  next_action?: string | null;
}

export interface DraftVersion {
  version: number;
  content: string;
  created_at: string;
  created_by: string;
  notes: AgentNote[];
}

export interface AgentNote {
  agent: string;
  timestamp: string;
  message: string;
  context?: Record<string, any>;
}

export interface SafetyReview {
  status: 'pending' | 'passed' | 'flagged' | 'critical';
  flagged_lines: number[];
  concerns: string[];
  recommendations: string[];
  reviewed_at: string | null;
}

export interface ClinicalReview {
  status: 'pending' | 'approved' | 'needs_revision' | 'rejected';
  empathy_score: number;
  tone_score: number;
  structure_score: number;
  feedback: string[];
  reviewed_at: string | null;
}

export interface StateUpdate {
  node: string;
  state: FoundryState;
  timestamp: string;
}







