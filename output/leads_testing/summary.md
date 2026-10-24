# Lead Qualification Summary - leads_testing.csv

Run `20261024T085001Z-4827df` | provider **gemini** (gemini-3.5-flash) | rubric v1.2 | reference date 2024-01-20

**20 leads processed** in 90.97s (manual estimate: ~200 min).

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

### #1 Test_RecentEngagement - Hot Lead Corp (demo_followup, llm)

```
Hi Test,

Thank you for reaching out for a demo of FlowPilot today. With Hot Lead Corp having around 200 employees in the SaaS space, our platform is built to help teams automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets.

I would love to connect and show you how we can streamline your team's workflow transitions. Are you available for a brief call this Wednesday at 11:00 AM or Thursday at 3:00 PM?

Best regards,

Sam Rivera
Account Executive, FlowPilot
```

### #6 Test_WeekOldInteraction - Week Old Corp (event_followup, llm)

```
Hi Test_WeekOldInteraction,

Thank you for attending our recent workflow webinar last week. It was great to see representatives from Week Old Corp in the session. Given your team of 250 in the logistics industry, operational speed and visibility are critical.

FlowPilot can help you automate shipment-exception and carrier hand-offs so nothing sits in an inbox waiting for action. I put together a brief guide on reducing logistics communication delays that I think you will find useful. Would you be interested in taking a look?

Best regards,

Sam Rivera
Account Executive, FlowPilot
```

### #7 Test_UnknownIndustry - Mysterious Startup (warm_referral, llm)

```
Hi Test,

I am reaching out following up on the referral we received yesterday regarding Mysterious Startup. Knowing that your team has around 15 employees, we specialize in helping growing companies replace manual, email-driven hand-offs with automated workflows to eliminate bottlenecks.

I would love to learn more about your operational goals and discuss how FlowPilot can support your team. Do you have 15 minutes open later this week for a brief introductory conversation?

Best regards,

Sam Rivera
Account Executive, FlowPilot
```

### #2 Test_HighValueMatch - Perfect Fit Enterprise (demo_followup, llm)

```
Hi Test_HighValueMatch,

Thank you for reaching out for a demo of FlowPilot. With 2,000 employees in the SaaS space, managing cross-team execution at Perfect Fit Enterprise can quickly get complex. We help organizations like yours automate customer onboarding and renewal hand-offs so CS and Sales stop chasing spreadsheets.

I would love to walk you through a tailored demonstration of our platform. Are you available for a brief 20-minute call this Thursday at 10:00 AM or Friday at 2:00 PM?

Best regards,

Sam Rivera
Account Executive, FlowPilot
```

### #3 Test_MultipleInteractions - Active Company (demo_followup, llm)

```
Hi Test,

Thank you for submitting a demo request today for Active Company. With 500 employees in the finance sector, we know how critical operational rigor is. FlowPilot helps organizations like yours automate approval and compliance workflows with a full audit trail, ensuring seamless execution across teams.

I would be glad to schedule a tailored demonstration for your team. Are you available to connect this Thursday at 10:00 AM or Friday at 1:00 PM?

Best regards,

Sam Rivera
Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 2 (API calls incl. retries: 6, retries: 4, batch splits: 0, invalid responses: 0)
- Judgment source per lead: {'llm': 20}
- Circuit breaker opened: False
- Leads with data-quality issues: 8 - by field: {'company_size': 4, 'source': 4, 'last_interaction_date': 2, 'industry': 2, 'company': 1}
