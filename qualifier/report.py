"""
Stage 4 - OUTPUT: turn decisions into things people can act on.

  output_report.json - complete, machine-readable record (per-lead + stats + run metadata)
  leads_scored.csv   - one row per lead; opens in Excel / Google Sheets for the sales team
  summary.md         - a one-screen human summary: priority queue, review queue, sample messages
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from .models import LeadDecision


def lead_record(d: LeadDecision) -> dict:
    return {
        **d.lead.to_dict(),
        "decision": d.decision,
        "qualification_score": d.final_score,
        "priority_rank": d.priority_rank,
        "priority_tier": d.priority_tier,
        "next_action": d.next_action,
        "reasoning": d.decision_reasons,
        "score_breakdown": {
            "base_score": d.rubric.base_score,
            "factors": [f.to_dict() for f in d.rubric.factors],
            "llm_adjustment": d.judgment.adjustment,
            "llm_adjustment_reason": d.judgment.adjustment_reason or None,
            "caps_applied": [c["rule"] for c in d.rubric.caps if d.rubric.base_score + d.judgment.adjustment > c["max_score"]],
        },
        "llm": {"source": d.judgment.source, "confidence": d.judgment.confidence,
                "summary": d.judgment.summary or None, "note": d.judgment.note or None},
        "data_issues": [i.to_dict() for i in d.lead.issues],
        "outreach": ({"angle": d.message_angle, "message_source": d.message_source,
                      "status": "ready to send" if d.decision == "qualified" else "draft - send only after human approval",
                      "message": d.outreach_message, "sequence": d.outreach_sequence}
                     if d.outreach_message else None),
    }


def queue_entry(rec: dict) -> dict:
    """Compact view for the queues; the full record (factors, issues, message) is in report["leads"]."""
    return {
        "priority_rank": rec["priority_rank"], "priority_tier": rec["priority_tier"], "lead_id": rec["lead_id"],
        "name": rec["name"], "company": rec["company"], "qualification_score": rec["qualification_score"],
        "why": [f["explanation"] for f in rec["score_breakdown"]["factors"]],
        "reasoning": rec["reasoning"], "next_action": rec["next_action"],
    }


def pick_samples(decisions: list[LeadDecision], n: int) -> list[dict]:
    """Best-ranked qualified leads, but one per message angle first so the samples show variety."""
    q = sorted((d for d in decisions if d.decision == "qualified" and d.outreach_message), key=lambda d: d.priority_rank)
    chosen, seen = [], set()
    for d in q:
        if d.message_angle not in seen:
            chosen.append(d)
            seen.add(d.message_angle)
    for d in q:
        if len(chosen) >= n:
            break
        if d not in chosen:
            chosen.append(d)
    return [{"lead_id": d.lead.lead_id, "contact": d.lead.display_name, "company": d.lead.company,
             "priority_rank": d.priority_rank, "angle": d.message_angle, "message_source": d.message_source,
             "message": d.outreach_message} for d in chosen[:n]]


def build_stats(decisions: list[LeadDecision], ingest_stats: dict, judge, elapsed: float, manual_minutes: float) -> dict:
    total = len(decisions)
    count = Counter(d.decision for d in decisions)
    pct = lambda k: round(100.0 * count[k] / total, 1) if total else 0.0

    rejection_reasons = Counter()
    for d in decisions:
        if d.decision == "rejected":
            rejection_reasons.update(r for r in d.decision_reasons if not r.startswith("Score "))
    review_reasons = Counter()
    for d in decisions:
        if d.decision == "review":
            for r in d.decision_reasons:
                if r.startswith("Needs human review"):
                    review_reasons[r.split(" - ")[1].split(":")[0].split(" (")[0]] += 1
                elif "too close to call" in r:
                    review_reasons["score in 'too close to call' band"] += 1
                elif r.startswith("Capped"):
                    review_reasons["knock-out cap (" + r.split(": ", 1)[1].split(":")[0] + ")"] += 1

    by_source = {}
    for d in decisions:
        key = d.lead.source or "(missing)"
        s = by_source.setdefault(key, {"total": 0, "qualified": 0})
        s["total"] += 1
        s["qualified"] += d.decision == "qualified"
    issues = Counter(i.field for d in decisions for i in d.lead.issues)
    llm_sources = Counter(d.judgment.source for d in decisions)
    scores = [d.final_score for d in decisions]

    return {
        "total_processed": total,
        "rows_read": ingest_stats.get("rows_read"),
        "blank_rows_skipped": ingest_stats.get("rows_skipped_blank"),
        "decisions": {k: {"count": count[k], "percent": pct(k)} for k in ("qualified", "review", "rejected")},
        "qualified_percent": pct("qualified"),
        "priority_tiers": dict(Counter(d.priority_tier for d in decisions)),
        "average_score": round(sum(scores) / total, 2) if total else None,
        "score_distribution": {b: sum(1 for s in scores if lo <= s < hi)
                               for b, lo, hi in (("1-2.9", 1, 3), ("3-4.9", 3, 5), ("5-6.9", 5, 7), ("7-8.4", 7, 8.5), ("8.5-10", 8.5, 10.01))},
        "common_rejection_reasons": rejection_reasons.most_common(),
        "review_reasons": review_reasons.most_common(),
        "qualified_rate_by_source": {k: {**v, "rate_percent": round(100 * v["qualified"] / v["total"], 1)}
                                     for k, v in sorted(by_source.items(), key=lambda kv: -kv[1]["total"])},
        "data_quality_issues_by_field": dict(issues.most_common()),
        "leads_with_data_issues": sum(1 for d in decisions if d.lead.issues),
        "llm": {
            "judgment_source_counts": dict(llm_sources),
            "llm_adjusted_leads": sum(1 for d in decisions if d.judgment.adjustment),
            "batches_sent": judge.batches_sent,
            "batch_splits": judge.batch_splits,
            "circuit_breaker_opened": judge.circuit_open,
            "circuit_breaker_reason": judge.circuit_reason or None,
            **judge.stats.to_dict(),
            "messages_from_llm": sum(1 for d in decisions if d.message_source == "llm"),
            "messages_from_template": sum(1 for d in decisions if d.message_source == "template"),
        },
        "efficiency": {
            "runtime_seconds": round(elapsed, 2),
            "seconds_per_lead": round(elapsed / total, 3) if total else None,
            "estimated_manual_minutes": round(total * manual_minutes),
            "note": f"Manual estimate assumes {manual_minutes} min per lead (brief: 8-12 min).",
        },
    }


def output_paths(out_dir: Path) -> dict[str, Path]:
    return {"json": out_dir / "output_report.json", "csv": out_dir / "leads_scored.csv", "md": out_dir / "summary.md"}


def write_outputs(report: dict, decisions: list[LeadDecision], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(out_dir)

    with open(paths["json"], "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    order = {"qualified": 0, "review": 1, "rejected": 2}
    rows = sorted(decisions, key=lambda d: (order[d.decision], d.priority_rank or 10 ** 6, -d.final_score))
    with open(paths["csv"], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lead_id", "decision", "priority_tier", "priority_rank", "score", "base_score", "llm_adjustment",
                    "name", "company", "company_size", "industry", "source", "last_interaction_date",
                    "next_action", "reasoning", "data_issues", "message_source", "outreach_message"])
        for d in rows:
            w.writerow([d.lead.lead_id, d.decision, d.priority_tier, d.priority_rank or "", d.final_score,
                        d.rubric.base_score, d.judgment.adjustment, d.lead.name or "", d.lead.company or "",
                        d.lead.company_size or "", d.lead.industry or "", d.lead.source or "",
                        d.lead.last_interaction.isoformat() if d.lead.last_interaction else "",
                        d.next_action, " | ".join(d.decision_reasons), " | ".join(i.issue for i in d.lead.issues),
                        d.message_source or "", d.outreach_message or ""])

    paths["md"].write_text(render_markdown(report), encoding="utf-8")
    return paths


def render_markdown(report: dict) -> str:
    m, s = report["run"], report["stats"]
    dec = s["decisions"]
    lines = [
        f"# Lead Qualification Summary - {m['input_file']}",
        "",
        f"Run `{m['run_id']}` | provider **{m['llm_provider']}** ({m['llm_model']}) | rubric v{m['rubric_version']} | "
        f"reference date {m['reference_date']}",
        "",
        f"**{s['total_processed']} leads processed** in {s['efficiency']['runtime_seconds']}s "
        f"(manual estimate: ~{s['efficiency']['estimated_manual_minutes']} min).",
        "",
        "| Decision | Count | % |", "|---|---|---|",
        *[f"| {k.title()} | {v['count']} | {v['percent']}% |" for k, v in dec.items()],
        "",
        "## Priority queue (contact in this order)", "",
        "| # | Tier | Score | Contact | Company | Why | Next action |", "|---|---|---|---|---|---|---|",
    ]
    for l in report["priority_queue"]:
        why = "; ".join(w.split(":")[0] for w in l["why"])
        lines.append(f"| {l['priority_rank']} | {l['priority_tier']} | {l['qualification_score']} | {l['name'] or '-'} | "
                     f"{l['company'] or '-'} | {why} | {l['next_action']} |")
    lines += ["", "## Needs human review", "", "| # | Score | Contact | Company | Reason |", "|---|---|---|---|---|"]
    for l in report["review_queue"]:
        reason = "; ".join(r for r in l["reasoning"] if not r.startswith("Score ")) or l["reasoning"][0]
        lines.append(f"| {l['priority_rank']} | {l['qualification_score']} | {l['name'] or '-'} | {l['company'] or '-'} | {reason} |")
    lines += ["", "## Disqualified", "", f"{dec['rejected']['count']} leads. Most common reasons:", ""]
    lines += [f"- {r} ({c})" for r, c in s["common_rejection_reasons"]] or ["- none"]
    lines += ["", "## Sample outreach messages", ""]
    for smp in report["sample_outreach_messages"]:
        lines += [f"### #{smp['priority_rank']} {smp['contact']} - {smp['company']} ({smp['angle']}, {smp['message_source']})",
                  "", "```", smp["message"], "```", ""]
    llm = s["llm"]
    lines += ["## Robustness", "",
              f"- LLM batches sent: {llm['batches_sent']} (API calls incl. retries: {llm['api_calls']}, retries: {llm['retries']}, "
              f"batch splits: {llm['batch_splits']}, invalid responses: {llm['invalid_responses']})",
              f"- Judgment source per lead: {llm['judgment_source_counts']}",
              f"- Circuit breaker opened: {llm['circuit_breaker_opened']}" + (f" ({llm['circuit_breaker_reason']})" if llm['circuit_breaker_reason'] else ""),
              f"- Leads with data-quality issues: {s['leads_with_data_issues']} - by field: {s['data_quality_issues_by_field']}",
              ""]
    return "\n".join(lines)
