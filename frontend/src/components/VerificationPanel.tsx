import type { AnswerResponse } from "../types";

interface VerificationPanelProps {
  result: AnswerResponse;
}

const statusCopy: Record<string, string> = {
  SUPPORTED: "Supported",
  CONTRADICTED: "Contradicted",
  INSUFFICIENT_EVIDENCE: "Insufficient evidence",
  CONFLICTING_EVIDENCE: "Conflicting evidence",
};

export function VerificationPanel({ result }: VerificationPanelProps) {
  const summary = result.verification_summary;
  const analysis = result.query_analysis;

  return (
    <div className="verification-panel">
      <div className="section-heading">
        <h3>Claim verification</h3>
        <p>
          The verifier is deterministic and heuristic. A citation ID existing in the corpus is not
          treated as proof that its passage supports a claim.
        </p>
      </div>

      <div className="verification-grid">
        <div className="verify-tile verify-supported">
          <span>{summary.supported_count}</span>
          <small>supported</small>
        </div>
        <div className="verify-tile verify-contradicted">
          <span>{summary.contradicted_count}</span>
          <small>contradicted</small>
        </div>
        <div className="verify-tile verify-insufficient">
          <span>{summary.insufficient_count}</span>
          <small>insufficient</small>
        </div>
        <div className="verify-tile verify-conflicting">
          <span>{summary.conflicting_count}</span>
          <small>conflicting</small>
        </div>
      </div>

      <div className="coverage-box">
        <div className="coverage-topline">
          <span>Evidence term coverage (heuristic)</span>
          <strong>{(analysis.evidence_coverage * 100).toFixed(0)}%</strong>
        </div>
        <div className="coverage-track">
          <div
            className="coverage-fill"
            style={{ width: `${Math.min(100, Math.max(0, analysis.evidence_coverage * 100))}%` }}
          />
        </div>
        <p className="help-text">
          Matched: {analysis.matched_terms.length > 0 ? analysis.matched_terms.join(", ") : "none"}
          {analysis.missing_terms.length > 0
            ? ` · Missing: ${analysis.missing_terms.join(", ")}`
            : " · No informative query term is missing from retrieved evidence."}
        </p>
      </div>

      {result.abstention_reason && (
        <div className="callout callout-warning">
          <strong>Why the system abstained</strong>
          <p>{result.abstention_reason}</p>
        </div>
      )}

      {result.answer_claims.length === 0 ? (
        <p className="empty-inline">No answer claims were composed for this response.</p>
      ) : (
        <div className="claim-list">
          {result.answer_claims.map((claim) => (
            <article className={`claim-card claim-${claim.verification_status.toLowerCase()}`} key={claim.claim_id}>
              <div className="claim-topline">
                <span className="claim-id">{claim.claim_id}</span>
                <span className={`claim-status status-${claim.verification_status.toLowerCase()}`}>
                  {statusCopy[claim.verification_status] ?? claim.verification_status}
                </span>
              </div>
              <p className="claim-text" lang="te">
                {claim.text}
              </p>
              <p className="claim-explanation">{claim.explanation}</p>
              <div className="claim-tags">
                {claim.evidence_ids.map((id) => (
                  <span className="data-chip" key={id}>
                    evidence {id}
                  </span>
                ))}
                {claim.citation_ids.map((id) => (
                  <span className="data-chip" key={id}>
                    citation {id}
                  </span>
                ))}
                {claim.confidence !== null && (
                  <span className="data-chip" title="Heuristic verifier score, not a calibrated probability">
                    heuristic score {claim.confidence.toFixed(3)}
                  </span>
                )}
              </div>
              {claim.caveat && <p className="claim-caveat">{claim.caveat}</p>}
            </article>
          ))}
        </div>
      )}

      <div className="trace-grid">
        <div>
          <span className="meta-label">Generation mode</span>
          <p>{result.generation_metadata.used_mode}</p>
        </div>
        <div>
          <span className="meta-label">Provider</span>
          <p>
            {result.generation_metadata.provider}
            {result.generation_metadata.model ? ` · ${result.generation_metadata.model}` : ""}
          </p>
        </div>
        <div>
          <span className="meta-label">Safety</span>
          <p>
            {result.safety.label} · {result.safety.method}
          </p>
        </div>
        <div>
          <span className="meta-label">Request</span>
          <p>{result.request_id}</p>
        </div>
      </div>

      <details className="latency-details">
        <summary>Measured stage latencies</summary>
        <dl className="latency-grid">
          <div>
            <dt>Detection</dt>
            <dd>{result.latency_metadata.detection_ms.toFixed(2)} ms</dd>
          </div>
          <div>
            <dt>Safety</dt>
            <dd>{result.latency_metadata.safety_ms.toFixed(2)} ms</dd>
          </div>
          <div>
            <dt>Retrieval</dt>
            <dd>{result.latency_metadata.retrieval_ms.toFixed(2)} ms</dd>
          </div>
          <div>
            <dt>Composition</dt>
            <dd>{result.latency_metadata.composition_ms.toFixed(2)} ms</dd>
          </div>
          <div>
            <dt>Generation</dt>
            <dd>{result.latency_metadata.generation_ms.toFixed(2)} ms</dd>
          </div>
          <div>
            <dt>Total</dt>
            <dd>{result.latency_metadata.total_ms.toFixed(2)} ms</dd>
          </div>
        </dl>
      </details>
    </div>
  );
}
