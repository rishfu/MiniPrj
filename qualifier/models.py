"""
Data structures that flow through the pipeline.

Each stage takes one of these and produces the next one, so you can read the
pipeline as a chain of transformations:

    CSV row -> Lead -> RubricResult -> LLMJudgment -> LeadDecision -> report

Keeping these as plain dataclasses (rather than passing dicts around) makes it
obvious what each stage needs and returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DataIssue:
    """A problem found while reading a lead. `critical` issues stop a lead from
    being auto-qualified; `warning` issues are just reported."""
    field: str
    issue: str
    severity: str = "warning"  # "warning" | "critical"

    def to_dict(self) -> dict:
        return {"field": self.field, "issue": self.issue, "severity": self.severity}


@dataclass
class Lead:
    """One cleaned lead. Fields are None when missing/invalid - never a fake value."""
    lead_id: str
    row_number: int                  # line number in the CSV (header = line 1), for traceability
    name: Optional[str]
    company: Optional[str]
    company_size: Optional[int]
    industry: Optional[str]
    source: Optional[str]
    last_interaction: Optional[date]
    raw: dict = field(default_factory=dict)          # original values, for the audit trail
    issues: list[DataIssue] = field(default_factory=list)
    duplicate_of: Optional[str] = None

    @property
    def display_name(self) -> str:
        return self.name or "Unknown contact"

    @property
    def first_name(self) -> Optional[str]:
        if not self.name:
            return None
        return self.name.split()[0]

    def add_issue(self, field_name: str, issue: str, severity: str = "warning") -> None:
        self.issues.append(DataIssue(field_name, issue, severity))

    def to_dict(self) -> dict:
        return {
            "lead_id": self.lead_id,
            "row_number": self.row_number,
            "name": self.name,
            "company": self.company,
            "company_size": self.company_size,
            "industry": self.industry,
            "source": self.source,
            "last_interaction_date": self.last_interaction.isoformat() if self.last_interaction else None,
        }


@dataclass
class FactorScore:
    """Score for one rubric factor, with a human-readable explanation."""
    factor: str
    points: float
    max_points: float
    label: str
    is_default: bool = False   # True when the value was missing/unmapped and a default was used
    min_possible: float = 0.0  # worst score this factor could have had (for the uncertainty check)

    @property
    def ratio(self) -> float:
        return self.points / self.max_points if self.max_points else 0.0

    def to_dict(self) -> dict:
        return {"factor": self.factor, "points": self.points, "max_points": self.max_points,
                "explanation": self.label, "used_default": self.is_default}


@dataclass
class RubricResult:
    """Deterministic score from the rubric (no LLM involved)."""
    factors: list[FactorScore]
    base_score: float
    days_since_contact: Optional[int]
    industry_tier: Optional[str]     # core | adjacent | low | unmapped | None (missing)
    source_key: Optional[str]        # inbound_demo | referral | ... | None
    caps: list[dict] = field(default_factory=list)   # knock-out caps that apply: {rule, max_score, reason}

    def factor(self, name: str) -> FactorScore:
        return next(f for f in self.factors if f.factor == name)


@dataclass
class LLMJudgment:
    """What the LLM (or the fallback) said about a lead."""
    adjustment: float = 0.0
    adjustment_reason: str = ""
    confidence: str = "medium"       # high | medium | low
    summary: str = ""
    outreach_message: Optional[str] = None
    source: str = "fallback"         # llm | mock | fallback - where this judgment came from
    note: str = ""                   # e.g. why a fallback was used


@dataclass
class LeadDecision:
    """Final, explainable outcome for one lead."""
    lead: Lead
    rubric: RubricResult
    judgment: LLMJudgment
    final_score: float
    decision: str                    # qualified | review | rejected
    decision_reasons: list[str]
    priority_rank: Optional[int] = None
    priority_tier: Optional[str] = None
    next_action: str = ""
    outreach_sequence: list[dict] = field(default_factory=list)
    outreach_message: Optional[str] = None
    message_source: Optional[str] = None   # llm | template | None
    message_angle: Optional[str] = None
