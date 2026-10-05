from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.decision_engine.scoring import evaluate
from app.decision_engine.structure import structure_decision
from app.decision_engine.suggestions import create_suggestion
from app.models.analysis import Analysis, AnalysisDraft, Context, Option
from app.models.decision import Decision, DecisionCreate
from app.models.evaluation import (
    EvaluationEnvelope,
    EvaluationInput,
    SavedEvaluation,
    analysis_signature,
)
from app.models.suggestion import AIProvenance, AISuggestionStatus, Suggestion
from app.repositories.decisions import DecisionRepository

router = APIRouter(prefix="/decisions", tags=["decisions"])


def get_repository(request: Request, response: Response) -> DecisionRepository:
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.decisions


Repository = Annotated[DecisionRepository, Depends(get_repository)]


@router.post("", response_model=Decision, status_code=201)
def create_decision(draft: DecisionCreate, repository: Repository) -> Decision:
    return repository.create(draft)


@router.get("", response_model=list[Decision])
def list_decisions(repository: Repository) -> list[Decision]:
    return repository.list()


@router.get("/{decision_id}", response_model=Decision)
def get_decision(decision_id: UUID, repository: Repository) -> Decision:
    decision = repository.get(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{decision_id}/analysis", response_model=Analysis)
def analyze_decision(decision_id: UUID, repository: Repository) -> Analysis:
    decision = get_decision(decision_id, repository)
    existing = repository.get_analysis(decision_id)
    if existing:
        return existing
    return repository.save_analysis(structure_decision(decision), create_only=True)


@router.get("/{decision_id}/analysis", response_model=Analysis)
def get_analysis(decision_id: UUID, repository: Repository) -> Analysis:
    get_decision(decision_id, repository)
    analysis = repository.get_analysis(decision_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Decision has no structured context yet")
    return analysis


@router.put("/{decision_id}/analysis", response_model=Analysis)
def save_analysis(decision_id: UUID, draft: AnalysisDraft, repository: Repository) -> Analysis:
    decision = get_decision(decision_id, repository)
    original = decision.model_dump(include={"situation", "domain", "stakes", "time_pressure"})
    if any(getattr(draft.context, key) != value for key, value in original.items()):
        raise HTTPException(status_code=422, detail="Original decision fields cannot change here")
    current = repository.get_analysis(decision_id)
    analysis = Analysis(**draft.model_dump(), decision_id=decision_id, reviewed=True,
                        ai_provenance=current.ai_provenance if current else None,
                        warnings=["Reviewed context reflects user statements, not independently verified facts."])
    return repository.save_analysis(analysis)


@router.get("/{decision_id}/evaluation", response_model=EvaluationEnvelope)
def get_evaluation(decision_id: UUID, repository: Repository) -> EvaluationEnvelope:
    analysis = get_analysis(decision_id, repository)
    saved = repository.get_evaluation(decision_id)
    signature = analysis_signature(analysis)
    if saved:
        saved.stale = saved.inputs.analysis_signature != signature
    return EvaluationEnvelope(analysis_signature=signature, evaluation=saved)


@router.put("/{decision_id}/evaluation", response_model=SavedEvaluation)
def score_decision(decision_id: UUID, inputs: EvaluationInput, repository: Repository) -> SavedEvaluation:
    analysis = get_analysis(decision_id, repository)
    if not analysis.reviewed:
        raise HTTPException(status_code=409, detail="Review and save structured context first")
    if inputs.analysis_signature != analysis_signature(analysis):
        raise HTTPException(status_code=409, detail="Context changed; reopen scoring before evaluating")
    if {r.option_id for r in inputs.ratings} != {o.id for o in analysis.options}:
        raise HTTPException(status_code=422, detail="Ratings must match the saved options exactly")
    saved = SavedEvaluation(inputs=inputs, result=evaluate(analysis, inputs))
    if not repository.save_evaluation(decision_id, saved):
        raise HTTPException(status_code=409, detail="Context changed while evaluating; reopen scoring")
    return saved


@router.get("/{decision_id}/ai-suggestion", response_model=AISuggestionStatus)
def get_ai_suggestion(decision_id: UUID, request: Request, repository: Repository) -> AISuggestionStatus:
    analysis = get_analysis(decision_id, repository)
    suggestion = repository.get_suggestion(decision_id)
    if suggestion:
        suggestion.stale = suggestion.base_signature != analysis_signature(analysis)
    return AISuggestionStatus(configured=request.app.state.reasoning is not None, suggestion=suggestion)


@router.post("/{decision_id}/ai-suggestion", response_model=Suggestion)
def generate_ai_suggestion(decision_id: UUID, request: Request, repository: Repository) -> Suggestion:
    decision = get_decision(decision_id, repository)
    analysis = get_analysis(decision_id, repository)
    suggestion = create_suggestion(decision, analysis, request.app.state.reasoning, request.app.state.ai_model)
    repository.save_suggestion(suggestion)
    suggestion.stale = suggestion.base_signature != analysis_signature(get_analysis(decision_id, repository))
    return suggestion


@router.post("/{decision_id}/ai-suggestion/{suggestion_id}/apply", response_model=Analysis)
def apply_ai_suggestion(decision_id: UUID, suggestion_id: UUID, repository: Repository) -> Analysis:
    current = get_analysis(decision_id, repository)
    suggestion = repository.get_suggestion(decision_id, suggestion_id)
    if not suggestion or suggestion.id != suggestion_id:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion.source != "openai":
        raise HTTPException(status_code=409, detail="Fallback retains current context; no AI draft to apply")
    proposal = suggestion.proposal
    context = Context(**current.context.model_dump(exclude={"problem", "actors", "constraints", "known_facts", "unknowns"}),
        problem=proposal.problem, actors=proposal.actors, constraints=proposal.constraints,
        known_facts=[f.statement for f in proposal.reported_facts], unknowns=proposal.unknowns)
    existing_ids = {o.description: o.id for o in current.options}
    analysis = Analysis(decision_id=decision_id, context=context,
        options=[Option(id=existing_ids.get(o.description, uuid4()), description=o.description)
                 for o in proposal.options],
        reviewed=False,
        ai_provenance=AIProvenance(suggestion_id=suggestion.id, source=suggestion.source,
            model=suggestion.model, generated_at=suggestion.generated_at, prompt_version=suggestion.prompt_version),
        warnings=["AI draft applied. Review and save context before scoring.",
                  "Reported facts are unverified user claims."] + proposal.assumptions)
    if not repository.apply_suggestion(decision_id, suggestion_id, analysis):
        raise HTTPException(status_code=409, detail="Context or suggestion changed; generate a new preview")
    return analysis


@router.get("/{decision_id}/ai-suggestion/{suggestion_id}", response_model=Suggestion)
def get_saved_ai_suggestion(decision_id: UUID, suggestion_id: UUID, repository: Repository) -> Suggestion:
    analysis = get_analysis(decision_id, repository)
    suggestion = repository.get_suggestion(decision_id, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.stale = suggestion.base_signature != analysis_signature(analysis)
    return suggestion
