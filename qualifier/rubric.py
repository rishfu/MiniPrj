"""
Stage 2 - ANALYZE (rules): score every lead against the rubric in config.yaml.

This stage is pure Python on purpose:
  * Consistent: the same lead always gets the same base score.
  * Explainable: every point comes from a named factor with a label.
  * Free and instant: no API call, so it works even if the LLM is down.

The LLM later adds a small, bounded adjustment on top (see judge.py), and the
knock-out caps defined here are re-applied after that adjustment.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from .models import FactorScore, Lead, RubricResult


def _key(text: str) -> str:
    """'Non-profit' / 'NonProfit' / 'non profit' -> 'nonprofit' for matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


class Rubric:
    def __init__(self, rubric_cfg: dict):
        self.cfg = rubric_cfg
        f = rubric_cfg["factors"]
        self.size_cfg = f["company_size"]
        self.industry_cfg = f["industry_fit"]
        self.intent_cfg = f["intent_signal"]
        self.recency_cfg = f["recency"]
        self.caps_cfg = {c["rule"]: c for c in rubric_cfg.get("caps", [])}

        # Pre-build lookup tables: normalised name -> tier / source key.
        self._industry_lookup: dict[str, str] = {}
        for tier, tier_cfg in self.industry_cfg["tiers"].items():
            for ind in tier_cfg["industries"]:
                self._industry_lookup[_key(ind)] = tier
        self._source_lookup: dict[str, str] = {}
        for src_key, src_cfg in self.intent_cfg["sources"].items():
            for alias in src_cfg.get("aliases", []) + [src_key]:
                self._source_lookup[_key(alias)] = src_key

        self._min_points = {
            "company_size": min(b["points"] for b in self.size_cfg["bands"]),
            "industry_fit": min(t["points"] for t in self.industry_cfg["tiers"].values()),
            "intent_signal": min(s["points"] for s in self.intent_cfg["sources"].values()),
            "recency": min(b["points"] for b in self.recency_cfg["bands"]),
        }
        self.max_total = sum(x["max_points"] for x in (self.size_cfg, self.industry_cfg, self.intent_cfg, self.recency_cfg))

    # ---- individual factors -------------------------------------------------

    def score_size(self, size: Optional[int]) -> FactorScore:
        mx = self.size_cfg["max_points"]
        if size is None:
            return FactorScore("company_size", self.size_cfg["missing_points"], mx,
                               "Company size unknown: neutral-low default used", is_default=True)
        for band in self.size_cfg["bands"]:
            if size >= band["min"] and (band["max"] is None or size <= band["max"]):
                return FactorScore("company_size", band["points"], mx, f"{band['label']} [{size:,} employees]")
        return FactorScore("company_size", self.size_cfg["missing_points"], mx, f"Size {size} outside all bands", True)

    def industry_tier(self, industry: Optional[str]) -> Optional[str]:
        if industry is None:
            return None
        return self._industry_lookup.get(_key(industry), "unmapped")

    def score_industry(self, industry: Optional[str]) -> FactorScore:
        mx = self.industry_cfg["max_points"]
        tier = self.industry_tier(industry)
        if tier is None:
            return FactorScore("industry_fit", self.industry_cfg["missing_points"], mx,
                               "Industry unknown: default used", is_default=True)
        if tier == "unmapped":
            return FactorScore("industry_fit", self.industry_cfg["unmapped_points"], mx,
                               f"Industry '{industry}' is not in our rubric yet: neutral default used", is_default=True)
        tier_cfg = self.industry_cfg["tiers"][tier]
        return FactorScore("industry_fit", tier_cfg["points"], mx, f"{tier_cfg['label']} [{industry}]")

    def source_key(self, source: Optional[str]) -> Optional[str]:
        if source is None:
            return None
        return self._source_lookup.get(_key(source), "unmapped")

    def score_intent(self, source: Optional[str]) -> FactorScore:
        mx = self.intent_cfg["max_points"]
        key = self.source_key(source)
        if key is None:
            return FactorScore("intent_signal", self.intent_cfg["missing_points"], mx,
                               "Lead source unknown: low default used", is_default=True)
        if key == "unmapped":
            return FactorScore("intent_signal", self.intent_cfg["unmapped_points"], mx,
                               f"Source '{source}' not in our rubric: neutral default used", is_default=True)
        s = self.intent_cfg["sources"][key]
        return FactorScore("intent_signal", s["points"], mx, s["label"])

    def score_recency(self, days: Optional[int]) -> FactorScore:
        mx = self.recency_cfg["max_points"]
        if days is None:
            return FactorScore("recency", self.recency_cfg["missing_points"], mx,
                               "Last interaction date unknown: low default used", is_default=True)
        for band in self.recency_cfg["bands"]:
            if band["max_days"] is None or days <= band["max_days"]:
                return FactorScore("recency", band["points"], mx, f"{band['label']} [{days} days ago]")
        raise AssertionError("recency bands must end with max_days: null")

    # ---- whole lead ---------------------------------------------------------

    def score(self, lead: Lead, reference_date: date) -> RubricResult:
        days = (reference_date - lead.last_interaction).days if lead.last_interaction else None
        factors = [
            self.score_size(lead.company_size),
            self.score_industry(lead.industry),
            self.score_intent(lead.source),
            self.score_recency(days),
        ]
        for f in factors:
            f.min_possible = self._min_points[f.factor]
        base = round(sum(f.points for f in factors), 2)
        # Rescale defensively in case someone edits max_points so they no longer sum to 10.
        if abs(self.max_total - 10.0) > 1e-9:
            base = round(base * 10.0 / self.max_total, 2)

        caps = []
        if lead.company_size is not None and lead.company_size <= 10 and "micro_company" in self.caps_cfg:
            caps.append(self.caps_cfg["micro_company"])
        if days is not None and days > 365 and "stale_contact" in self.caps_cfg:
            caps.append(self.caps_cfg["stale_contact"])
        if lead.company_size is not None and lead.company_size > 20000 and "very_large_company" in self.caps_cfg:
            caps.append(self.caps_cfg["very_large_company"])

        return RubricResult(factors=factors, base_score=base, days_since_contact=days,
                            industry_tier=self.industry_tier(lead.industry),
                            source_key=self.source_key(lead.source),
                            caps=[{"rule": c["rule"], "max_score": c["max_score"], "reason": c["reason"]} for c in caps])

    def summary_text(self) -> str:
        """Short rubric description that is shown to the LLM and put in the report."""
        th = self.cfg["thresholds"]
        return (
            f"Score = company size (max {self.size_cfg['max_points']}) + industry fit (max {self.industry_cfg['max_points']}) "
            f"+ intent signal from lead source (max {self.intent_cfg['max_points']}) + recency of last interaction "
            f"(max {self.recency_cfg['max_points']}) = 10. "
            f">= {th['qualified_min']} qualified, {th['review_min']}-{th['qualified_min']} human review, "
            f"< {th['review_min']} rejected. Micro companies (<=10 staff), very large companies (>20,000 staff) and "
            f"contacts older than a year are capped at review."
        )
