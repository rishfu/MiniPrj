# Lead Qualification Summary - leads_testing.csv

Run `20261024T081304Z-a0bc32` | provider **mock** (mock) | rubric v1.2 | reference date 2024-01-20

**20 leads processed** in 0.01s (manual estimate: ~200 min).

| Decision | Count | % |
|---|---|---|
| Qualified | 7 | 35.0% |
| Review | 9 | 45.0% |
| Rejected | 4 | 20.0% |

## Priority queue (contact in this order)

| # | Tier | Score | Contact | Company | Why | Next action |
|---|---|---|---|---|---|---|
| 1 | P1 | 10.0 | Test_RecentEngagement | Hot Lead Corp | Core mid-market (51-1000); Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 2 | P1 | 9.3 | Test_HighValueMatch | Perfect Fit Enterprise | Upper mid-market (1001-5000); Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 3 | P1 | 9.0 | Test_MultipleInteractions | Active Company | Core mid-market (51-1000); Adjacent vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 4 | P1 | 9.0 | Test_SMBAverage | Average SMB Co | Core mid-market (51-1000); Adjacent vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 5 | P1 | 8.5 | Test_MissingSize | Test Inc | Company size unknown; Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 6 | P2 | 7.8 | Test_WeekOldInteraction | Week Old Corp | Core mid-market (51-1000); Core vertical; Webinar attendee; Hot | P2: send first message via Email (webinar follow-up) within 3 business days |
| 7 | P2 | 7.3 | Test_UnknownIndustry | Mysterious Startup | Small business (11-50); Industry unknown; Referral; Hot | P2: send first message via Email (warm intro) within 3 business days |

## Needs human review

| # | Score | Contact | Company | Reason |
|---|---|---|---|---|
| 1 | 7.8 | Test_MissingName | - | Needs human review - data problem: missing company name - cannot personalise or verify the account |
| 2 | 6.5 | Test_MidMarketSoft | Mid Market Software | Score 6.5 is in the 6.0-7.0 'too close to call' band |
| 3 | 6.3 | Test_NoSourceInfo | Source Unknown Corp | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 4 | 6.3 | Test_GovernmentBuyer | Government Tech | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 5 | 6.0 | Test_VeryLargeEnterprise | Global Fortune 500 Corp | Capped at 6.0: Over 20,000 employees: capped at review - verify the record and consider routing to an enterprise team |
| 6 | 6.0 | Test_VeryRecentSignup | Brand New Startup | Capped at 6.0: Company has 10 or fewer employees: capped at review - too small for our product unless a human sees a special case |
| 7 | 5.8 | Test_PartialData | Tech Partial | Unknown company size (scored with a default); Unknown intent signal (scored with a default); Needs human review - insufficient data (company_size, source missing); score not reliable |
| 8 | 5.8 | Test_MissingDate | Mystery Co | Unknown intent signal (scored with a default); Unknown recency (scored with a default); Needs human review - insufficient data (source, last_interaction_date missing); score not reliable |
| 9 | 2.8 | Test_NameOnly | James Wilson | Unknown company size (scored with a default); Unknown industry fit (scored with a default); Unknown intent signal (scored with a default); Unknown recency (scored with a default); Needs human review - insufficient data (company_size, industry, source, last_interaction_date missing); score not reliable |

## Disqualified

4 leads. Most common reasons:

- Company size outside target range (3)
- Weak buying-intent signal (cold or early-stage source) (2)
- No recent interaction (2)
- Low-fit or unknown industry (1)

## Sample outreach messages

### #1 Test_RecentEngagement - Hot Lead Corp (demo_followup, template)

```
Hi Test_RecentEngagement,

Thanks for requesting a FlowPilot demo just now. For a 200-person organisation in SaaS like Hot Lead Corp, the quickest win is usually to automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets. I'd like to tailor the demo to your current hand-offs - would Tuesday at 10am or Thursday at 2pm work for 30 minutes?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #6 Test_WeekOldInteraction - Week Old Corp (event_followup, template)

```
Hi Test_WeekOldInteraction,

Thanks for joining our webinar earlier this week. Many Logistics teams in the audience asked how to automate shipment-exception and carrier hand-offs so nothing sits in an inbox, so I put together a two-page example that fits a 250-person organisation like Week Old Corp. Shall I send it over, or would a short walkthrough be more useful?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #7 Test_UnknownIndustry - Mysterious Startup (warm_referral, template)

```
Hi Test_UnknownIndustry,

You were referred to us just now, so I wanted to reach out personally. Teams in your industry often use FlowPilot to replace manual, email-driven hand-offs with automated workflows, and at Mysterious Startup's size (a team of about 15) that tends to pay off fast. Would a 20-minute call next week be useful to see if it fits?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #2 Test_HighValueMatch - Perfect Fit Enterprise (demo_followup, template)

```
Hi Test_HighValueMatch,

Thanks for requesting a FlowPilot demo just now. For an organisation of 2,000 people in SaaS like Perfect Fit Enterprise, the quickest win is usually to automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets. I'd like to tailor the demo to your current hand-offs - would Tuesday at 10am or Thursday at 2pm work for 30 minutes?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #3 Test_MultipleInteractions - Active Company (demo_followup, template)

```
Hi Test_MultipleInteractions,

Thanks for requesting a FlowPilot demo just now. For a 500-person organisation in Finance like Active Company, the quickest win is usually to automate approval and compliance workflows with a full audit trail. I'd like to tailor the demo to your current hand-offs - would Tuesday at 10am or Thursday at 2pm work for 30 minutes?

Best,
Sam Rivera
Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 2 (API calls incl. retries: 2, retries: 0, batch splits: 0, invalid responses: 0)
- Judgment source per lead: {'mock': 20}
- Circuit breaker opened: False
- Leads with data-quality issues: 8 - by field: {'company_size': 4, 'source': 4, 'last_interaction_date': 2, 'industry': 2, 'company': 1}
