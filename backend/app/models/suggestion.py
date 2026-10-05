from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class ProposedOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    rationale: str
    assumptions: list[str]


class ReportedFact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str
    source_quote: str


class ProposedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    problem: str
    actors: list[str]
    constraints: list[str]
    reported_facts: list[ReportedFact]
    unknowns: list[str]
    options: list[ProposedOption]
    summary: str
    assumptions: list[str]


    @model_validator(mode="after")
    def validate_details(self) -> "ProposedContext":
        strings = [self.problem, *self.actors, *self.constraints, *self.unknowns,
                   *[o.description for o in self.options]]
        if any(not value.strip() for value in strings):
            raise ValueError("Required details cannot be blank")
        names = [o.description.strip().casefold() for o in self.options]
        if len(names) != len(set(names)):
            raise ValueError("Candidate options must be distinct")
        return self


class Suggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    decision_id: UUID
    base_signature: str
    generated_at: datetime
    source: Literal["openai", "rules_fallback"]
    model: str | None
    prompt_version: str
    notice: str
    proposal: ProposedContext
    stale: bool = False


class AISuggestionStatus(BaseModel):
    configured: bool
    suggestion: Suggestion | None


class AIProvenance(BaseModel):
    suggestion_id: UUID
    source: Literal["openai", "rules_fallback"]
    model: str | None
    generated_at: datetime
    prompt_version: str
