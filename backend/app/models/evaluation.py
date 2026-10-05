import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.analysis import Analysis, Text

Number = Annotated[float, Field(ge=0, le=10, allow_inf_nan=False)]


def analysis_signature(analysis: Analysis) -> str:
    return hashlib.sha256(json.dumps(analysis.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Criterion(StrictModel):
    id: UUID
    name: Text
    weight: Number


class Rating(StrictModel):
    option_id: UUID
    scores: dict[UUID, Number | None]


class Rule(StrictModel):
    id: UUID
    name: Text
    criterion_id: UUID
    comparison: Literal["below", "above"]
    threshold: Number
    effect: Literal["exclude", "penalize"]
    penalty: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)] = 0

    @model_validator(mode="after")
    def valid_penalty(self) -> "Rule":
        if self.effect == "exclude" and self.penalty != 0:
            raise ValueError("Exclusion rules have no point penalty")
        if self.effect == "penalize" and self.penalty <= 0:
            raise ValueError("Penalty rules require positive points")
        return self


class EvaluationInput(StrictModel):
    analysis_signature: str
    criteria: list[Criterion]
    ratings: list[Rating]
    rules: list[Rule] = Field(default_factory=list)
    preferred_option_id: UUID | None = None

    @model_validator(mode="after")
    def valid_references(self) -> "EvaluationInput":
        for values in [[c.id for c in self.criteria], [r.option_id for r in self.ratings],
                       [r.id for r in self.rules]]:
            if len(values) != len(set(values)):
                raise ValueError("Duplicate criterion, option, or rule IDs")
        criteria = {c.id for c in self.criteria}
        if any(set(r.scores) != criteria for r in self.ratings):
            raise ValueError("Each option needs every criterion; use null for unknown ratings")
        if any(r.criterion_id not in criteria for r in self.rules):
            raise ValueError("Rule references an unknown criterion")
        if self.preferred_option_id is not None and self.preferred_option_id not in {
            r.option_id for r in self.ratings
        }:
            raise ValueError("Preferred option is not among the rated options")
        return self


class Contribution(StrictModel):
    criterion: str
    rating: float | None
    weight: float
    points: float | None


class RuleTrace(StrictModel):
    rule: str
    condition: str
    triggered: bool | None
    effect: str


class OptionScore(StrictModel):
    option_id: UUID
    description: str
    eligible: bool | None
    base_score: float | None
    final_score: float | None
    penalty: float
    contributions: list[Contribution]
    rules: list[RuleTrace]


class EvaluationResult(StrictModel):
    status: Literal["recommended", "tie", "incomplete", "no_eligible_options"]
    recommended_option_id: UUID | None
    tied_option_ids: list[UUID]
    options: list[OptionScore]
    conflicts: list[str]
    explanation: str


class SavedEvaluation(StrictModel):
    inputs: EvaluationInput
    result: EvaluationResult
    stale: bool = False


class EvaluationEnvelope(StrictModel):
    analysis_signature: str
    evaluation: SavedEvaluation | None
