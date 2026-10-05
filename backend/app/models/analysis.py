from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models.decision import DecisionCreate
from app.models.suggestion import AIProvenance

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Context(DecisionCreate):
    # Retain the original situation alongside the editable structured problem.
    actors: list[Text] = Field(default_factory=list)
    problem: Text
    constraints: list[Text] = Field(default_factory=list)
    known_facts: list[Text] = Field(default_factory=list)
    unknowns: list[Text] = Field(default_factory=list)


class Option(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    description: Text


class AnalysisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context: Context
    options: list[Option] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_option_ids(self) -> "AnalysisDraft":
        ids = [option.id for option in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("Option IDs must be unique")
        return self


class Analysis(AnalysisDraft):
    ai_provenance: AIProvenance | None = None
    decision_id: UUID
    reviewed: bool = False
    warnings: list[str] = Field(default_factory=list)
