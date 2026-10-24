"""
Outreach messages: angle selection, template fallback, and validation.

The LLM writes the primary message. But an LLM can fail, time out, or write
something unusable, so every qualified lead also has a deterministic template
message built from the same lead details. A sales rep never gets an empty slot.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import Lead

ANGLE_BY_SOURCE = {
    "inbound_demo": "demo_followup",
    "referral": "warm_referral",
    "sales_call": "call_recap",
    "webinar": "event_followup",
    "content_download": "content_followup",
    "linkedin": "social_intro",
}

PLACEHOLDER_RE = re.compile(r"\[[^\]]{1,40}\]|\{\{?[^}]{1,40}\}?\}|<[A-Za-z _]{1,40}>")


def message_angle(source_key: Optional[str]) -> str:
    return ANGLE_BY_SOURCE.get(source_key or "", "general_intro")


def value_prop_for(industry: Optional[str], value_props: dict) -> str:
    """Pick the value proposition whose keyword appears in the industry name."""
    ind = (industry or "").lower()
    for keyword, text in value_props.items():
        if keyword != "default" and keyword in ind:
            return text
    return value_props.get("default", "replace manual hand-offs with automated workflows")


def _size_phrase(size: Optional[int]) -> str:
    if size is None:
        return "a growing team"
    if size <= 50:
        return f"a team of about {size}"
    if size <= 1000:
        return f"a {size:,}-person organisation"
    return f"an organisation of {size:,} people"


def _when_phrase(days: Optional[int]) -> str:
    if days is None:
        return "recently"
    if days <= 1:
        return "just now"
    if days <= 7:
        return "earlier this week"
    if days <= 30:
        return "a few weeks ago"
    return f"about {max(1, round(days / 30))} month{'s' if days >= 45 else ''} ago"


def template_message(lead: Lead, angle: str, days: Optional[int], seller: dict, value_prop: str) -> str:
    """Deterministic, still-personalised message used when the LLM can't provide one."""
    greeting = f"Hi {lead.first_name}," if lead.first_name else "Hi there,"
    company = lead.company or "your team"
    industry = lead.industry or "your industry"
    when, size = _when_phrase(days), _size_phrase(lead.company_size)
    sign = f"Best,\n{seller['sender_name']}\n{seller['sender_title']}"
    possessive = (f"{company}' " if company.endswith("s") else f"{company}'s ") if lead.company else "your "

    bodies = {
        "demo_followup": (
            f"Thanks for requesting a {seller['company_name']} demo {when}. For {size} in {industry} like {company}, "
            f"the quickest win is usually to {value_prop}. I'd like to tailor the demo to your current hand-offs - "
            f"would Tuesday at 10am or Thursday at 2pm work for 30 minutes?"),
        "warm_referral": (
            f"You were referred to us {when}, so I wanted to reach out personally. Teams in {industry} often use "
            f"{seller['company_name']} to {value_prop}, and at {possessive}size ({size}) that tends to pay off fast. "
            f"Would a 20-minute call next week be useful to see if it fits?"),
        "call_recap": (
            f"Thanks again for the conversation {when}. As a quick recap: for {company}, {size} in {industry}, the "
            f"clearest opportunity is to {value_prop}. As a next step, I can put together a short workflow map for "
            f"your team - could we book 30 minutes this week to review it together?"),
        "event_followup": (
            f"Thanks for joining our webinar {when}. Many {industry} teams in the audience asked how to {value_prop}, "
            f"so I put together a two-page example that fits {size} like {company}. Shall I send it over, or would a "
            f"short walkthrough be more useful?"),
        "content_followup": (
            f"I saw you downloaded one of our guides {when} - I hope it was useful. One idea that tends to land well "
            f"with {industry} teams like {company} is to {value_prop}. If it would help, I'm happy to share a "
            f"10-minute example tailored to {size}. No pressure either way."),
        "social_intro": (
            f"I came across {company} while looking at {industry} teams of your size ({size}). We help companies "
            f"like yours {value_prop}. Curious - how does your team handle hand-offs between departments today? "
            f"If it's still email and spreadsheets, I'd love to compare notes."),
        "general_intro": (
            f"I'm reaching out because {company} looks like a strong fit for {seller['company_name']}: we help "
            f"{industry} teams of {size} {value_prop}. Would a short call next week be worthwhile to see whether "
            f"it fits your current priorities?"),
    }
    return f"{greeting}\n\n{bodies.get(angle, bodies['general_intro'])}\n\n{sign}"


def validate_message(msg: Optional[str], lead: Lead) -> tuple[bool, str]:
    """Quality gate for LLM-written messages. Returns (ok, reason)."""
    if not msg or not isinstance(msg, str):
        return False, "no message returned"
    words = len(msg.split())
    if words < 30:
        return False, f"too short ({words} words)"
    if words > 180:
        return False, f"too long ({words} words)"
    if PLACEHOLDER_RE.search(msg):
        return False, "contains an unfilled placeholder"
    if lead.company and lead.company.split()[0].lower() not in msg.lower():
        return False, "does not mention the company"
    if re.search(r"\bas an ai\b|language model", msg, re.IGNORECASE):
        return False, "contains AI boilerplate"
    return True, "ok"
