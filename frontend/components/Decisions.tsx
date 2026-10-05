"use client";

import AnalysisPanel from "@/components/AnalysisPanel";
import { useEffect, useState } from "react";
import { Decision, getDecision, listDecisions } from "@/lib/decisions";

export default function Decisions({ selectedId, onSelect }: {
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selected, setSelected] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setSelected(null);
    async function load() {
      try {
        if (selectedId) {
          const decision = await getDecision(selectedId);
          if (active) setSelected(decision);
        } else {
          const records = await listDecisions();
          if (active) setDecisions(records);
        }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Could not load decisions.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [selectedId, attempt]);

  return (
    <div className="pageStack">
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow dark">SAVED CONTEXT</p>
          <h2>{selectedId ? "Saved Decision" : "Decisions"}</h2>
          <p className="lede">Reopen your saved situations and decision context.</p>
        </div>
      </header>
      {selectedId && <button className="primaryButton backButton" onClick={() => onSelect(null)}>Back to decisions</button>}
      {loading && <p role="status">Loading decisions…</p>}
      {!loading && error && <section className="panel">
        <p role="alert">{error}</p>
        <button className="primaryButton" onClick={() => setAttempt((value) => value + 1)}>Try again</button>
      </section>}
      {!loading && !error && selected && <article className="panel">
        <h3>Situation</h3>
        <p className="savedSituation">{selected.situation}</p>
        <dl className="contextList">
          <div><dt>Domain</dt><dd>{selected.domain}</dd></div>
          <div><dt>Stakes</dt><dd>{selected.stakes}</dd></div>
          <div><dt>Time pressure</dt><dd>{selected.time_pressure}</dd></div>
          <div><dt>Created</dt><dd>{new Date(selected.created_at).toLocaleString()}</dd></div>
          <div><dt>Updated</dt><dd>{new Date(selected.updated_at).toLocaleString()}</dd></div>
        </dl>
      </article>}
      {!loading && !error && selected && <AnalysisPanel key={selected.id} decisionId={selected.id} />}
      {!loading && !error && !selectedId && (decisions.length === 0 ?
        <section className="panel emptyState"><strong>No saved decisions yet</strong><p>Use New Decision to save your first situation.</p></section> :
        <ul className="decisionList">{decisions.map((decision) => <li key={decision.id}>
          <button className="panel decisionRow" onClick={() => onSelect(decision.id)}>
            <strong>{decision.situation}</strong>
            <span>{decision.domain} · {decision.stakes} stakes · {new Date(decision.created_at).toLocaleString()}</span>
            <span>Open decision →</span>
          </button>
        </li>)}</ul>)}
    </div>
  );
}
