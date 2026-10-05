export type DecisionDraft = {
  situation: string;
  domain: string;
  stakes: string;
  time_pressure: string;
};

export type Decision = DecisionDraft & {
  id: string;
  created_at: string;
  updated_at: string;
};

const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${base}/api/v1/decisions${path}`, { ...init, cache: "no-store" });
  } catch {
    throw new Error("Could not reach the server. Check your connection and try again.");
  }
  if (!response.ok) {
    if (response.status === 404) throw new Error("Decision not found.");
    if (response.status === 409) throw new Error("Saved context changed or needs review. Save reviewed context and reopen scoring.");
    if (response.status === 422) throw new Error("Check the decision fields and try again.");
    throw new Error("The server could not complete the request. Please try again.");
  }
  return response.json() as Promise<T>;
}

export const listDecisions = () => request<Decision[]>("");
export const getDecision = (id: string) => request<Decision>(`/${encodeURIComponent(id)}`);
export const createDecision = (draft: DecisionDraft) => request<Decision>("", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(draft),
});

export type StructuredContext = DecisionDraft & {
  actors: string[];
  problem: string;
  constraints: string[];
  known_facts: string[];
  unknowns: string[];
};
export type CandidateOption = { id: string; description: string };
export type AnalysisDraft = { context: StructuredContext; options: CandidateOption[] };
export type Analysis = AnalysisDraft & { decision_id: string; reviewed: boolean; warnings: string[] };
export const analyzeDecision = (id: string) => request<Analysis>(`/${encodeURIComponent(id)}/analysis`, { method: "POST" });
export const saveAnalysis = (id: string, draft: AnalysisDraft) => request<Analysis>(`/${encodeURIComponent(id)}/analysis`, {
  method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft),
});

export type Criterion = { id: string; name: string; weight: number };
export type Rating = { option_id: string; scores: Record<string, number | null> };
export type ScoringRule = { id: string; name: string; criterion_id: string; comparison: "below" | "above"; threshold: number; effect: "exclude" | "penalize"; penalty: number };
export type EvaluationInput = { analysis_signature: string; criteria: Criterion[]; ratings: Rating[]; rules: ScoringRule[]; preferred_option_id: string | null };
export type OptionScore = { option_id: string; description: string; eligible: boolean | null; base_score: number | null; final_score: number | null; penalty: number; contributions: { criterion: string; rating: number | null; weight: number; points: number | null }[]; rules: { rule: string; condition: string; triggered: boolean | null; effect: string }[] };
export type EvaluationResult = { status: string; recommended_option_id: string | null; tied_option_ids: string[]; options: OptionScore[]; conflicts: string[]; explanation: string };
export type SavedEvaluation = { inputs: EvaluationInput; result: EvaluationResult; stale: boolean };
export const getEvaluation = (id: string) => request<{ analysis_signature: string; evaluation: SavedEvaluation | null }>(`/${encodeURIComponent(id)}/evaluation`);
export const saveEvaluation = (id: string, inputs: EvaluationInput) => request<SavedEvaluation>(`/${encodeURIComponent(id)}/evaluation`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(inputs) });

export type AISuggestion = {
  id: string; decision_id: string; generated_at: string; source: "openai" | "rules_fallback";
  model: string | null; prompt_version: string; notice: string; stale: boolean;
  proposal: { problem: string; actors: string[]; constraints: string[];
    reported_facts: { statement: string; source_quote: string }[]; unknowns: string[];
    options: { description: string; rationale: string; assumptions: string[] }[];
    summary: string; assumptions: string[] };
};
export const getAISuggestion = (id: string) => request<{ configured: boolean; suggestion: AISuggestion | null }>(`/${encodeURIComponent(id)}/ai-suggestion`);
export const generateAISuggestion = (id: string) => request<AISuggestion>(`/${encodeURIComponent(id)}/ai-suggestion`, {method:"POST"});
export const applyAISuggestion = (id: string, suggestionId: string) => request<Analysis>(`/${encodeURIComponent(id)}/ai-suggestion/${encodeURIComponent(suggestionId)}/apply`, {method:"POST"});
