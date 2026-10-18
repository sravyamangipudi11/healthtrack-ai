"""Pydantic models: input validation (request) and output contract (LLM response)."""
import re
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# letters/digits plus a few punctuation chars common in symptom text; blocks markup & injection-style payloads
SYMPTOM_RE = re.compile(r"^[a-z0-9][a-z0-9 \-',/()]{1,79}$")
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class Sex(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class SymptomRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1, max_length=15)
    age: int = Field(ge=0, le=120)
    sex: Sex = Sex.unknown
    duration_days: Optional[int] = Field(default=None, ge=0, le=3650)
    temperature: Optional[float] = Field(default=None)
    temperature_unit: Literal["C", "F"] = "C"
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_temperature(self):
        if self.temperature is not None:
            low, high = (25, 45) if self.temperature_unit == "C" else (77, 113)
            if not low <= self.temperature <= high:
                raise ValueError(
                    f"Temperature must be between {low} and {high} degrees "
                    f"{self.temperature_unit}"
                )
        return self

    @field_validator("symptoms")
    @classmethod
    def clean_symptoms(cls, items: list[str]) -> list[str]:
        out: list[str] = []
        for s in items:
            s = " ".join(s.strip().lower().split())  # normalise case/whitespace
            if not SYMPTOM_RE.match(s):
                raise ValueError(f"Invalid symptom: {s[:40]!r} (2-80 chars; letters, digits, - ' , / ( ) only)")
            if s not in out:  # de-duplicate, keep order
                out.append(s)
        return out

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = CONTROL_CHARS.sub("", v).strip()
        return v or None


class Condition(BaseModel):
    name: str
    rationale: str
    likelihood: Literal["low", "medium", "high"]


class Insight(BaseModel):
    """Contract the LLM output must satisfy; anything else is rejected."""
    possible_conditions: list[Condition] = Field(max_length=6)
    recommended_next_steps: list[str] = Field(max_length=8)
    red_flags: list[str] = Field(default_factory=list)
    urgency: Literal["routine", "urgent", "emergency"]


class InsightResponse(Insight):
    request_id: str
    cached: bool
    disclaimer: str = "Preliminary decision-support only. Not a diagnosis; clinical judgement prevails."
