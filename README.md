# 🛡️ Agentic Content Sentinel

An AI agent that automatically researches DevOps topics, writes a technical article, and publishes it to DEV.to and Hashnode — with your approval before anything goes live.

Every post is written by AI, reviewed by you, and deployed by a GitHub Action. No servers. No dashboards. Just a GitHub Issue you comment on.

---

## What it does

1. **Scouts** — twice a week, the agent searches the web for fresh, high-signal DevOps content across 9 topic areas (AI for DevOps, SRE, GitOps, Security, Observability, Cost Optimisation, MLOps, Production Troubleshooting, IaC)
2. **Writes** — a 600-800 word technical article using Llama 3.3-70b, with code blocks and concrete takeaways
3. **Asks you** — opens a GitHub Issue with the draft. You read it, edit if you want, then comment `/approve`
4. **Publishes** — automatically posts to DEV.to and Hashnode, generates a ready-to-paste Medium draft and Substack note in the closed issue comment

---

## Quick Start

### 1. Fork and clone

```bash
git clone https://github.com/vmprachi7/agentic-sentinel.git
cd agentic-sentinel
```

### 2. Install dependencies locally

```bash
pip install requests tavily-python langchain-groq python-dotenv
```

### 3. Set up your `.env` file

```bash
cp .env.example .env
# fill in your keys — see Prerequisites below
```

### 4. Test the scout locally

```bash
python scout.py
# This will create a real GitHub Issue in your repo
```

### 5. Set secrets in GitHub

Go to **Settings → Secrets and variables → Actions** and add all keys from the Prerequisites section below.

### 6. Set workflow permissions

Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.

### 7. Let it run

The pipeline triggers automatically every Monday and Thursday at 03:30 UTC. You will receive a GitHub notification email when a new draft issue is created. Comment `/approve` on the issue to publish.

---

## Prerequisites

You need accounts and API keys for the following:

| Service | What it's for | Where to get the key |
|---|---|---|
| [Groq](https://console.groq.com) | Runs the LLM (free tier available) | console.groq.com → API Keys |
| [Tavily](https://tavily.com) | Web search for the agent (free tier available) | app.tavily.com → API Keys |
| [DEV.to](https://dev.to/settings/extensions) | Publishes your article | dev.to → Settings → Extensions → API Key |
| [Hashnode](https://hashnode.com/settings/developer) | Mirrors your article | hashnode.com → Settings → Developer → Access Token |
| GitHub PAT | Creates issues, closes them | Settings → Developer settings → Personal access tokens → repo scope |

Optional (for Hashnode):

| Secret name | Value |
|---|---|
| `HASHNODE_TOKEN` | Your Hashnode personal access token |
| `HASHNODE_PUBLICATION_ID` | Found at hashnode.com → Your blog → Settings → bottom of page |

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| LLM | Llama 3.3-70b via Groq | Fast inference, free tier, strong technical writing |
| Web search | Tavily AI | Built for LLM retrieval, supports time-range filtering |
| Orchestration | GitHub Actions | Zero infrastructure, native secret management, event-driven |
| State / approval | GitHub Issues | Audit trail, email notifications, no external database |
| Primary publication | DEV.to | Google-indexed, developer audience, free API |
| Mirror publication | Hashnode | 500k+ developer community, own feed algorithm |
| Language | Python 3.9 | Simple, readable, minimal dependencies |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  TRIGGER — GitHub Actions                                     │
│  Cron: Mon & Thu 03:30 UTC  OR  manual workflow_dispatch     │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  SCOUT AGENT — scout.py                                       │
│                                                               │
│  1. Fetch last 15 issue titles  →  dedup memory              │
│  2. Pick uncovered topic area from 9 categories              │
│  3. Run 3-4 Tavily searches (time_range=week)                │
│  4. Llama 3.3-70b writes 600-800 word article                │
│  5. Llama 3.3-70b generates punchy title                     │
└─────────────────────────┬────────────────────────────────────┘
                          │  GitHub Issues API
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  CONTROL PLANE — GitHub Issue                                 │
│  label: pending-approval                                      │
│  body: full article draft                                     │
│  @mention: email notification to you                         │
└─────────────────────────┬────────────────────────────────────┘
                          │  You read, optionally edit, comment /approve
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  PUBLISH AGENT — publish.py                                   │
│                                                               │
│  1. Groq generates tags (4 for DEV.to, 5 for Hashnode)       │
│  2. Groq writes SEO meta description                         │
│  3. Groq writes Medium draft + Substack note                 │
│  4. POST to DEV.to API                                       │
│  5. POST to Hashnode GraphQL API (canonical → DEV.to)        │
│  6. Close issue with live links + copy-paste drafts          │
└──────────┬───────────────────────────┬───────────────────────┘
           │                           │
           ▼                           ▼
    ┌─────────────┐             ┌─────────────┐
    │   DEV.to    │             │  Hashnode   │
    │  (primary)  │             │  (mirror)   │
    └─────────────┘             └─────────────┘
```

After publish, the closed issue contains a ready-to-paste Medium draft and Substack note so you can cross-post manually in under 5 minutes.

---

## Topic areas

The scout agent rotates across 9 topic areas, avoiding repetition:

- AI for DevOps — agents, LLM-powered pipelines, auto-remediation
- MLOps and ML Infrastructure — model deployment, inference serving, feature stores
- Cost Optimisation — FinOps, spot instances, kubernetes right-sizing
- Security for DevOps — DevSecOps, supply chain, secrets management
- Observability and Monitoring — OpenTelemetry, SLOs, eBPF, distributed tracing
- GitOps and Platform Engineering — ArgoCD, Flux, internal developer platforms
- Production Troubleshooting and Runbooks — post-mortems, memory leaks, network latency
- SRE Practices — chaos engineering, toil reduction, capacity planning
- Terraform and IaC — Terraform at scale, drift detection, OpenTofu

---

## Why GitOps approval flow

The `/approve` comment pattern is a deliberate design choice, not just convenience:

- **Audit trail** — every article has a corresponding GitHub Issue showing when it was drafted and when it was approved
- **Zero infrastructure** — no Flask server, no database, no hosting cost. GitHub Actions is the compute
- **Human oversight** — the AI does the research and writing, you make the publishing decision
- **Secrets stay in GitHub** — API keys never touch your local machine at runtime

---

## Project structure

```
agentic-sentinel/
├── .github/
│   └── workflows/
│       └── gitops.yml       # pipeline definition
├── scout.py                 # AI research and issue creation agent
├── publish.py               # publishing and draft generation agent
├── .env.example             # environment variable template
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Areas of improvement

These are honest limitations with concrete paths to fix them:

**No LLM output validation** — the article is published as written. A second LLM call scoring technical accuracy and relevance before creating the issue would catch poor outputs.

**Single model, no fallback** — if Groq is unavailable the whole pipeline fails. Adding a fallback to a second provider (e.g. Together AI) would make it more resilient.

**GitHub Issue as the only state** — if an issue is accidentally closed before approval, the draft is lost. Storing the article body as a commit on a `drafts/` branch would make Git the source of truth.

**No image generation** — DEV.to and Hashnode articles with a cover image get significantly more clicks. Adding a DALL-E or Stable Diffusion call to generate a relevant cover would improve reach.

**Static cron schedule** — the agent runs twice a week regardless of whether the previous article was approved. Adding a check that skips the scout if there are open `pending-approval` issues would prevent a backlog.

---

## Screenshots

### Draft issue created by the agent
`[add screenshot here]`

### `/approve` comment triggering publish
`[add screenshot here]`

### Live article on DEV.to
`[add screenshot here — and link]`

---
portfolio piece that others can view but not reuse — leave it as is, or add a `LICENSE` file that says "All rights reserved".
