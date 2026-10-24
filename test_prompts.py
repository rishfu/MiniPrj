#!/usr/bin/env python3
"""
Try the prompt on a handful of leads BEFORE running a full batch.

Shows exactly what is sent to the LLM, the raw reply, and how each reply is
validated, so you can iterate on prompts in config.yaml / qualifier/prompts.py
cheaply (one API call) instead of discovering problems after 100 leads.

    python test_prompts.py                                   # 5 training leads, mock provider
    python test_prompts.py --provider groq -n 8              # real LLM
    python test_prompts.py --file data/leads_testing.csv --show-prompt
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from qualifier.ingest import apply_reference_date, load_leads, resolve_reference_date
from qualifier.judge import parse_results
from qualifier.llm_client import LLMError, build_provider, load_dotenv
from qualifier.messages import validate_message, value_prop_for
from qualifier.prompts import build_system_prompt, build_user_prompt, lead_payload
from qualifier.rubric import Rubric

ROOT = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(ROOT / "data" / "leads_training.csv"))
    ap.add_argument("-n", type=int, default=5, help="number of leads to send (default 5)")
    ap.add_argument("--provider")
    ap.add_argument("--model")
    ap.add_argument("--show-prompt", action="store_true", help="print the full system + user prompt")
    args = ap.parse_args()

    load_dotenv(str(ROOT / ".env"))
    cfg = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
    rubric = Rubric(cfg["rubric"])
    leads, _ = load_leads(args.file)
    ref = resolve_reference_date(leads)
    apply_reference_date(leads, ref)
    leads = leads[: args.n]

    payloads = []
    for lead in leads:
        rr = rubric.score(lead, ref)
        payloads.append(lead_payload(lead, rr, True, value_prop_for(lead.industry, cfg["seller"]["value_props"])))
    system = build_system_prompt(cfg["seller"], rubric.summary_text())
    user = build_user_prompt(payloads)

    if args.show_prompt:
        print("=" * 30, "SYSTEM PROMPT", "=" * 30, f"\n{system}\n")
        print("=" * 30, "USER PROMPT", "=" * 32, f"\n{user}\n")
    print(f"Prompt size: ~{(len(system) + len(user)) // 4} tokens for {len(leads)} leads")

    provider = build_provider(cfg["llm"], args.provider, args.model)
    print(f"Calling {provider.name} ({provider.model}) ...")
    try:
        raw = provider.complete(system, user)
    except LLMError as e:
        print(f"LLM call failed: {type(e).__name__}: {e}")
        return 1
    print("=" * 30, "RAW RESPONSE", "=" * 31)
    print(raw[:4000])

    print("=" * 30, "VALIDATION", "=" * 33)
    adj = cfg["rubric"]["llm_adjustment"]
    try:
        results = parse_results(raw, {p["lead_id"] for p in payloads}, adj["max_abs"], adj["step"], provider.name)
    except LLMError as e:
        print(f"Response rejected: {e}")
        return 1
    for lead, p in zip(leads, payloads):
        j = results.get(lead.lead_id)
        if not j:
            print(f"{lead.lead_id}: MISSING from response")
            continue
        ok, why = validate_message(j.outreach_message, lead)
        print(f"{lead.lead_id} {lead.company}: base {p['rubric']['base_score']} adj {j.adjustment:+} "
              f"conf {j.confidence} | message {'OK' if ok else 'REJECTED: ' + why}")
        if j.adjustment_reason:
            print(f"    reason: {j.adjustment_reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
