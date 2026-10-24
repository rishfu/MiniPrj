# Lead Qualification Summary - leads_edge_cases_extra.csv

Run `20261024T081304Z-8db9e7` | provider **mock** (mock) | rubric v1.2 | reference date 2024-01-20

**20 leads processed** in 0.01s (manual estimate: ~200 min).

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
| 2 | 6.3 | Grace Kim | Pulse Health | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 3 | 6.3 | Grace Kim | Pulse Health | Needs human review - data problem: possible duplicate of L016 (same name and company) |
| 4 | 6.0 | Sarah Quinn | Solo Studio | Capped at 6.0: Company has 10 or fewer employees: capped at review - too small for our product unless a human sees a special case |
| 5 | 6.0 | Wei Zhang | Orbital Dynamics | Score 6.0 is in the 6.0-7.0 'too close to call' band |
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

### #1 Unknown contact - Nimbus Cloud (warm_referral, template)

```
Hi there,

You were referred to us earlier this week, so I wanted to reach out personally. Teams in SaaS often use FlowPilot to automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets, and at Nimbus Cloud's size (a 120-person organisation) that tends to pay off fast. Would a 20-minute call next week be useful to see if it fits?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #2 Liam Brown - Future Date Co (demo_followup, template)

```
Hi Liam,

Thanks for requesting a FlowPilot demo recently. For a 60-person organisation in SaaS like Future Date Co, the quickest win is usually to automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets. I'd like to tailor the demo to your current hand-offs - would Tuesday at 10am or Thursday at 2pm work for 30 minutes?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #3 Emma Wilson - ScaleUp Labs (call_recap, template)

```
Hi Emma,

Thanks again for the conversation just now. As a quick recap: for ScaleUp Labs, an organisation of 1,200 people in SaaS, the clearest opportunity is to automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets. As a next step, I can put together a short workflow map for your team - could we book 30 minutes this week to review it together?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #4 Tom Hughes - Hughes Logistics (warm_referral, template)

```
Hi Tom,

You were referred to us recently, so I wanted to reach out personally. Teams in Logistics often use FlowPilot to automate shipment-exception and carrier hand-offs so nothing sits in an inbox, and at Hughes Logistics' size (a 400-person organisation) that tends to pay off fast. Would a 20-minute call next week be useful to see if it fits?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #5 Mason Reed - Reed & Co (warm_referral, template)

```
Hi Mason,

You were referred to us earlier this week, so I wanted to reach out personally. Teams in Professional Services often use FlowPilot to replace manual, email-driven hand-offs with automated workflows, and at Reed & Co's size (a team of about 38) that tends to pay off fast. Would a 20-minute call next week be useful to see if it fits?

Best,
Sam Rivera
Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 2 (API calls incl. retries: 2, retries: 0, batch splits: 0, invalid responses: 0)
- Judgment source per lead: {'mock': 20}
- Circuit breaker opened: False
- Leads with data-quality issues: 13 - by field: {'company_size': 7, 'last_interaction_date': 4, 'source': 2, 'name': 1, 'company': 1, 'industry': 1, 'row': 1}
