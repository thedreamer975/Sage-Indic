import type { KeyboardEvent } from "react";

import type { DemoExample, ServiceStatus } from "../types";

interface QueryWorkspaceProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  examples: DemoExample[];
  status: ServiceStatus | null;
  loading: boolean;
  useLlm: boolean;
  onUseLlmChange: (value: boolean) => void;
  topK: number;
  onTopKChange: (value: number) => void;
}

const behaviorLabel: Record<DemoExample["expected_behavior"], string> = {
  answer: "answerable",
  partial: "partially answerable",
  abstain: "unanswerable",
};

const modalityLabel: Record<string, string> = {
  native: "Native",
  romanized: "Romanized",
  code_mixed: "Code-mixed",
  english: "English",
};

export function QueryWorkspace({
  query,
  onQueryChange,
  onSubmit,
  examples,
  status,
  loading,
  useLlm,
  onUseLlmChange,
  topK,
  onTopKChange,
}: QueryWorkspaceProps) {
  const llmAvailable = Boolean(status?.llm.available);

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <section className="panel query-panel" aria-labelledby="query-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Query workspace</p>
          <h2 id="query-heading">Ask in Telugu, Romanized Telugu, or code-mixed text</h2>
        </div>
      </div>

      <label className="field-label" htmlFor="query-input">
        Your question
      </label>
      <textarea
        id="query-input"
        className="query-input"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={4}
        maxLength={1000}
        placeholder="ఉదా: గోల్కొండ కోట ఎక్కడ ఉంది? / Golconda fort ekkada undi? / Golconda fort location gurinchi cheppu"
        aria-describedby="query-help"
      />
      <p id="query-help" className="help-text">
        The detector identifies script, language, and code-mix. Evidence is retrieved from the
        approved Telugu corpus. Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to submit.
      </p>

      <div className="query-options">
        <div className="option-group">
          <label className="field-label" htmlFor="top-k">
            Evidence passages
          </label>
          <select
            id="top-k"
            className="select"
            value={topK}
            onChange={(event) => onTopKChange(Number(event.target.value))}
          >
            {[4, 6, 8, 10].map((value) => (
              <option key={value} value={value}>
                Top {value}
              </option>
            ))}
          </select>
        </div>

        <div className="llm-option">
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={useLlm}
              disabled={!llmAvailable}
              onChange={(event) => onUseLlmChange(event.target.checked)}
            />
            <span>
              Optional LLM paraphrase
              <small>
                {llmAvailable
                  ? "The model only paraphrases supplied evidence; its draft is rejected if any claim is unsupported."
                  : "LLM provider unavailable. Deterministic evidence-grounded answers remain fully functional."}
              </small>
            </span>
          </label>
        </div>
      </div>

      <button
        type="button"
        className="primary-button"
        onClick={onSubmit}
        disabled={loading || query.trim().length === 0}
      >
        {loading ? (
          <>
            <span className="spinner" aria-hidden="true" />
            Running pipeline…
          </>
        ) : (
          "Submit query"
        )}
      </button>

      <div className="examples">
        <div className="examples-heading">
          <p className="eyebrow">Manually checked examples</p>
          <p className="help-text">
            Clicking an example fills the input. It does not submit a stored answer.
          </p>
        </div>
        <div className="example-list">
          {examples.map((example) => (
            <button
              key={example.id}
              type="button"
              className={`example-card example-${example.expected_behavior}`}
              onClick={() => onQueryChange(example.query)}
              title={example.note}
            >
              <span className="example-topline">
                <span className="example-modality">
                  {modalityLabel[example.modality] ?? example.modality}
                </span>
                <span className="example-behavior">{behaviorLabel[example.expected_behavior]}</span>
              </span>
              <span className="example-query">{example.query}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
