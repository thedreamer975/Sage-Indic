export type AnswerStatus =
  | "ANSWERED"
  | "PARTIALLY_ANSWERED"
  | "ABSTAINED"
  | "BLOCKED"
  | "ERROR";

export type VerificationStatus =
  | "SUPPORTED"
  | "CONTRADICTED"
  | "INSUFFICIENT_EVIDENCE"
  | "CONFLICTING_EVIDENCE";

export interface ContentHash {
  algorithm: string;
  digest: string;
}

export interface RetrievedEvidence {
  evidence_id: string;
  rank: number;
  score: number;
  document_id: string;
  chunk_id: string;
  title: string;
  source_name: string;
  publisher: string;
  license_name: string;
  license_url: string | null;
  source_url: string | null;
  text: string;
  char_start: number;
  char_end: number;
  content_hash: ContentHash;
  selected: boolean;
  used_in_answer: boolean;
}

export interface AnswerClaim {
  claim_id: string;
  text: string;
  verification_status: VerificationStatus;
  evidence_ids: string[];
  citation_ids: string[];
  explanation: string;
  caveat: string | null;
  confidence: number | null;
}

export interface Citation {
  citation_id: string;
  evidence_id: string;
  document_id: string;
  chunk_id: string;
  title: string;
  source_name: string;
  publisher: string;
  license_name: string;
  source_url: string | null;
  quoted_text: string;
  char_start: number;
  char_end: number;
  claim_ids: string[];
  verification_status: VerificationStatus;
  supports_claim: boolean;
}

export interface VerificationSummary {
  total_claims: number;
  supported_count: number;
  contradicted_count: number;
  insufficient_count: number;
  conflicting_count: number;
  all_claims_supported: boolean;
  cited_evidence_count: number;
  evidence_coverage: number;
  notes: string[];
}

export interface GenerationMetadata {
  requested_mode: "deterministic" | "llm" | "llm_fallback";
  used_mode: "deterministic" | "llm" | "llm_fallback";
  provider: string;
  model: string | null;
  provider_available: boolean;
  fallback_used: boolean;
  fallback_reason: string | null;
  draft_rejected: boolean;
  rejection_reasons: string[];
  raw_draft_kept_internally: boolean;
  latency_ms: number;
}

export interface LatencyMetadata {
  detection_ms: number;
  safety_ms: number;
  retrieval_ms: number;
  composition_ms: number;
  generation_ms: number;
  total_ms: number;
}

export interface SafetyInfo {
  label: string;
  method: string;
  confidence: number | null;
  category: string;
  notes: string[];
}

export interface QueryAnalysis {
  intent: string;
  content_terms: string[];
  matched_terms: string[];
  missing_terms: string[];
  evidence_coverage: number;
  expanded_query: string;
}

export interface AnswerResponse {
  request_id: string;
  original_query: string;
  detected_modality: string;
  detected_modality_confidence: number;
  normalized_query: string;
  answer_text: string;
  answer_status: AnswerStatus;
  answer_claims: AnswerClaim[];
  citations: Citation[];
  retrieved_evidence: RetrievedEvidence[];
  verification_summary: VerificationSummary;
  abstention_reason: string | null;
  generation_metadata: GenerationMetadata;
  query_analysis: QueryAnalysis;
  safety: SafetyInfo;
  warnings: string[];
  latency_metadata: LatencyMetadata;
}

export interface ServiceStatus {
  service: string;
  version: string;
  corpus: {
    loaded: boolean;
    version: string;
    documents: number;
    chunks: number;
    retrieval_eligible_only: boolean;
  };
  retriever: {
    indexed: boolean;
    method: string;
    top_k: number;
    tokenizer: string;
  };
  llm: {
    configured: boolean;
    available: boolean;
    provider: string;
    base_url: string;
    model: string;
    error: string | null;
    max_tokens: number;
    temperature: number;
    timeout_seconds: number;
  };
  safety: {
    method: string;
    semantic_classifier_available: boolean;
  };
  deterministic_fallback: boolean;
  default_generation_mode: string;
}

export interface DemoExample {
  id: string;
  label: string;
  query: string;
  modality: string;
  expected_behavior: "answer" | "partial" | "abstain";
  note: string;
}

export interface CorpusDocument {
  document_id: string;
  title: string;
  source_name: string;
  publisher: string;
  license_name: string;
  license_status: string;
  source_url: string | null;
  source_revision: string | null;
  chunk_count: number;
  language: string;
  script: string;
}

export interface CorpusInfo {
  corpus_version: string;
  document_count: number;
  chunk_count: number;
  documents: CorpusDocument[];
}
