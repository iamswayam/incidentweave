export type EvidenceSource = "vector" | "fulltext" | "both";

export interface InvestigationEvidence {
  chunk_id: string;
  file_path: string;
  start_line: number | null;
  end_line: number | null;
  rank: number;
  rrf_score: number | null;
  vector_score: number | null;
  fts_score: number | null;
  source: EvidenceSource | null;
}

export interface ClaimCitation {
  chunk_id: string;
  quote?: string;
  file_path?: string;
  start_line?: number | null;
  end_line?: number | null;
}

export interface InvestigationClaim {
  text?: string;
  claim?: string;
  supported?: boolean;
  evidence?: ClaimCitation[];
  citations?: ClaimCitation[];
}

export interface InvestigationResponse {
  investigation_id: number | null;
  repository_name: string;
  query: string;
  diagnosis: string;
  outcome: string;
  model_self_rating: string;
  rating_note: string;
  cited_chunk_ids: string[];
  evidence_check: Record<string, unknown>;
  retry_used?: boolean;
  tool_calls?: Record<string, unknown>[];
  claims: InvestigationClaim[];
  uncertainty_note: string;
  citation_validation: Record<string, unknown>;
  model: string;
  latency_ms: number | null;
  evaluation_note?: string;
  unavailable_answer: boolean;
  degraded: boolean;
  degraded_reason?: string | null;
  evidence: InvestigationEvidence[];
}

export interface RepositorySummary {
  name: string;
  chunk_count: number;
  embedded_chunk_count: number;
}

export interface InvestigationSummary {
  id: number;
  repository_name: string;
  query: string;
  outcome: string;
  model_self_rating: string | null;
  latency_ms: number | null;
  created_at: string;
}

export interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
  };
}

export class ApiError extends Error {
  status: number;
  code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}
