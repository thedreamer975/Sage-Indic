import type { AnswerResponse, Citation } from "../types";

interface AnswerPanelProps {
  result: AnswerResponse | null;
  error: string | null;
  loading: boolean;
}

const statusLabel: Record<string, string> = {
  ANSWERED: "Answered",
  PARTIALLY_ANSWERED: "Partially answered",
  ABSTAINED: "Abstained",
  BLOCKED: "Blocked by safety policy",
  ERROR: "Error",
};

function CitationText({
  text,
  citations,
}: {
  text: string;
  citations: Citation[];
}) {
  const byId = new Map(citations.map((citation) => [citation.citation_id, citation]));
  const parts = text.split(/(\[C\d+\])/g);
  return (
    <>
      {parts.map((part, index) => {
        const match = part.match(/^\[(C\d+)\]$/);
        if (!match) return <span key={index}>{part}</span>;
        const citation = byId.get(match[1]);
        if (!citation) return <span key={index}>{part}</span>;
        return (
          <sup key={index} className="inline-citation" title={citation.title}>
            <a href={`#cite-${citation.citation_id}`}>{citation.citation_id}</a>
          </sup>
        );
      })}
    </>
  );
}

export function AnswerPanel({ result, error, loading }: AnswerPanelProps) {
  if (error) {
    return (
      <section className="panel" aria-live="polite">
        <div className="error-state">
          <p className="eyebrow">Request failed</p>
          <h2>Could not complete the query</h2>
          <p>{error}</p>
          <p className="help-text">
            Check that the backend is running at the configured API address and that the corpus
            files are present under <code>data/processed/rag/</code>.
          </p>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="panel loading-panel" aria-live="polite" aria-busy="true">
        <p className="eyebrow">Processing</p>
        <h2>Running the evidence pipeline</h2>
        <p className="help-text">
          Detection, safety screening, retrieval, claim extraction, verification, then composition.
          This applies the real pipeline; no stored answers are shown.
        </p>
        <ol className="loading-stages" aria-hidden="true">
          <li>Detect script and code-mix</li>
          <li>Screen input safety</li>
          <li>Retrieve evidence passages</li>
          <li>Extract and verify claims</li>
          <li>Compose cited answer</li>
        </ol>
        <div className="loading-bar" aria-hidden="true">
          <span />
        </div>
        <p className="help-text">
          Optional LLM paraphrase can take tens of seconds on a local provider. Deterministic
          composition is faster.
        </p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="panel empty-state" aria-live="polite">
        <p className="eyebrow">Answer</p>
        <h2>Evidence-grounded answer will appear here</h2>
        <p>
          The pipeline runs input detection, conservative normalization, retrieval, claim
          extraction, relation-aware verification, and composition. It answers only from
          retrieved passages and abstains when evidence is insufficient.
        </p>
        <div className="empty-steps" aria-hidden="true">
          <span>Detect</span>
          <span>Retrieve</span>
          <span>Verify</span>
          <span>Compose</span>
        </div>
      </section>
    );
  }

  const summary = result.verification_summary;
  const generation = result.generation_metadata;

  return (
    <section className="panel answer-panel" aria-live="polite" aria-labelledby="answer-heading">
      <div className="answer-header">
        <div>
          <p className="eyebrow">Composed response</p>
          <h2 id="answer-heading">
            <span className={`status-badge status-${result.answer_status.toLowerCase()}`}>
              {statusLabel[result.answer_status] ?? result.answer_status}
            </span>
          </h2>
        </div>
        <div className="answer-meta">
          <span className="meta-label">Detected form</span>
          <strong>{result.detected_modality.replaceAll("_", " ")}</strong>
          <span className="meta-sub">
            confidence {result.detected_modality_confidence.toFixed(2)} · intent{" "}
            {result.query_analysis.intent.toLowerCase()}
          </span>
        </div>
      </div>

      <div className="normalized-box">
        <span className="meta-label">Normalized input</span>
        <p lang="te">{result.normalized_query}</p>
      </div>

      <div className="answer-text" lang="te">
        <CitationText text={result.answer_text} citations={result.citations} />
      </div>

      {result.abstention_reason && (
        <div className={`callout ${result.answer_status === "BLOCKED" ? "callout-danger" : "callout-warning"}`}>
          <strong>
            {result.answer_status === "BLOCKED" ? "Safety policy" : "Abstention reason"}
          </strong>
          <p>{result.abstention_reason}</p>
        </div>
      )}

      <div className="answer-stats">
        <div>
          <span className="stat-value">{summary.supported_count}</span>
          <span className="stat-label">supported claims</span>
        </div>
        <div>
          <span className="stat-value">{summary.cited_evidence_count}</span>
          <span className="stat-label">cited passages</span>
        </div>
        <div>
          <span className="stat-value">{(summary.evidence_coverage * 100).toFixed(0)}%</span>
          <span className="stat-label">term coverage (heuristic)</span>
        </div>
        <div>
          <span className="stat-value">{Math.round(result.latency_metadata.total_ms)} ms</span>
          <span className="stat-label">measured latency</span>
        </div>
      </div>

      <div className="generation-note">
        <span className={`mode-chip mode-${generation.used_mode}`}>
          {generation.used_mode === "llm"
            ? "LLM paraphrase accepted"
            : generation.used_mode === "llm_fallback"
              ? "Deterministic fallback"
              : "Deterministic composition"}
        </span>
        <span className="help-text">
          {generation.used_mode === "llm"
            ? "The LLM draft passed claim-level verification against the supplied evidence."
            : "The visible answer is composed from verbatim evidence sentences; the application attaches citations."}
        </span>
      </div>

      {generation.fallback_reason && (
        <p className="inline-warning">Provider note: {generation.fallback_reason}</p>
      )}
      {generation.draft_rejected && (
        <div className="callout callout-warning">
          <strong>LLM draft rejected</strong>
          <p>
            The draft contained claims or citations that could not be verified against the supplied
            evidence. It was not shown as a verified answer.
          </p>
          {generation.rejection_reasons.length > 0 && (
            <ul>
              {generation.rejection_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {result.warnings.length > 0 && (
        <ul className="warning-list">
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}

      {result.citations.length > 0 && (
        <div className="citations">
          <div className="section-heading">
            <h3>Citations</h3>
            <p>Attached programmatically from supplied evidence. Support is claim-level.</p>
          </div>
          {result.citations.map((citation) => (
            <article className="citation-card" id={`cite-${citation.citation_id}`} key={citation.citation_id}>
              <div className="citation-topline">
                <span className="citation-id">[{citation.citation_id}]</span>
                <span className={`support-badge ${citation.supports_claim ? "support-yes" : "support-no"}`}>
                  {citation.supports_claim ? "supports claim" : "does not support claim"}
                </span>
              </div>
              <h4>{citation.title}</h4>
              <p className="citation-source">
                {citation.document_id} · {citation.chunk_id} · {citation.license_name}
              </p>
              <blockquote lang="te">{citation.quoted_text}</blockquote>
              {citation.source_url && (
                <a href={citation.source_url} target="_blank" rel="noreferrer">
                  Open source revision
                </a>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
