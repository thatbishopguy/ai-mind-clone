from datetime import UTC, datetime
from uuid import uuid4

from app.models.analysis import Analysis
from app.models.decision import Decision
from app.models.evaluation import analysis_signature
from app.models.suggestion import ProposedContext, ProposedOption, ReportedFact, Suggestion
from app.providers.prompts import PROMPT_VERSION
from app.providers.reasoning import ProviderFailure, ReasoningProvider


def create_suggestion(decision: Decision, analysis: Analysis,
                      provider: ReasoningProvider | None, model: str) -> Suggestion:
    source = "openai"
    notice = "AI suggestions may be wrong. Review the source quotes and assumptions before applying."
    try:
        if provider is None:
            raise ProviderFailure("AI access is not configured.")
        proposal = provider.suggest(decision, analysis)
    except ProviderFailure as exc:
        source = "rules_fallback"
        notice = f"{exc} Showing existing structured context only; this is not an AI-generated result."
        proposal = ProposedContext(
            problem=analysis.context.problem, actors=analysis.context.actors,
            constraints=analysis.context.constraints, unknowns=analysis.context.unknowns,
            reported_facts=[ReportedFact(statement=fact, source_quote=fact)
                            for fact in analysis.context.known_facts],
            options=[ProposedOption(description=o.description, rationale="Existing candidate option.",
                                    assumptions=[]) for o in analysis.options],
            summary="Existing context retained for manual review.", assumptions=[],
        )
    return Suggestion(id=uuid4(), decision_id=decision.id,
        base_signature=analysis_signature(analysis), generated_at=datetime.now(UTC),
        source=source, model=model if source == "openai" else None,
        prompt_version=PROMPT_VERSION, notice=notice, proposal=proposal)
