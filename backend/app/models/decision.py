from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints


class DecisionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    situation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10)]
    domain: Literal["Personal", "Work", "Relationship", "Financial", "Safety", "Health", "Other"]
    stakes: Literal["Low", "Medium", "High", "Critical"]
    time_pressure: Literal["None", "Low", "Moderate", "High", "Immediate"]


class Decision(DecisionCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
