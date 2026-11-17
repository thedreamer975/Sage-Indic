import { useEffect, useState } from "react";

import { fetchCorpus, fetchExamples, fetchStatus, submitQuery } from "./api";
import { AnswerPanel } from "./components/AnswerPanel";
import { EvidencePanel } from "./components/EvidencePanel";
import { Header } from "./components/Header";
import { QueryWorkspace } from "./components/QueryWorkspace";
import { StatusPanel } from "./components/StatusPanel";
import { VerificationPanel } from "./components/VerificationPanel";
import type {
  AnswerResponse,
  CorpusInfo,
  DemoExample,
  ServiceStatus,
} from "./types";

type Tab = "evidence" | "verification";

export default function App() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [examples, setExamples] = useState<DemoExample[]>([]);
  const [corpus, setCorpus] = useState<CorpusInfo | null>(null);

  const [query, setQuery] = useState("గోల్కొండ కోట ఎక్కడ ఉంది?");
  const [useLlm, setUseLlm] = useState(false);
  const [topK, setTopK] = useState(8);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnswerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("evidence");

  useEffect(() => {
    let active = true;
    Promise.all([fetchStatus(), fetchExamples(), fetchCorpus()])
      .then(([statusPayload, examplesPayload, corpusPayload]) => {
        if (!active) return;
        setStatus(statusPayload);
        setExamples(examplesPayload.examples);
        setCorpus(corpusPayload);
        setStatusError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setStatusError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit() {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const response = await submitQuery(trimmed, useLlm, topK);
      setResult(response);
      setTab("evidence");
      if (window.innerWidth <= 1080) {
        requestAnimationFrame(() => {
          document
            .getElementById("answer-region")
            ?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      }
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Header status={status} statusError={statusError} />

      <main className="layout">
        <div className="left-column">
          {statusError && (
            <div className="callout callout-danger">
              <strong>Backend connection issue</strong>
              <p>{statusError}</p>
              <p className="help-text">
                Start the API with <code>uvicorn sage_indic.api.app:app --port 8000</code>.
              </p>
            </div>
          )}
          <QueryWorkspace
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleSubmit}
            examples={examples}
            status={status}
            loading={loading}
            useLlm={useLlm}
            onUseLlmChange={setUseLlm}
            topK={topK}
            onTopKChange={setTopK}
          />
          <StatusPanel status={status} corpus={corpus} />
        </div>

        <div className="right-column">
          <div id="answer-region">
            <AnswerPanel result={result} error={error} loading={loading} />
          </div>

          {result && (
            <section className="panel results-panel" aria-label="Evidence and verification details">
              <div className="tab-list" role="tablist" aria-label="Result details">
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "evidence"}
                  className={`tab-button ${tab === "evidence" ? "tab-active" : ""}`}
                  onClick={() => setTab("evidence")}
                >
                  Evidence
                  <span className="tab-count">{result.retrieved_evidence.length}</span>
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "verification"}
                  className={`tab-button ${tab === "verification" ? "tab-active" : ""}`}
                  onClick={() => setTab("verification")}
                >
                  Verification
                  <span className="tab-count">
                    {result.verification_summary.total_claims}
                  </span>
                </button>
              </div>

              {tab === "evidence" ? (
                <EvidencePanel evidence={result.retrieved_evidence} />
              ) : (
                <VerificationPanel result={result} />
              )}
            </section>
          )}
        </div>
      </main>

      <footer className="site-footer">
        <p>
          Research prototype. Answers are grounded in the approved Telugu corpus; retrieval is not
          treated as proof of factuality, and claim verification is deterministic/heuristic rather
          than a calibrated NLI model.
        </p>
        <p>
          Demo queries are illustrative, not a benchmark. See <code>HOW_TO_RUN.md</code> and{" "}
          <code>OPEN_ISSUES.md</code> for setup and known limitations.
        </p>
      </footer>
    </div>
  );
}
