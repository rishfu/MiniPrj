"""
Stage 1 - INTAKE: read the CSV and turn messy rows into clean `Lead` objects.

Principles:
  * Never crash on bad data. A bad value becomes None + a DataIssue, and the
    lead keeps flowing through the pipeline.
  * Never invent data. A missing size stays None; the rubric decides how to
    score "unknown", and the report shows that a default was used.
  * Keep the raw value. The report can always show what the CSV really said.
"""

from __future__ import annotations

import csv
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .models import Lead

log = logging.getLogger("lead_qualifier.ingest")

EXPECTED_COLUMNS = ["name", "company", "company_size", "industry", "source", "last_interaction_date"]

# Values that mean "we don't know". The data README says blank = missing, but
# the testing file also uses "NA", so we accept the common spellings.
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan", "-", "--", "?"}
# "Unknown Source", "Unknown Sector" etc. are placeholders, not real values.
PLACEHOLDER_RE = re.compile(r"^unknown\b", re.IGNORECASE)

DATE_FORMATS = [("%Y-%m-%d", False), ("%Y/%m/%d", True), ("%m/%d/%Y", True), ("%d-%m-%Y", True)]

EXTREME_SIZE = 20000   # sizes above this are plausible but worth a human glance


class IngestError(Exception):
    """The file itself can't be used (missing, empty, wrong format)."""


def _normalise_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (h or "").strip().lower()).strip("_")


def clean_text(value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (clean_value, issue). Collapses whitespace; maps missing tokens to None."""
    if value is None:
        return None, None
    v = re.sub(r"\s+", " ", str(value)).strip()
    if v.lower() in MISSING_TOKENS:
        return None, None
    if PLACEHOLDER_RE.match(v):
        return None, f"placeholder value '{v}' treated as missing"
    return v, None


def parse_company_size(value: Optional[str]) -> tuple[Optional[int], Optional[str]]:
    """Parse sizes like '50', '1,200', '~300', '5k', '500+', '25-50' (midpoint)."""
    v, _ = clean_text(value)
    if v is None:
        return None, None
    s = v.lower().replace(",", "").replace("~", "").replace("+", "").replace("employees", "").strip()
    try:
        range_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)", s)
        if range_match:
            lo, hi = float(range_match.group(1)), float(range_match.group(2))
            size = int(round((lo + hi) / 2))
            note = f"size given as range '{v}', used midpoint {size}"
        elif s.endswith("k"):
            size, note = int(float(s[:-1]) * 1000), None
        else:
            size, note = int(float(s)), None
    except ValueError:
        return None, f"invalid company_size '{v}' (not a number)"
    if size <= 0:
        return None, f"invalid company_size '{v}' (must be positive)"
    return size, note


def parse_date(value: Optional[str]) -> tuple[Optional[date], Optional[str]]:
    v, _ = clean_text(value)
    if v is None:
        return None, None
    for fmt, non_standard in DATE_FORMATS:
        try:
            d = datetime.strptime(v, fmt).date()
            return d, (f"non-standard date format '{v}' (expected YYYY-MM-DD)" if non_standard else None)
        except ValueError:
            continue
    return None, f"invalid date '{v}'"


def load_leads(path: str | Path) -> tuple[list[Lead], dict]:
    """Read a CSV into Lead objects. Returns (leads, ingest_stats)."""
    path = Path(path)
    if not path.exists():
        raise IngestError(f"Input file not found: {path}")
    if path.stat().st_size == 0:
        raise IngestError(f"Input file is empty: {path}")

    stats = {"rows_read": 0, "rows_skipped_blank": 0, "missing_columns": [], "duplicates": 0}
    leads: list[Lead] = []
    seen: dict[tuple, str] = {}

    # utf-8-sig silently drops the BOM Excel adds to CSV exports.
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise IngestError(f"No header row found in {path}")
        header_map = {_normalise_header(h): h for h in reader.fieldnames if h is not None}
        missing_cols = [c for c in EXPECTED_COLUMNS if c not in header_map]
        if len(missing_cols) == len(EXPECTED_COLUMNS):
            raise IngestError(f"None of the expected columns {EXPECTED_COLUMNS} found in {path}")
        if missing_cols:
            # Degrade gracefully: treat the whole column as missing for every row.
            log.warning("Columns missing from %s: %s - treating them as blank", path.name, missing_cols)
            stats["missing_columns"] = missing_cols

        for line_no, row in enumerate(reader, start=2):
            stats["rows_read"] += 1
            raw = {c: (row.get(header_map[c]) if c in header_map else None) for c in EXPECTED_COLUMNS}
            if all(clean_text(v)[0] is None for v in raw.values()):
                stats["rows_skipped_blank"] += 1
                log.info("Row %d is blank - skipped", line_no)
                continue
            lead = _build_lead(f"L{len(leads) + 1:03d}", line_no, raw)

            key = ((lead.name or "").lower(), (lead.company or "").lower())
            if lead.company and key in seen:
                lead.duplicate_of = seen[key]
                lead.add_issue("row", f"possible duplicate of {seen[key]} (same name and company)", "critical")
                stats["duplicates"] += 1
            elif lead.company:
                seen[key] = lead.lead_id
            leads.append(lead)

    log.info("Loaded %d leads from %s (%d blank rows skipped)", len(leads), path.name, stats["rows_skipped_blank"])
    return leads, stats


def _build_lead(lead_id: str, line_no: int, raw: dict) -> Lead:
    lead = Lead(lead_id=lead_id, row_number=line_no, name=None, company=None, company_size=None,
                industry=None, source=None, last_interaction=None, raw=dict(raw))

    for fld in ("name", "company", "industry", "source"):
        value, issue = clean_text(raw.get(fld))
        setattr(lead, fld, value)
        if issue:
            lead.add_issue(fld, issue)

    size, size_issue = parse_company_size(raw.get("company_size"))
    lead.company_size = size
    if size_issue:
        lead.add_issue("company_size", size_issue)
    if size is not None and size > EXTREME_SIZE:
        lead.add_issue("company_size", f"unusually large company_size {size:,} - verify")

    d, date_issue = parse_date(raw.get("last_interaction_date"))
    lead.last_interaction = d
    if date_issue:
        lead.add_issue("last_interaction_date", date_issue)

    # Record plain "missing" issues so the report can count them per field.
    if lead.name is None:
        lead.add_issue("name", "missing contact name - message will use a neutral greeting")
    if lead.company is None:
        lead.add_issue("company", "missing company name - cannot personalise or verify the account", "critical")
    for fld, val in (("company_size", lead.company_size), ("industry", lead.industry),
                     ("source", lead.source), ("last_interaction_date", lead.last_interaction)):
        if val is None and not any(i.field == fld for i in lead.issues):
            lead.add_issue(fld, f"missing {fld}")
    return lead


def resolve_reference_date(leads: list[Lead], setting: str = "auto") -> date:
    """
    Which day counts as "today" when measuring recency?

    The sample data is from Dec 2023 - Jan 2024. Measured against the real
    today, every lead would be "stale" and recency would carry no signal. So by
    default we use the latest interaction date in the file (the day the export
    was taken). Pass "today" or an explicit YYYY-MM-DD for live data.
    """
    setting = (setting or "auto").strip().lower()
    if setting == "today":
        return date.today()
    if setting != "auto":
        return datetime.strptime(setting, "%Y-%m-%d").date()
    today = date.today()
    dates = sorted(l.last_interaction for l in leads if l.last_interaction and l.last_interaction <= today)
    if not dates:
        return today
    # Robustness: one typo'd date (e.g. 2025 instead of 2024) must not become
    # "today" for the whole file and make every other lead look stale. Ignore
    # dates more than 90 days after the 90th-percentile date.
    p90 = dates[int(0.9 * (len(dates) - 1))]
    plausible = [d for d in dates if (d - p90).days <= 90]
    outliers = len(dates) - len(plausible)
    if outliers:
        log.warning("Ignoring %d outlier date(s) when choosing the reference date (latest plausible: %s)",
                    outliers, plausible[-1])
    return plausible[-1]


def apply_reference_date(leads: list[Lead], ref: date) -> None:
    """Dates after the reference date are impossible, so drop and flag them."""
    for lead in leads:
        if lead.last_interaction and lead.last_interaction > ref:
            lead.add_issue("last_interaction_date",
                           f"date {lead.last_interaction.isoformat()} is after reference date {ref.isoformat()} - treated as missing")
            lead.last_interaction = None
