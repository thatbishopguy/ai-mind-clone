"use client";
import { useEffect, useState } from "react";
import { AISuggestion, Analysis, applyAISuggestion, generateAISuggestion, getAISuggestion } from "@/lib/decisions";

export default function AISuggestionPanel({ analysis, onApplied }: { analysis: Analysis; onApplied: (value: Analysis) => void }) {
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    getAISuggestion(analysis.decision_id).then(value => { if (active) { setConfigured(value.configured); setSuggestion(value.suggestion); } })
      .catch(() => { if (active) setError("Could not load AI status. You can still use manual context."); });
    return () => { active = false; };
  }, [analysis]);
  async function generate() {
    setBusy(true); setError("");
    try { setSuggestion(await generateAISuggestion(analysis.decision_id)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not get suggestions."); }
    finally { setBusy(false); }
  }
  async function apply() {
    if (!suggestion) return;
    setBusy(true); setError("");
    try { onApplied(await applyAISuggestion(analysis.decision_id, suggestion.id)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not apply suggestions."); }
    finally { setBusy(false); }
  }
  return <section className="scoringPanel" aria-label="AI suggestions">
    <h3>AI suggestions</h3>
    <p className="muted">Generate a proposed context and candidate options. This sends this decision and its saved context to OpenAI. Your scores, weights, and rules stay unchanged.</p>
    {configured === false && <p role="status">AI access is not configured. Manual context and scoring remain available.</p>}
    <button className="primaryButton" disabled={busy || configured === null} onClick={generate}>{busy ? "Working…" : configured ? "Generate AI suggestions" : "Show manual fallback"}</button>
    {error && <p role="alert">{error}</p>}
    {suggestion && <div className="evaluationResults">
      <strong>{suggestion.source === "openai" ? "AI draft — review required" : "Manual fallback — not an AI result"}</strong>
      <p>{suggestion.notice}</p>
      {suggestion.stale && <p role="alert">Context changed since this preview. Generate a new preview before applying.</p>}
      <p>{suggestion.proposal.summary}</p>
      <div className="scoreCard"><h4>Proposed problem</h4><p>{suggestion.proposal.problem}</p>
        <h4>People</h4><p>{suggestion.proposal.actors.join(", ") || "Not provided"}</p>
        <h4>Constraints</h4><ul>{suggestion.proposal.constraints.map((text,i) => <li key={i}>{text}</li>)}</ul>
        <h4>Reported facts and source quotes</h4>{suggestion.proposal.reported_facts.map((fact,i) => <div key={i}><p>{fact.statement}</p><blockquote>{fact.source_quote}</blockquote></div>)}
        <h4>Unknowns</h4><ul>{suggestion.proposal.unknowns.map((text,i) => <li key={i}>{text}</li>)}</ul>
        <h4>Assumptions</h4><ul>{suggestion.proposal.assumptions.map((text,i) => <li key={i}>{text}</li>)}</ul>
      </div>
      {suggestion.proposal.options.map((option,i) => <article className="scoreCard" key={i}><h4>{option.description}</h4><p>{option.rationale}</p><ul>{option.assumptions.map((text,j) => <li key={j}>{text}</li>)}</ul></article>)}
      {suggestion.source === "openai" && <>
        <p>Applying replaces your structured context and options with this draft. Review and save it before scoring. Previous scoring results will become out of date.</p>
        <button className="primaryButton" disabled={busy || suggestion.stale} onClick={apply}>Apply suggestions for review</button>
      </>}
      <p className="helperText">Source: {suggestion.source} · {suggestion.model ?? "No model used"} · {new Date(suggestion.generated_at).toLocaleString()}</p>
    </div>}
  </section>;
}
