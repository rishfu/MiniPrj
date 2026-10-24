# Lead Qualification Summary - leads_training.csv

Run `20261024T081304Z-106598` | provider **mock** (mock) | rubric v1.2 | reference date 2024-01-20

**29 leads processed** in 0.01s (manual estimate: ~290 min).

| Decision | Count | % |
|---|---|---|
| Qualified | 12 | 41.4% |
| Review | 7 | 24.1% |
| Rejected | 10 | 34.5% |

## Priority queue (contact in this order)

| # | Tier | Score | Contact | Company | Why | Next action |
|---|---|---|---|---|---|---|
| 1 | P1 | 10.0 | Jack White | Digital Marketing Agency | Core mid-market (51-1000); Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 2 | P1 | 9.3 | Alice Chen | CloudScale AI | Small business (11-50); Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 3 | P1 | 9.3 | Nathan Brooks | Enterprise Solutions Corp | Upper mid-market (1001-5000); Core vertical; Inbound demo request; Hot | P1: send first message via Email (reply to demo request) within 24 hours |
| 4 | P1 | 9.0 | Samuel Lee | Cybersecurity Startup | Core mid-market (51-1000); Core vertical; Referral; Warm | P1: send first message via Email (warm intro) within 24 hours |
| 5 | P1 | 8.8 | Leon Chen | FinTech Startup | Small business (11-50); Core vertical; Referral; Hot | P1: send first message via Email (warm intro) within 24 hours |
| 6 | P2 | 8.0 | Yuki Tanaka | Travel Technology | Core mid-market (51-1000); Adjacent vertical; Referral; Warm | P2: send first message via Email (warm intro) within 3 business days |
| 7 | P2 | 8.0 | Zara Hassan | Education Institution | Core mid-market (51-1000); Adjacent vertical; Inbound demo request; Cooling | P2: send first message via Email (reply to demo request) within 3 business days |
| 8 | P2 | 7.5 | Emma Thompson | RetailWorks Solutions | Core mid-market (51-1000); Adjacent vertical; Inbound demo request; Cold | P2: send first message via Email (reply to demo request) within 3 business days |
| 9 | P2 | 7.3 | Henry Park | EdTech Innovations | Core mid-market (51-1000); Core vertical; Content download; Hot | P2: send first message via Email (content follow-up) within 3 business days |
| 10 | P2 | 7.3 | Victor Moore | Real Estate Platform | Core mid-market (51-1000); Adjacent vertical; Sales call; Warm | P2: send first message via Email (call recap) within 3 business days |
| 11 | P2 | 7.3 | Xavier Lopez | Data Analytics Firm | Core mid-market (51-1000); Core vertical; Webinar attendee; Warm | P2: send first message via Email (webinar follow-up) within 3 business days |
| 12 | P2 | 7.3 | Tina Patel | Energy Solutions | Core mid-market (51-1000); Adjacent vertical; Inbound demo request; Very cold | P2: send first message via Email (reply to demo request) within 3 business days |

## Needs human review

| # | Score | Contact | Company | Reason |
|---|---|---|---|---|
| 1 | 6.8 | Karen Miller | InsurancePro | Score 6.8 is in the 6.0-7.0 'too close to call' band |
| 2 | 6.8 | Bella Cross | Legal Services Firm | Score 6.8 is in the 6.0-7.0 'too close to call' band |
| 3 | 6.5 | Frank Liu | Healthcare Systems Ltd | Score 6.5 is in the 6.0-7.0 'too close to call' band |
| 4 | 6.5 | Aaron Benj | Supply Chain Co | Score 6.5 is in the 6.0-7.0 'too close to call' band |
| 5 | 6.3 | Quinn Matthews | Consulting Firm | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 6 | 6.0 | David Moore | StartupXYZ | Capped at 6.0: Company has 10 or fewer employees: capped at review - too small for our product unless a human sees a special case |
| 7 | 6.0 | Pamela White | Pharma Research Inc | Score 6.0 is in the 6.0-7.0 'too close to call' band |

## Disqualified

10 leads. Most common reasons:

- Weak buying-intent signal (cold or early-stage source) (10)
- No recent interaction (3)
- Low-fit or unknown industry (2)
- Company size outside target range (1)

## Sample outreach messages

### #1 Jack White - Digital Marketing Agency (demo_followup, template)

```
Hi Jack,

Thanks for requesting a FlowPilot demo just now. For a 120-person organisation in Marketing like Digital Marketing Agency, the quickest win is usually to automate campaign-approval and client-onboarding workflows. I'd like to tailor the demo to your current hand-offs - would Tuesday at 10am or Thursday at 2pm work for 30 minutes?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #4 Samuel Lee - Cybersecurity Startup (warm_referral, template)

```
Hi Samuel,

You were referred to us a few weeks ago, so I wanted to reach out personally. Teams in Cybersecurity often use FlowPilot to automate incident-triage and access-request workflows with an audit trail, and at Cybersecurity Startup's size (a 60-person organisation) that tends to pay off fast. Would a 20-minute call next week be useful to see if it fits?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #9 Henry Park - EdTech Innovations (content_followup, template)

```
Hi Henry,

I saw you downloaded one of our guides earlier this week - I hope it was useful. One idea that tends to land well with EdTech teams like EdTech Innovations is to automate learner-onboarding and content-approval workflows. If it would help, I'm happy to share a 10-minute example tailored to a 75-person organisation. No pressure either way.

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #10 Victor Moore - Real Estate Platform (call_recap, template)

```
Hi Victor,

Thanks again for the conversation a few weeks ago. As a quick recap: for Real Estate Platform, a 250-person organisation in Real Estate, the clearest opportunity is to automate lease, maintenance and tenant-request workflows. As a next step, I can put together a short workflow map for your team - could we book 30 minutes this week to review it together?

Best,
Sam Rivera
Account Executive, FlowPilot
```

### #11 Xavier Lopez - Data Analytics Firm (event_followup, template)

```
Hi Xavier,

Thanks for joining our webinar a few weeks ago. Many Analytics teams in the audience asked how to replace manual, email-driven hand-offs with automated workflows, so I put together a two-page example that fits a 110-person organisation like Data Analytics Firm. Shall I send it over, or would a short walkthrough be more useful?

Best,
Sam Rivera
Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 3 (API calls incl. retries: 3, retries: 0, batch splits: 0, invalid responses: 0)
- Judgment source per lead: {'mock': 29}
- Circuit breaker opened: False
- Leads with data-quality issues: 0 - by field: {}
