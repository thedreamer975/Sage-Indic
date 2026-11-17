import type { CorpusInfo, ServiceStatus } from "../types";

interface StatusPanelProps {
  status: ServiceStatus | null;
  corpus: CorpusInfo | null;
}

export function StatusPanel({ status, corpus }: StatusPanelProps) {
  if (!status) {
    return (
      <section className="panel status-panel">
        <p className="eyebrow">System status</p>
        <p className="help-text">Waiting for backend status…</p>
      </section>
    );
  }

  return (
    <section className="panel status-panel" aria-labelledby="status-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">System status</p>
          <h2 id="status-heading">Runtime and evidence corpus</h2>
        </div>
        <span className="version-chip">v{status.version}</span>
      </div>

      <dl className="status-grid">
        <div>
          <dt>Retriever</dt>
          <dd>
            {status.retriever.indexed ? "Indexed" : "Not indexed"} · {status.retriever.method}
          </dd>
        </div>
        <div>
          <dt>Corpus</dt>
          <dd>
            {status.corpus.documents} documents · {status.corpus.chunks} chunks ·{" "}
            {status.corpus.version}
          </dd>
        </div>
        <div>
          <dt>Safety</dt>
          <dd>
            {status.safety.method}
            {status.safety.semantic_classifier_available
              ? ""
              : " (semantic model unavailable; context-aware lexical fallback)"}
          </dd>
        </div>
        <div>
          <dt>LLM provider</dt>
          <dd>
            {status.llm.available ? "Available" : "Unavailable"} · {status.llm.base_url} ·{" "}
            {status.llm.model}
            {status.llm.error ? ` · ${status.llm.error}` : ""}
          </dd>
        </div>
        <div>
          <dt>Default answer path</dt>
          <dd>
            Deterministic evidence-grounded composition
            {status.deterministic_fallback ? " (always available)" : ""}
          </dd>
        </div>
      </dl>

      {corpus && (
        <details className="corpus-details">
          <summary>Evidence sources and licenses ({corpus.document_count})</summary>
          <div className="corpus-list">
            {corpus.documents.map((doc) => (
              <article className="corpus-card" key={doc.document_id}>
                <div className="corpus-topline">
                  <span className="data-chip">{doc.document_id}</span>
                  <span className="data-chip">{doc.license_name}</span>
                  <span className="data-chip">{doc.chunk_count} chunks</span>
                </div>
                <h4 lang="te">{doc.title}</h4>
                <p className="help-text">
                  {doc.publisher} · {doc.license_status}
                  {doc.source_revision ? ` · ${doc.source_revision}` : ""}
                </p>
                {doc.source_url && (
                  <a href={doc.source_url} target="_blank" rel="noreferrer">
                    Source revision
                  </a>
                )}
              </article>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}
