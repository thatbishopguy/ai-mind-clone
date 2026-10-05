"use client";
import { useState } from "react";
import { Analysis, EvaluationInput, EvaluationResult, ScoringRule, getEvaluation, saveEvaluation } from "@/lib/decisions";

export default function EvaluationPanel({ analysis }: { analysis: Analysis }) {
  const [inputs, setInputs] = useState<EvaluationInput | null>(null);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function update(value: EvaluationInput) { setInputs(value); setResult(null); setNotice("Changes are not evaluated or saved yet."); }
  async function open() {
    setBusy(true); setError("");
    try {
      const saved = await getEvaluation(analysis.decision_id);
      if (saved.evaluation && !saved.evaluation.stale) {
        setInputs(saved.evaluation.inputs); setResult(saved.evaluation.result); setNotice("Saved evaluation loaded.");
      } else {
        setInputs({ analysis_signature: saved.analysis_signature, criteria: [], rules: [], preferred_option_id: null,
          ratings: analysis.options.map(option => ({ option_id: option.id, scores: {} })) });
        setResult(null);
        setNotice(saved.evaluation?.stale ? "Context changed. Previous results are out of date; enter a fresh evaluation." : "Choose your criteria and weights. No personal weights have been assumed.");
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load evaluation."); }
    finally { setBusy(false); }
  }
  async function score() {
    if (!inputs) return;
    setBusy(true); setError("");
    try { const saved = await saveEvaluation(analysis.decision_id, inputs); setResult(saved.result); setNotice("Evaluation saved."); }
    catch (cause) { setResult(null); setError(cause instanceof Error ? cause.message : "Could not evaluate."); }
    finally { setBusy(false); }
  }
  function ruleChange(index: number, change: Partial<ScoringRule>) {
    if (inputs) update({ ...inputs, rules: inputs.rules.map((rule, i) => i === index ? { ...rule, ...change } : rule) });
  }
  const invalid = inputs && (inputs.criteria.some(c => !c.name.trim()) || inputs.rules.some(r => !r.name.trim() || (r.effect === "penalize" && r.penalty <= 0)));
  return <section className="scoringPanel">
    <h3>Rules and scoring</h3>
    <p className="muted">Rate how well each option meets your criteria: 0 is worst, 10 is best. Weights express importance; 0 ignores a criterion in the weighted score. Leave unknown ratings blank.</p>
    {!inputs && <button className="primaryButton" disabled={busy || !analysis.reviewed || analysis.options.length < 2} onClick={open}>{busy ? "Opening…" : "Open scoring"}</button>}
    {(!analysis.reviewed || analysis.options.length < 2) && <p>Save reviewed context with at least two options first.</p>}
    {error && <div role="alert"><p>{error}</p><button className="primaryButton" disabled={busy} onClick={open}>Reload saved evaluation</button></div>}
    {notice && <p role="status">{notice}</p>}
    {inputs && <fieldset className="analysisFields" disabled={busy}>
      <legend>Criteria and weights</legend>
      {inputs.criteria.map((criterion, index) => <div className="scoreCard" key={criterion.id}>
        <label>Criterion {index + 1}<input aria-label={`Criterion ${index + 1}`} value={criterion.name} onChange={e => update({ ...inputs, criteria: inputs.criteria.map(c => c.id === criterion.id ? { ...c, name: e.target.value } : c) })} /></label>
        <label>Weight (0–10)<input aria-label={`Weight ${index + 1}`} type="number" min={0} max={10} step="any" value={criterion.weight} onChange={e => update({ ...inputs, criteria: inputs.criteria.map(c => c.id === criterion.id ? { ...c, weight: Number(e.target.value) } : c) })} /></label>
        <button className="primaryButton" onClick={() => update({ ...inputs, criteria: inputs.criteria.filter(c => c.id !== criterion.id), rules: inputs.rules.filter(r => r.criterion_id !== criterion.id), ratings: inputs.ratings.map(r => ({ ...r, scores: Object.fromEntries(Object.entries(r.scores).filter(([key]) => key !== criterion.id)) })) })}>Remove criterion {index + 1} and its rules</button>
      </div>)}
      <button className="primaryButton" onClick={() => { const id = crypto.randomUUID(); update({ ...inputs, criteria: [...inputs.criteria, { id, name: "", weight: 0 }], ratings: inputs.ratings.map(r => ({ ...r, scores: { ...r.scores, [id]: null } })) }); }}>Add criterion</button>
      <h4>Option ratings</h4>
      {analysis.options.map((option, index) => <div className="scoreCard" key={option.id}><strong>{option.description}</strong>
        {inputs.criteria.map(criterion => <label key={criterion.id}>{criterion.name || "Unnamed criterion"} (0–10)
          <input aria-label={`Rating option ${index + 1} ${criterion.name}`} type="number" min={0} max={10} step="any" placeholder="Unknown" value={inputs.ratings.find(r => r.option_id === option.id)?.scores[criterion.id] ?? ""}
            onChange={e => update({ ...inputs, ratings: inputs.ratings.map(r => r.option_id === option.id ? { ...r, scores: { ...r.scores, [criterion.id]: e.target.value === "" ? null : Number(e.target.value) } } : r) })} />
        </label>)}
      </div>)}
      <h4>Rules</h4><p className="helperText">Rules trigger strictly below or above a rating. A hard exclusion always overrides the score. A soft penalty subtracts points from the 0–100 score.</p>
      {inputs.rules.map((rule, index) => <div className="scoreCard" key={rule.id}>
        <label>Rule {index + 1}<input aria-label={`Rule ${index + 1}`} value={rule.name} onChange={e => ruleChange(index, { name: e.target.value })} /></label>
        <label>Criterion<select aria-label={`Rule criterion ${index + 1}`} value={rule.criterion_id} onChange={e => ruleChange(index, { criterion_id: e.target.value })}>{inputs.criteria.map(c => <option value={c.id} key={c.id}>{c.name || "Unnamed criterion"}</option>)}</select></label>
        <label>Trigger<select aria-label={`Rule comparison ${index + 1}`} value={rule.comparison} onChange={e => ruleChange(index, { comparison: e.target.value as "below" | "above" })}><option value="below">Rating below</option><option value="above">Rating above</option></select></label>
        <label>Threshold<input aria-label={`Rule threshold ${index + 1}`} type="number" min={0} max={10} step="any" value={rule.threshold} onChange={e => ruleChange(index, { threshold: Number(e.target.value) })} /></label>
        <label>Effect<select aria-label={`Rule effect ${index + 1}`} value={rule.effect} onChange={e => ruleChange(index, { effect: e.target.value as "exclude" | "penalize", penalty: 0 })}><option value="exclude">Exclude option</option><option value="penalize">Subtract points</option></select></label>
        {rule.effect === "penalize" && <label>Penalty (1–100)<input aria-label={`Rule penalty ${index + 1}`} type="number" min={1} max={100} step="any" value={rule.penalty} onChange={e => ruleChange(index, { penalty: Number(e.target.value) })} /></label>}
        <button className="primaryButton" onClick={() => update({ ...inputs, rules: inputs.rules.filter(r => r.id !== rule.id) })}>Remove rule {index + 1}</button>
      </div>)}
      <button className="primaryButton" disabled={!inputs.criteria.length} onClick={() => update({ ...inputs, rules: [...inputs.rules, { id: crypto.randomUUID(), name: "", criterion_id: inputs.criteria[0].id, comparison: "below", threshold: 0, effect: "exclude", penalty: 0 }] })}>Add rule</button>
      <label>Your preferred option (optional)<select aria-label="Preferred option" value={inputs.preferred_option_id ?? ""} onChange={e => update({ ...inputs, preferred_option_id: e.target.value || null })}><option value="">No preference stated</option>{analysis.options.map(o => <option value={o.id} key={o.id}>{o.description}</option>)}</select></label>
      <button className="primaryButton" disabled={busy || !!invalid} onClick={score}>{busy ? "Evaluating…" : "Evaluate and save"}</button>
    </fieldset>}
    {result && <section aria-label="Evaluation results" className="evaluationResults">
      <h4>{result.status === "recommended" ? "Highest-scoring eligible option" : result.status === "tie" ? "Tied options" : result.status === "incomplete" ? "More information needed" : "No eligible options"}</h4>
      <p>{result.explanation}</p>
      {result.recommended_option_id && <strong>{result.options.find(o => o.option_id === result.recommended_option_id)?.description}</strong>}
      {result.conflicts.map((text, i) => <p role="status" key={i}>{text}</p>)}
      {result.options.map(option => <article className="scoreCard" key={option.option_id}>
        <h4>{option.description}</h4>
        <p>{option.eligible === false ? "Excluded" : option.eligible === null ? "Eligibility unresolved" : "Eligible"} · Score: {option.final_score === null ? "Incomplete" : option.final_score.toFixed(2)} / 100</p>
        <p>Base: {option.base_score?.toFixed(2) ?? "Incomplete"} · Penalties: {option.penalty.toFixed(2)}. Scores are floored at zero.</p>
        <ul>{option.contributions.map((c, i) => <li key={i}>{c.criterion}: rating {c.rating ?? "unknown"}, weight {c.weight} → {c.points?.toFixed(2) ?? "unknown"} points</li>)}</ul>
        <ul>{option.rules.map((r, i) => <li key={i}>{r.rule}: {r.condition} → {r.triggered === null ? "Unknown" : r.triggered ? r.effect : "Not triggered"}</li>)}</ul>
      </article>)}
    </section>}
  </section>;
}
