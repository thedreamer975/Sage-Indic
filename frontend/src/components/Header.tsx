import type { ServiceStatus } from "../types";

interface HeaderProps {
  status: ServiceStatus | null;
  statusError: string | null;
}

function Dot({ ok }: { ok: boolean }) {
  return <span className={`dot ${ok ? "dot-ok" : "dot-off"}`} aria-hidden="true" />;
}

export function Header({ status, statusError }: HeaderProps) {
  return (
    <header className="site-header">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          స
        </div>
        <div>
          <div className="brand-name">SAGE-Indic</div>
          <p className="brand-tagline">
            Trustworthy, Telugu-first, evidence-grounded NLP
          </p>
        </div>
      </div>

      <div className="header-status" aria-label="System status">
        {statusError ? (
          <span className="status-chip status-chip-error">Backend unreachable</span>
        ) : status ? (
          <>
            <span className="status-chip">
              <Dot ok={status.corpus.loaded} />
              Corpus {status.corpus.loaded ? `${status.corpus.documents} docs` : "unavailable"}
            </span>
            <span className="status-chip">
              <Dot ok={status.retriever.indexed} />
              Retriever {status.retriever.indexed ? "ready" : "offline"}
            </span>
            <span className="status-chip">
              <Dot ok={status.llm.available} />
              LLM {status.llm.available ? status.llm.model : "offline"}
            </span>
            <span className="status-chip">
              <Dot ok={status.safety.semantic_classifier_available} />
              Safety {status.safety.semantic_classifier_available ? "semantic" : "lexical fallback"}
            </span>
          </>
        ) : (
          <span className="status-chip">Connecting…</span>
        )}
      </div>
    </header>
  );
}
