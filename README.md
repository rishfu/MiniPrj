# Lead Intelligence System

A command-line tool that scores a CSV of leads (1–10), decides **qualified / review / rejected**, ranks a priority queue, writes personalised first messages, and outputs a report a sales team can act on. Rules give consistency; an LLM adds bounded judgment and writes the messages.

## How to run

```bash
pip install -r requirements.txt                      # only PyYAML is required
python main.py data/leads_full_scale_100.csv --provider mock   # offline: no key needed, template messages

cp .env.example .env                                 # add NVIDIA_API_KEY (or GROQ/GEMINI/OPENAI)
python main.py data/leads_full_scale_100.csv         # default provider: NVIDIA Nemotron (config.yaml)
python test_prompts.py -n 5 --show-prompt            # check the prompt on 5 leads before a full run
python main.py data/leads_testing.csv --simulate-failures 0.4     # inject API failures to test robustness
python -m unittest discover -s tests -v              # 35 tests
```

Outputs go to `output/<input-name>/`: `output_report.json` (full record), `leads_scored.csv` (open in Excel), `summary.md` (one-screen summary), `run.log`. The sample output for the 100-lead file is at `output_report.json` in the repo root.

## Qualification rubric (v1.2, in `config.yaml`)

The score is the sum of four factors: **company size** (2.5 points; 51–1000 staff is ideal), **industry fit** (2; core / adjacent / low tiers), **buying intent from lead source** (3.5; demo request > referral > sales call > webinar > content download > cold LinkedIn) and **recency** (2; within the last week down to over a year). The LLM can then nudge the score by up to ±1, and only with a stated reason. Leads scoring ≥ 7 are **qualified** (P1 at ≥ 8.5: contact within 24h). Leads at 6–6.9 go to **human review**, and below 6 are **rejected** (nurture or archive). Hard caps the LLM can't override keep micro (≤10 staff), very large (>20k) and stale (>1 year) leads at review at most. A lead also goes to review when data is missing, the company is unknown, the row is a duplicate, the LLM is unsure, or the decision would flip depending on a missing value.

## How it works

`intake (ingest.py) → rubric score (rubric.py) → LLM in batches of 10 (judge.py) → decide + rank (decide.py) → report (report.py)`.
The pipeline makes 10 API calls for 100 leads. It retries 429/5xx/timeouts with exponential backoff and jitter (honouring Retry-After), throttles to N requests a minute, re-asks for leads the LLM skipped, and splits a batch whose reply was unusable. If the LLM fails, it falls back to rubric-only scoring with template messages, and a circuit breaker stops calling a dead API. Every lead always gets a decision, and the report shows where each judgment came from. See **[docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md)** for the full design walkthrough.

## Assumptions and known limitations

- **We are "FlowPilot"**, a made-up workflow-automation SaaS. The brief doesn't name a product, and the rubric and messages depend on one. Edit `seller:` in `config.yaml` to change it.
- **Recency reference date**: the data is from 2023–24, so recency is measured from the latest date in the file, not from today. Use `--reference-date today` for live data.
- **The committed sample outputs were made with Gemini on the free tier**: `leads_full_scale_100` and `leads_edge_cases_extra` with `gemini-3.5-flash-lite`, and `leads_training` and `leads_testing` with `gemini-3.5-flash` (its free daily quota of 20 requests ran out before the larger files). Every lead got an LLM judgment. In the 100-lead run, all 71 outreach messages came from the LLM and 0 from templates, and the LLM adjusted 2 scores. The `leads_full_scale_100_chaos_demo` output is older and kept as a failure-handling demo.
- Only six columns are available, so there are no budget or timeline signals. Thresholds were tuned by eye on the sample files, since there's no ground truth. With real conversion data, the weights should be fitted to outcomes.
- The ~49% qualified rate on the 100-lead file reflects a curated sample. The P1/P2 ranking is what limits outreach to the team's capacity.
- Industry matching is a keyword lookup. Unmapped industries get a neutral score and are flagged, and the LLM may adjust them.
- The duplicate check only matches exact name and company. Emails or domains, which this data doesn't have, would be better.
- The free-tier model names in `config.yaml` change over time. Override them with `--model`.
