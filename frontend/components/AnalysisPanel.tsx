"use client";

import AISuggestionPanel from "@/components/AISuggestionPanel";
import EvaluationPanel from "@/components/EvaluationPanel";
import { useState } from "react";
import { Analysis, analyzeDecision, saveAnalysis } from "@/lib/decisions";

const fields = [
  ["actors", "People involved"], ["constraints", "Constraints"],
  ["known_facts", "Reported facts"], ["unknowns", "Unknowns"],
] as const;
type ListField = (typeof fields)[number][0];

export default function AnalysisPanel({ decisionId }: { decisionId: string }) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [lists, setLists] = useState<Record<ListField, string>>({ actors: "", constraints: "", known_facts: "", unknowns: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState("");

  function accept(value: Analysis) {
    setAnalysis(value); setDirty(false);
    setLists({ actors: value.context.actors.join("\n"), constraints: value.context.constraints.join("\n"),
      known_facts: value.context.known_facts.join("\n"), unknowns: value.context.unknowns.join("\n") });
  }

  async function load() {
    setBusy(true); setError("");
    try { accept(await analyzeDecision(decisionId)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not structure the decision."); }
    finally { setBusy(false); }
  }

  async function save() {
    if (!analysis) return;
    setBusy(true); setError(""); setMessage("");
    const context = { ...analysis.context };
    for (const [key] of fields) context[key] = lists[key].split("\n").map(line => line.trim()).filter(Boolean);
    try {
      accept(await saveAnalysis(decisionId, { context, options: analysis.options }));
      setMessage("Structured context saved.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save context."); }
    finally { setBusy(false); }
  }

  return <section className="panel">
    <h3>Structured context</h3>
    {!analysis && <>
      <p className="muted">Create a draft or reopen your saved context. Review the details and add the options you are considering.</p>
      <p className="helperText">For precise extraction, use one labeled line per detail in your situation: Problem:, Actor:, Fact:, Constraint:, Unknown:, or Option:. Unlabeled prose stays in the problem for your review.</p>
      <button className="primaryButton" disabled={busy} onClick={load}>{busy ? "Opening…" : "Open structured context"}</button>
    </>}
    {error && <p role="alert">{error} Your edits remain on this screen.</p>}
    {analysis && <fieldset className="analysisFields" disabled={busy} onChange={() => { setMessage(""); setDirty(true); }}>
      <legend>{analysis.reviewed ? "Previously reviewed context" : "Draft for your review"}</legend>
      <ul className="muted">{analysis.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
      <label><span className="fieldLabel">Problem or decision</span>
        <textarea value={analysis.context.problem} rows={4} onChange={e => setAnalysis({ ...analysis, context: { ...analysis.context, problem: e.target.value } })} />
      </label>
      {fields.map(([key, label]) => <label key={key}><span className="fieldLabel">{label} — one per line</span>
        <textarea rows={3} value={lists[key]} placeholder="Not provided — add if known" onChange={e => setLists({ ...lists, [key]: e.target.value })} />
      </label>)}
      <h4>Options to consider</h4>
      <p className="helperText">These are your candidate choices. No scoring or recommendation has been applied.</p>
      {analysis.options.length === 0 && <p>No options recorded yet.</p>}
      {analysis.options.map((option, index) => <div className="optionEditor" key={option.id}>
        <label><span className="fieldLabel">Option {index + 1}</span><textarea rows={2} value={option.description}
          onChange={e => setAnalysis({ ...analysis, options: analysis.options.map(item => item.id === option.id ? { ...item, description: e.target.value } : item) })} /></label>
        <button className="primaryButton" onClick={() => { setDirty(true); setAnalysis({ ...analysis, options: analysis.options.filter(item => item.id !== option.id) }); }}>Remove option {index + 1}</button>
      </div>)}
      <button className="primaryButton" onClick={() => { setDirty(true); setAnalysis({ ...analysis, options: [...analysis.options, { id: crypto.randomUUID(), description: "" }] }); }}>Add option</button>
      <button className="primaryButton" disabled={busy || !analysis.context.problem.trim() || analysis.options.some(option => !option.description.trim())} onClick={save}>{busy ? "Saving…" : "Save reviewed context"}</button>
    </fieldset>}
    {message && <p role="status">{message}</p>}
    {analysis && !dirty && <AISuggestionPanel key={"ai-" + JSON.stringify(analysis)} analysis={analysis} onApplied={accept} />}
    {analysis && !dirty && <EvaluationPanel key={JSON.stringify(analysis)} analysis={analysis} />}
    {analysis && dirty && <p>Save your context changes before opening scoring.</p>}
  </section>;
}
