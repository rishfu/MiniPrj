# Lead Qualification Summary - leads_edge_cases_extra.csv

Run `20261024T085624Z-2fa79f` | provider **gemini** (gemini-3.5-flash-lite) | rubric v1.2 | reference date 2024-01-20

**20 leads processed** in 6.76s (manual estimate: ~200 min).

| Decision | Count | % |
|---|---|---|
| Qualified | 6 | 30.0% |
| Review | 8 | 40.0% |
| Rejected | 6 | 30.0% |

## Priority queue (contact in this order)

| # | Tier | Score | Contact | Company | Why | Next action |
|---|---|---|---|---|---|---|
| 1 | P1 | 9.5 | - | Nimbus Cloud | Core mid-market (51-1000); Core vertical; Referral; Hot | P1: send first message via Email (warm intro) within 24 hours |
| 2 | P1 | 8.5 | Liam Brown | Future Date Co | Core mid-market (51-1000); Core vertical; Inbound demo request; Last interaction date unknown | P1: send first message via Email (reply to demo request) within 24 hours |
| 3 | P2 | 8.0 | Emma Wilson | ScaleUp Labs | Upper mid-market (1001-5000); Core vertical; Sales call; Hot | P2: send first message via Email (call recap) within 3 business days |
| 4 | P2 | 8.0 | Tom Hughes | Hughes Logistics | Core mid-market (51-1000); Core vertical; Referral; Last interaction date unknown | P2: send first message via Email (warm intro) within 3 business days |
| 5 | P2 | 7.8 | Mason Reed | Reed & Co | Small business (11-50); Adjacent vertical; Referral; Hot | P2: send first message via Email (warm intro) within 3 business days |
| 6 | P2 | 7.5 | Jordan Lee | Vertex Robotics | Company size unknown; Adjacent vertical; Inbound demo request; Hot | P2: send first message via Email (reply to demo request) within 3 business days |

## Needs human review

| # | Score | Contact | Company | Reason |
|---|---|---|---|---|
| 1 | 6.8 | Maria Garcia | FreshCart | Score 6.8 is in the 6.0-7.0 'too close to call' band |
| 2 | 6.5 | Wei Zhang | Orbital Dynamics | LLM adjustment +0.5: Space Technology aligns closely with advanced engineering workflows, making industry fit stronger than the neutral default. |
| 3 | 6.3 | Grace Kim | Pulse Health | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 4 | 6.3 | Grace Kim | Pulse Health | Needs human review - data problem: possible duplicate of L016 (same name and company) |
| 5 | 6.0 | Sarah Quinn | Solo Studio | Capped at 6.0: Company has 10 or fewer employees: capped at review - too small for our product unless a human sees a special case |
| 6 | 6.0 | Peter Grant | Legacy Systems Inc | Capped at 6.0: No contact in over a year: capped at review - contact details and need must be re-verified first |
| 7 | 4.5 | Linda Park | BrightWave Media | Unknown company size (scored with a default); Unknown intent signal (scored with a default); Needs human review - could qualify if unknown company_size, intent_signal turns out favourable (best case 8.5) |
| 8 | 2.8 | Anonymous | - | Unknown company size (scored with a default); Unknown industry fit (scored with a default); Unknown intent signal (scored with a default); Unknown recency (scored with a default); Needs human review - data problem: missing company name - cannot personalise or verify the account; Needs human review - insufficient data (company_size, industry, source, last_interaction_date missing); score not reliable |

## Disqualified

6 leads. Most common reasons:

- Weak buying-intent signal (cold or early-stage source) (4)
- Company size outside target range (3)
- Unknown industry fit (scored with a default) (2)
- No recent interaction (2)
- Unknown company size (scored with a default) (1)

## Sample outreach messages

### #1 Unknown contact - Nimbus Cloud (warm_referral, llm)

```
Hi there, it's great to connect following the recent referral regarding Nimbus Cloud. We regularly help SaaS teams automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets. I'd love to share a few quick examples of how we do this. Do you have ten minutes later this week for a brief introductory chat? Best, Sam Rivera, Account Executive, FlowPilot.
```

### #2 Liam Brown - Future Date Co (demo_followup, llm)

```
Hi Liam,

Thanks for requesting a demo for Future Date Co. Since you are in the SaaS space with a growing team, I wanted to reach out directly. FlowPilot can help you automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets.

Do you have 15 minutes this Tuesday or Wednesday to connect?

Best,
Sam Rivera, Account Executive, FlowPilot
```

### #3 Emma Wilson - ScaleUp Labs (call_recap, llm)

```
Hi Emma,

It was great speaking with you regarding ScaleUp Labs earlier this week. Given your team size of 1,200, I wanted to follow up on how we discussed streamlining your processes. FlowPilot can help automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets.

Would you be open to a quick look at a workflow demo this Thursday or Friday?

Best,
Sam Rivera, Account Executive, FlowPilot
```

### #4 Tom Hughes - Hughes Logistics (warm_referral, llm)

```
Hi Tom, thanks for the warm introduction regarding Hughes Logistics. We work closely with logistics providers to automate shipment-exception and carrier hand-offs so nothing sits in an inbox. I'd love to connect and share how we've streamlined similar workflows for other teams. Do you have a few minutes for a brief call this week? Best, Sam Rivera, Account Executive, FlowPilot.
```

### #5 Mason Reed - Reed & Co (warm_referral, llm)

```
Hi Mason,

It is great to connect with Reed & Co following the recent warm referral. For growing professional services teams like yours, eliminating manual work is a game changer. FlowPilot can help you replace manual, email-driven hand-offs with automated workflows.

Are you available for a brief conversation sometime this week?

Best,
Sam Rivera, Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 2 (API calls incl. retries: 2, retries: 0, batch splits: 0, invalid responses: 0)
- Judgment source per lead: {'llm': 20}
- Circuit breaker opened: False
- Leads with data-quality issues: 13 - by field: {'company_size': 7, 'last_interaction_date': 4, 'source': 2, 'name': 1, 'company': 1, 'industry': 1, 'row': 1}
