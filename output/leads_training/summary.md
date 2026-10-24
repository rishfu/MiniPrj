# Lead Qualification Summary - leads_training.csv

Run `20261024T084705Z-8c71df` | provider **gemini** (gemini-3.5-flash) | rubric v1.2 | reference date 2024-01-20

**29 leads processed** in 175.82s (manual estimate: ~290 min).

| Decision | Count | % |
|---|---|---|
| Qualified | 11 | 37.9% |
| Review | 8 | 27.6% |
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

## Needs human review

| # | Score | Contact | Company | Reason |
|---|---|---|---|---|
| 1 | 6.8 | Karen Miller | InsurancePro | Score 6.8 is in the 6.0-7.0 'too close to call' band |
| 2 | 6.8 | Bella Cross | Legal Services Firm | Score 6.8 is in the 6.0-7.0 'too close to call' band |
| 3 | 6.8 | Tina Patel | Energy Solutions | LLM adjustment -0.5: The high intent signal from the inbound demo request is significantly weakened by the 94-day lapse in communication. |
| 4 | 6.5 | Frank Liu | Healthcare Systems Ltd | Score 6.5 is in the 6.0-7.0 'too close to call' band |
| 5 | 6.5 | Aaron Benj | Supply Chain Co | Score 6.5 is in the 6.0-7.0 'too close to call' band |
| 6 | 6.3 | Quinn Matthews | Consulting Firm | Score 6.3 is in the 6.0-7.0 'too close to call' band |
| 7 | 6.0 | David Moore | StartupXYZ | Capped at 6.0: Company has 10 or fewer employees: capped at review - too small for our product unless a human sees a special case |
| 8 | 6.0 | Pamela White | Pharma Research Inc | Score 6.0 is in the 6.0-7.0 'too close to call' band |

## Disqualified

10 leads. Most common reasons:

- Weak buying-intent signal (cold or early-stage source) (10)
- No recent interaction (3)
- Low-fit or unknown industry (2)
- Company size outside target range (1)

## Sample outreach messages

### #1 Jack White - Digital Marketing Agency (demo_followup, llm)

```
Hi Jack,

Thanks for submitting a demo request yesterday. For a 120-person team at Digital Marketing Agency, maintaining momentum across client accounts is crucial in the marketing industry.

FlowPilot allows teams to automate campaign-approval and client-onboarding workflows so your team can focus on strategy rather than tracking manual updates. I would love to walk you through a short demo this week. Are you available for a brief call Wednesday at 10:00 AM or Thursday at 2:00 PM?

Best regards,
Sam Rivera
Account Executive, FlowPilot
```

### #4 Samuel Lee - Cybersecurity Startup (warm_referral, llm)

```
Hi Samuel,

I was recently referred to you and wanted to reach out regarding Cybersecurity Startup. For a fast-growing cybersecurity team of 60, maintaining strict control over internal processes while responding swiftly to incidents is essential.

FlowPilot enables security teams to automate incident-triage and access-request workflows with an audit trail, keeping cross-functional hand-offs seamless and fully compliance-ready.

I would love to schedule a short call to introduce FlowPilot and see how we can support your operations. Are you open to connecting for 15 minutes later this week?

Best regards,
Sam Rivera
Account Executive, FlowPilot
```

### #9 Henry Park - EdTech Innovations (content_followup, llm)

```
Hi Henry,

I noticed you downloaded our content resource 6 days ago. For EdTech Innovations with a 75-person team, optimizing internal workflows is critical for scaling in the EdTech space.

FlowPilot helps teams automate learner-onboarding and content-approval workflows. A key takeaway from our research is that automating hand-offs reduces turnaround times significantly across departments. I would be glad to share a brief case study on how similar teams manage this if you are interested.

Best regards,
Sam Rivera
Account Executive, FlowPilot
```

### #10 Victor Moore - Real Estate Platform (call_recap, llm)

```
Hi Victor,

Thanks for taking the time to speak with us two weeks ago about Real Estate Platform. Following up on our sales call, I wanted to reconnect on how FlowPilot can help your team of 250 automate lease, maintenance, and tenant-request workflows. Moving away from manual hand-offs can significantly speed up response times for your property managers.

Are you open to a brief follow-up call this Thursday to review a tailored workflow demo and discuss next steps?

Best,
Sam Rivera, Account Executive, FlowPilot
```

### #11 Xavier Lopez - Data Analytics Firm (event_followup, llm)

```
Hi Xavier,

Thank you for attending our recent FlowPilot webinar about a month ago. I noticed your work at Data Analytics Firm and wanted to share a quick resource on how teams of 110 employees replace manual, email-driven hand-offs with automated workflows. In fast-paced analytics organizations, removing these manual operational bottlenecks can streamline cross-functional projects and increase delivery speed.

I would love to send over a short guide on optimizing workflow hand-offs if you are interested.

Best,
Sam Rivera, Account Executive, FlowPilot
```

## Robustness

- LLM batches sent: 5 (API calls incl. retries: 10, retries: 5, batch splits: 1, invalid responses: 1)
- Judgment source per lead: {'llm': 29}
- Circuit breaker opened: False
- Leads with data-quality issues: 0 - by field: {}
