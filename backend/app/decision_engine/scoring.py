"""Deterministic, user-configured scoring. No inferred personal priorities."""
import math

from app.models.analysis import Analysis
from app.models.evaluation import (
    Contribution,
    EvaluationInput,
    EvaluationResult,
    OptionScore,
    RuleTrace,
)


def evaluate(analysis: Analysis, inputs: EvaluationInput) -> EvaluationResult:
    total_weight = sum(c.weight for c in inputs.criteria)
    ratings = {r.option_id: r.scores for r in inputs.ratings}
    criterion_names = {c.id: c.name for c in inputs.criteria}
    results = []
    conflicts = []
    for option in analysis.options:
        scores = ratings[option.id]
        contributions = [Contribution(
            criterion=c.name, rating=scores[c.id], weight=c.weight,
            points=(0 if c.weight == 0 else scores[c.id] * c.weight * 10 / total_weight)
            if total_weight and (scores[c.id] is not None or c.weight == 0) else None,
        ) for c in inputs.criteria]
        complete = total_weight > 0 and all(c.points is not None for c in contributions)
        base = sum(c.points for c in contributions if c.points is not None) if complete else None
        traces = []
        excluded = False
        unresolved = False
        penalty = 0.0
        for rule in inputs.rules:
            rating = scores[rule.criterion_id]
            triggered = None if rating is None else (
                rating < rule.threshold if rule.comparison == "below" else rating > rule.threshold
            )
            traces.append(RuleTrace(rule=rule.name,
                condition=f"{criterion_names[rule.criterion_id]} {rule.comparison} {rule.threshold:g}",
                triggered=triggered,
                effect="Exclude option" if rule.effect == "exclude" else f"Subtract {rule.penalty:g} points"))
            if triggered is None:
                unresolved = True
            elif triggered and rule.effect == "exclude":
                excluded = True
            elif triggered:
                penalty += rule.penalty
        eligible = False if excluded else None if unresolved else True
        final = max(0.0, base - penalty) if base is not None and not unresolved else None
        results.append(OptionScore(option_id=option.id, description=option.description,
            eligible=eligible, base_score=base, final_score=final, penalty=penalty,
            contributions=contributions, rules=traces))
        if excluded and inputs.preferred_option_id == option.id:
            conflicts.append("Your preferred option is excluded by a hard rule.")
    possible = [r for r in results if r.eligible is not False]
    recommended = None
    tied = []
    if results and not possible:
        status = "no_eligible_options"
        explanation = "Every option is excluded by a hard rule. No recommendation is available."
    elif len(results) < 2 or not total_weight or any(
        r.eligible is None or r.final_score is None for r in possible
    ):
        status = "incomplete"
        explanation = "Add at least two options, a positive criterion weight, and missing ratings before comparing. Unknown ratings are not treated as zero."
    else:
        top = max(r.final_score for r in possible)
        tied = [r.option_id for r in possible if math.isclose(r.final_score, top, abs_tol=1e-9)]
        if len(tied) > 1:
            status = "tie"
            explanation = "Top eligible options are tied. The engine does not choose an arbitrary winner."
        else:
            status = "recommended"
            recommended = tied[0]
            tied = []
            explanation = "Highest eligible score under your entered weights, ratings, and rules. This is not a prediction of your behavior or a confidence estimate."
        if inputs.preferred_option_id is not None and inputs.preferred_option_id not in (
            tied or [recommended]
        ):
            conflicts.append("Your stated preference differs from the highest-scoring eligible option(s).")
    return EvaluationResult(status=status, recommended_option_id=recommended,
        tied_option_ids=tied, options=results, conflicts=conflicts, explanation=explanation)
