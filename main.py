#!/usr/bin/env python3
"""
Lead Intelligence System - command-line entry point.

Examples:
    python main.py data/leads_full_scale_100.csv                     # offline (mock LLM)
    python main.py data/leads_full_scale_100.csv --provider groq     # real LLM (needs GROQ_API_KEY)
    python main.py data/leads_testing.csv --simulate-failures 0.4    # prove error handling works
    python main.py data/leads.csv --no-llm                           # rubric only

Exit codes: 0 = success, 1 = configuration problem, 2 = input file problem.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from qualifier.ingest import IngestError
from qualifier.llm_client import load_dotenv
from qualifier.pipeline import run

ROOT = Path(__file__).resolve().parent


def setup_logging(verbose: bool, log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(fmt)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root = logging.getLogger("lead_qualifier")
    root.setLevel(logging.DEBUG)
    root.handlers[:] = [console, file_handler]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Auto-qualify leads from a CSV using a rubric + LLM.")
    ap.add_argument("input", help="CSV with columns name,company,company_size,industry,source,last_interaction_date")
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--provider", choices=["mock", "groq", "gemini", "openai"], help="overrides config llm.provider")
    ap.add_argument("--model", help="overrides the provider's default model")
    ap.add_argument("--batch-size", type=int, help="leads per LLM call (default from config)")
    ap.add_argument("--output-dir", help="default: output/<input file name>/")
    ap.add_argument("--reference-date", help="'auto' (latest date in file), 'today', or YYYY-MM-DD")
    ap.add_argument("--simulate-failures", type=float, default=0.0, metavar="RATE",
                    help="inject random API failures at this rate (0-1) to test robustness")
    ap.add_argument("--no-llm", action="store_true", help="rubric only; template messages")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    load_dotenv(str(ROOT / ".env"))
    try:
        with open(args.config, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1
    if args.batch_size:
        config["llm"]["batch_size"] = args.batch_size

    out_dir = Path(args.output_dir) if args.output_dir else ROOT / config["run"].get("output_root", "output") / Path(args.input).stem
    setup_logging(args.verbose, out_dir / "run.log")

    try:
        report = run(args.input, config, provider_name=args.provider, model=args.model, out_dir=out_dir,
                     reference_date=args.reference_date, failure_rate=args.simulate_failures,
                     use_llm=not args.no_llm)
    except IngestError as e:
        logging.getLogger("lead_qualifier").error("%s", e)
        return 2
    except ValueError as e:
        logging.getLogger("lead_qualifier").error("Configuration error: %s", e)
        return 1

    s = report["stats"]
    d = s["decisions"]
    print("\n" + "=" * 64)
    print(f" Processed {s['total_processed']} leads with {report['run']['llm_provider']} in "
          f"{s['efficiency']['runtime_seconds']}s")
    print(f"   qualified {d['qualified']['count']:>3} ({d['qualified']['percent']}%)   "
          f"review {d['review']['count']:>3} ({d['review']['percent']}%)   "
          f"rejected {d['rejected']['count']:>3} ({d['rejected']['percent']}%)")
    llm = s["llm"]
    print(f"   LLM: {llm['batches_sent']} batches, {llm['api_calls']} calls, {llm['retries']} retries, "
          f"{llm['judgment_source_counts']}")
    print(" Top of the priority queue:")
    for l in report["priority_queue"][:5]:
        print(f"   #{l['priority_rank']:<2} {l['priority_tier']}  {l['qualification_score']:>4}  {l['name']} - {l['company']}")
    print(" Outputs:")
    for v in report["output_files"].values():
        print(f"   {v}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
