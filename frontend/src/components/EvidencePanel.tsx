import type { RetrievedEvidence } from "../types";

interface EvidencePanelProps {
  evidence: RetrievedEvidence[];
}

function EvidenceCard({ item }: { item: RetrievedEvidence }) {
  const preview = item.text.length > 190 ? `${item.text.slice(0, 190).trim()}…` : item.text;
  return (
    <article className={`evidence-card ${item.used_in_answer ? "evidence-used" : ""}`}>
      <div className="evidence-topline">
        <span className="rank-chip">#{item.rank}</span>
        <span className="score-chip" title="Actual BM25 retriever score; not a calibrated probability">
          BM25 {item.score.toFixed(3)}
        </span>
        {item.used_in_answer && <span className="used-chip">cited in answer</span>}
        {item.selected && !item.used_in_answer && <span className="selected-chip">selected for verification</span>}
      </div>

      <h4>{item.title || "Untitled source"}</h4>
      <p className="evidence-source">
        {item.document_id} · {item.chunk_id}
      </p>
      <p className="evidence-source">
        {item.source_name} · {item.license_name} · chars {item.char_start}–{item.char_end}
      </p>

      <p className="evidence-text" lang="te">
        {preview}
      </p>

      <details>
        <summary>Show full retrieved passage</summary>
        <p className="evidence-text" lang="te">
          {item.text}
        </p>
        <p className="hash-line">
          SHA-256 {item.content_hash.digest.slice(0, 16)}… (untrusted evidence data)
        </p>
      </details>

      {item.source_url && (
        <a href={item.source_url} target="_blank" rel="noreferrer">
          Source revision
        </a>
      )}
    </article>
  );
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
  return (
    <div className="evidence-panel">
      <div className="section-heading">
        <h3>Retrieved evidence</h3>
        <p>
          {evidence.length} passages returned by the retriever. Text is untrusted evidence data,
          never instructions.
        </p>
      </div>
      {evidence.length === 0 ? (
        <p className="empty-inline">No passages were retrieved for this query.</p>
      ) : (
        <div className="evidence-list">
          {evidence.map((item) => (
            <EvidenceCard key={item.evidence_id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
