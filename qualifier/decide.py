"""
Stage 3 - DECIDE: combine rubric + LLM judgment into a final, explainable decision,
then rank the qualified leads and plan the outreach sequence.

Order of operations (it matters):
  1. final = base_score + llm_adjustment            (LLM nudges, within +/-1)
  2. apply knock-out caps                           (LLM can't override business rules)
  3. clamp to 1..10
  4. map to qualified / review / rejected via thresholds
  5. human-in-the-loop overrides -> REVIEW when the system shouldn't guess:
       - critical data problems (no company, duplicate row)
       - too many missing fields to trust the score
       - "qualified" but the LLM had low confidence
"""

from __future__ import annotations

import math
from typing import Optional

from .messages import message_angle, template_message, validate_message, value_prop_for
from .models import LeadDecision, LLMJudgment, Lead, RubricResult

CORE_FIELDS = ("company_size", "industry", "source", "last_interaction_date")

# Human-readable labels for "why was this rejected?" stats.
WEAK_FACTOR_REASONS = {
    "company_size": "Company size outside target range",
    "industry_fit": "Low-fit or unknown industry",
    "intent_signal": "Weak buying-intent signal (cold or early-stage source)",
    "recency": "No recent interaction",
}

CHANNEL_BY_SOURCE = {
    "inbound_demo": "Email (reply to demo request)",
    "referral": "Email (warm intro)",
    "sales_call": "Email (call recap)",
    "webinar": "Email (webinar follow-up)",
    "content_download": "Email (content follow-up)",
    "linkedin": "LinkedIn message",
}


def missing_core_fields(lead: Lead) -> list[str]:
    values = {"company_size": lead.company_size, "industry": lead.industry,
              "source": lead.source, "last_interaction_date": lead.last_interaction}
    return [f for f in CORE_FIELDS if values[f] is None]


def weak_factors(rubric: RubricResult) -> list[str]:
    """Factors that scored below half their max - used as rejection reasons.
    A factor scored from a default is reported as unknown, not as a bad fit."""
    return [f"Unknown {f.factor.replace('_', ' ')} (scored with a default)" if f.is_default
            else WEAK_FACTOR_REASONS[f.factor]
            for f in rubric.factors if f.ratio < 0.5]


def round_half_up(x: float, digits: int = 1) -> float:
    """round(9.25, 1) gives 9.2 in Python (binary floats + banker's rounding); a sales rep expects 9.3."""
    m = 10 ** digits
    return math.floor(x * m + 0.5 + 1e-9) / m


def decide(lead: Lead, rubric: RubricResult, judgment: LLMJudgment, rubric_cfg: dict) -> LeadDecision:
    th = rubric_cfg["thresholds"]
    reasons: list[str] = []

    score = rubric.base_score + judgment.adjustment
    if judgment.adjustment:
        reasons.append(f"LLM adjustment {judgment.adjustment:+.1f}: {judgment.adjustment_reason}")
    for cap in rubric.caps:
        if score > cap["max_score"]:
            reasons.append(f"Capped at {cap['max_score']}: {cap['reason']}")
            score = cap["max_score"]
    # Decide on the exact value; round only for display (rounding first can flip
    # a borderline decision - e.g. 7.25 shown as 7.3 changes the worst case).
    score = max(1.0, min(10.0, score))
    shown = round_half_up(score)

    if score >= th["qualified_min"]:
        decision = "qualified"
        reasons.insert(0, f"Score {shown} >= {th['qualified_min']} qualification threshold")
    elif score >= th["review_min"]:
        decision = "review"
        reasons.insert(0, f"Score {shown} is in the {th['review_min']}-{th['qualified_min']} 'too close to call' band")
    else:
        decision = "rejected"
        reasons.insert(0, f"Score {shown} < {th['review_min']}")
        reasons.extend(weak_factors(rubric) or ["Overall fit below threshold"])

    # ---- human-in-the-loop overrides --------------------------------------
    critical = [i.issue for i in lead.issues if i.severity == "critical"]
    missing = missing_core_fields(lead)
    if critical:
        decision = "review"
        reasons.append("Needs human review - data problem: " + "; ".join(critical))
    if len(missing) >= th["insufficient_data_missing_fields"]:
        decision = "review"
        reasons.append(f"Needs human review - insufficient data ({', '.join(missing)} missing); score not reliable")
    # Uncertainty check: for every factor scored with a default (missing or
    # unmapped value), what if the true value were the worst / best possible?
    # If that could flip the outcome, a human should decide - not the default.
    defaulted = [f for f in rubric.factors if f.is_default]
    if defaulted:
        names = ", ".join(f.factor for f in defaulted)
        cap_max = min((c["max_score"] for c in rubric.caps), default=10.0)
        worst = score - sum(f.points - f.min_possible for f in defaulted)
        best = min(cap_max, score + sum(f.max_points - f.points for f in defaulted))
        if decision == "qualified" and worst < th["qualified_min"]:
            decision = "review"
            reasons.append(f"Needs human review - qualification depends on unknown value(s) for {names} "
                           f"(worst case {round_half_up(worst)})")
        elif decision == "rejected" and best >= th["qualified_min"]:
            decision = "review"
            reasons.append(f"Needs human review - could qualify if unknown {names} turns out favourable "
                           f"(best case {round_half_up(best)})")
    if decision == "qualified" and judgment.confidence == "low":
        decision = "review"
        reasons.append("Needs human review - LLM confidence is low")

    return LeadDecision(lead=lead, rubric=rubric, judgment=judgment, final_score=shown,
                        decision=decision, decision_reasons=reasons,
                        message_angle=message_angle(rubric.source_key))


def attach_message(d: LeadDecision, seller_cfg: dict, write_message: bool) -> Optional[str]:
    """Use the LLM message if it passes validation; otherwise the template. Returns a note if we fell back."""
    if d.decision == "rejected" or not write_message:
        return None
    value_prop = value_prop_for(d.lead.industry, seller_cfg["value_props"])
    ok, why = validate_message(d.judgment.outreach_message, d.lead)
    if ok:
        d.outreach_message, d.message_source = d.judgment.outreach_message, "llm"
        return None
    d.outreach_message = template_message(d.lead, d.message_angle, d.rubric.days_since_contact, seller_cfg, value_prop)
    d.message_source = "template"
    return why if d.judgment.source == "llm" else None


def rank_and_plan(decisions: list[LeadDecision], rubric_cfg: dict) -> None:
    """Order the queues and attach next actions + a 3-touch outreach sequence."""
    pr = rubric_cfg["priority"]
    src_points = {k: v["points"] for k, v in rubric_cfg["factors"]["intent_signal"]["sources"].items()}

    def sort_key(d: LeadDecision):
        # Highest score first; ties -> most recent contact; then strongest intent.
        days = d.rubric.days_since_contact if d.rubric.days_since_contact is not None else 10 ** 6
        return (-d.final_score, days, -src_points.get(d.rubric.source_key or "", 0), d.lead.lead_id)

    qualified = sorted((d for d in decisions if d.decision == "qualified"), key=sort_key)
    for rank, d in enumerate(qualified, 1):
        d.priority_rank = rank
        p1 = d.final_score >= pr["p1_min_score"]
        d.priority_tier = "P1" if p1 else "P2"
        first = "within 24 hours" if p1 else "within 3 business days"
        channel = CHANNEL_BY_SOURCE.get(d.rubric.source_key or "", "Email")
        d.next_action = f"{d.priority_tier}: send first message via {channel} {first}"
        d.outreach_sequence = [
            {"step": 1, "day": 0, "channel": channel, "action": f"Send the personalised first message ({first})"},
            {"step": 2, "day": 3, "channel": "Email", "action": "Short follow-up with one relevant customer example"},
            {"step": 3, "day": 7, "channel": "Phone" if (d.lead.company_size or 0) > 50 else "LinkedIn",
             "action": "Final touch; if no reply, move to nurture"},
        ]

    review = sorted((d for d in decisions if d.decision == "review"), key=sort_key)
    for rank, d in enumerate(review, 1):
        d.priority_rank = rank
        d.priority_tier = "REVIEW"
        d.next_action = "Human review: an SDR confirms or rejects (see decision_reasons)"

    for d in decisions:
        if d.decision == "rejected":
            d.priority_tier = "NURTURE" if d.final_score >= pr["nurture_min_score"] else "ARCHIVE"
            d.next_action = ("Add to monthly newsletter / nurture track" if d.priority_tier == "NURTURE"
                             else "Archive - no action")
