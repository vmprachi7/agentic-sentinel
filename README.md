# 🛡️ Agentic Content Sentinel
### *Autonomous Technical Intelligence & GitOps-Driven Publication Pipeline*

> An autonomous AI agent that scouts the web for production DevOps events, writes a technical article using a 70B LLM, and routes it through a GitOps-native approval workflow before deploying it live to DEV.to — all without a single always-on server.

---

## 📌 Live Proof of Work

| Artifact | Link |
|---|---|
| 🌐 DEV.to Published Articles | `[ADD YOUR DEV.TO PROFILE LINK]` |
| 🐙 GitHub Issues (Approval Trail) | `[ADD LINK TO YOUR REPO ISSUES]` |
| 🐦 X / Tweet Thread (why we mock) | See [Why Not X?](#-why-not-x-twitter) section below |

---

## 📸 System in Action

### Step 1 — AI Drafts a GitHub Approval Issue
> *The scout agent researches a topic and opens this for your review*

```
[INSERT SCREENSHOT: GitHub Issue with article draft + pending-approval label]
```

### Step 2 — Human Approves with `/approve`
> *One comment triggers the entire publish pipeline*

```
[INSERT SCREENSHOT: /approve comment on the issue]
```

### Step 3 — Article Goes Live on DEV.to
> *The finalized article, deployed automatically*

```
[INSERT SCREENSHOT: Live DEV.to article]
[INSERT LINK: https://dev.to/your-username/article-slug]
```

---

## 🧠 What Is "Agentic AI" — And Why Does It Matter Here?

Most AI integrations are **reactive**: a user asks, the LLM answers. This project implements **Agentic AI** — a system that acts autonomously toward a goal across multiple steps, with memory, decision-making, and tool use.

| Capability | Standard LLM App | This Project |
|---|---|---|
| **Runs on a schedule** | ❌ | ✅ Cron-triggered via GitHub Actions |
| **Uses external tools** | ❌ | ✅ Tavily web search + GitHub API |
| **Has memory** | ❌ | ✅ Queries past issues to avoid repetition |
| **Multi-step reasoning** | ❌ | ✅ Scout → Synthesize → Title → Publish |
| **Human oversight** | ❌ | ✅ Approval gate before any deployment |
| **Self-corrects output** | ❌ | ✅ Generates its own title + reformats Markdown |

### The Agent's Decision Loop

```
1. CHECK MEMORY     → "What have I already covered?" (GitHub Issues API)
2. SCOUT            → "What's newsworthy this week?" (Tavily time_range=week)
3. FILTER           → "Is this production-grade, or just hype?" (LLM prompt engineering)
4. SYNTHESIZE       → Write 600-word deep-dive with code blocks (Llama 3.3-70b)
5. SELF-TITLE       → Generate a punchy 6-word title (second LLM call)
6. REQUEST APPROVAL → Create GitHub Issue, tag reviewer via @mention
7. AWAIT SIGNAL     → Block on human `/approve` comment
8. DEPLOY           → Publish to DEV.to via REST API
```

This mirrors the **ReAct pattern** (Reason + Act) used in production agentic systems — the agent reasons about context before each action, rather than blindly chaining calls.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              TRIGGER LAYER (GitHub Actions)                      │
│    Cron: Mon & Thu 03:30 UTC  ──OR──  Manual workflow_dispatch  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SCOUT AGENT  (scout.py)                        │
│                                                                  │
│  ① GitHub Issues API → fetch last 10 titles (DEDUP MEMORY)     │
│  ② Tavily AI → deep search (time_range="week")                  │
│  ③ Llama 3.3-70b (Groq) → 600-word Markdown article            │
│  ④ Llama 3.3-70b (Groq) → sharp 6-word title                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ GitHub Issues API (POST)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              CONTROL PLANE  (GitHub Issue)                       │
│                                                                  │
│  • Full article in issue body                                    │
│  • Label: pending-approval                                       │
│  • @mention → email notification to reviewer                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ Human reviews, edits if needed
                         │ Types: /approve
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              HUMAN-IN-THE-LOOP GATE                              │
│              (GitHub issue_comment event trigger)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PUBLISH AGENT  (publish.py)                         │
│                                                                  │
│  • Reads ISSUE_BODY + ISSUE_TITLE from Actions context          │
│  • Strips internal draft prefix from title                       │
│  • POSTs to DEV.to API → published: true                        │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
             ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │  DEV.to Article │             │  X / Tweet      │
    │  (LIVE)         │             │  (Mock — see ↓) │
    └─────────────────┘             └─────────────────┘
```

**Key design principle:** No always-on server. GitHub Actions provides the compute. GitHub Issues provides the state. No database, no Redis, no EC2.

---

## ⚙️ GitOps Pipeline Deep-Dive

**File:** `.github/workflows/gitops.yml`

The workflow has two completely independent jobs:

### Job 1: `scout_and_draft`
**Trigger:** `schedule` (cron) or `workflow_dispatch`

Runs `scout.py`, which:
1. Fetches deduplication context from the GitHub Issues API
2. Performs a deep Tavily AI search scoped to the past week
3. Sends a structured prompt to Llama 3.3-70b to write a technical article
4. Creates a GitHub Issue with the `pending-approval` label and @mentions the repo owner

### Job 2: `approve_and_publish`
**Trigger:** `issue_comment` event where comment body contains `/approve`

Runs `publish.py`, which:
1. Receives `ISSUE_BODY` and `ISSUE_TITLE` via GitHub Actions environment injection
2. Cleans the title (strips draft prefix)
3. POSTs to DEV.to Articles API with `published: true`

**Why this is elegant:** The `if:` conditionals on each job mean they never conflict. The issue body acts as a zero-latency message bus between the two jobs — no external queue needed.

---

## 🤔 Why DEV.to Instead of X (Twitter)?

This is a deliberate architectural decision, not a limitation.

### The Core Problem with X for Technical Content

X has a **280-character limit** and an API ecosystem that has become increasingly hostile to developers since the 2023 restructuring:

- **Elevated API tiers** now cost $100–$5,000/month for meaningful write access
- **No code blocks** — technical articles posted as threads lose all structure
- **Algorithmic decay** — technical content underperforms against engagement-bait
- **Audience mismatch** — engineers seeking solutions are not the primary X demographic

### Why DEV.to Is the Right Target

| Criterion | X (Twitter) | DEV.to |
|---|---|---|
| **Character limit** | 280 | Unlimited Markdown |
| **Code blocks** | ❌ | ✅ Full syntax highlighting |
| **API access** | Paid ($100+/mo) | Free, stable REST API |
| **Audience** | General public | 1M+ developers |
| **SEO value** | Low | High (Google-indexed) |
| **Long-term reach** | Ephemeral | Evergreen |
| **DevOps community** | Scattered | Concentrated |

### The X Integration Still Exists

`main.py` contains a full X (Tweepy) integration with human-in-the-loop Slack approval. It runs in **mock mode** to avoid API cost during development. The architecture is ready to activate when a paid tier is available — it requires only swapping `post_to_x_mock()` for `post_to_x()` and setting the real credentials.

```
[INSERT SCREENSHOT: Slack approval message with "Approve & Publish" button]
[INSERT LINK: X post, if/when activated]
```

---

## 🛠️ Technology Stack

| Layer | Technology | Why Chosen |
|---|---|---|
| **LLM** | Llama 3.3-70b via Groq | Sub-second inference at 70B scale; free tier; beats GPT-3.5 on reasoning |
| **Web Search** | Tavily AI | Built for LLM retrieval; structured results; `time_range` filtering |
| **Orchestration** | GitHub Actions | Zero-infrastructure; native secret management; event-driven |
| **State / Control Plane** | GitHub Issues | Audit trail; email notifications; no external DB |
| **Publication Target** | DEV.to REST API | Stable; Markdown-native; developer audience |
| **Tweet Layer** | Tweepy (mock) | Full integration ready; awaiting API tier |
| **Slack Approval** | Slack SDK + Flask | Interactive buttons; human-in-the-loop for X path |
| **Local Dev** | python-dotenv | Parity between local and Actions environments |

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.9+
- API keys: Groq, Tavily, DEV.to
- A GitHub repo with a Personal Access Token (PAT)

### 1. Clone & Install

```bash
git clone https://github.com/vmprachi7/agentic-sentinel.git
cd agentic-sentinel
pip install requests tavily-python langchain-groq python-dotenv slack-sdk tweepy flask
```

### 2. Configure Environment

Create a `.env` file (never commit this):

```env
# AI Keys
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...

# Publishing
DEV_TO_API_KEY=your_devto_key

# GitHub (for dedup memory + issue creation)
GITHUB_TOKEN=ghp_...
GITHUB_REPOSITORY=vmprachi7/agentic-sentinel

# Optional: Slack (for X approval flow in main.py)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...

# Optional: X / Twitter (set real keys to go live)
X_CONSUMER_KEY=your_key
X_CONSUMER_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

### 3. Run the Scout Agent

```bash
# Trigger the full AI research + issue creation flow
python scout.py
```

The agent will:
1. Fetch past issue titles for deduplication
2. Search the web for this week's top DevOps events
3. Write a 600-word technical article
4. Open a GitHub Issue tagged `pending-approval` in your repo
5. Email you via GitHub's @mention notification

### 4. Approve and Publish

Go to your GitHub repo → Issues → find the new draft → comment `/approve`

GitHub Actions will automatically pick up the comment event and run `publish.py`.

### 5. (Optional) Run the Slack + X Flow

```bash
# In terminal 1: start ngrok
ngrok http 3000

# In terminal 2: start the Flask server + kick off the AI workflow
python main.py
```

Then update your Slack App's Interactive Components URL to the ngrok endpoint (`https://<your-id>.ngrok.io/slack/interactive`).

---

## 🔧 GitHub Repo Setup (One-Time)

### Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

```
GROQ_API_KEY
TAVILY_API_KEY
DEV_TO_API_KEY
GITHUB_TOKEN  (use ${{ secrets.GITHUB_TOKEN }} — auto-provided by Actions)
```

### Permissions
Go to **Settings → Actions → General → Workflow permissions** and select:
- ✅ **Read and write permissions**
- ✅ **Allow GitHub Actions to create and approve pull requests**

### Watch Notifications
Go to **Watch → Custom → Issues** on your repo to receive email alerts when the agent opens a new draft issue.

---

## 📁 Project Structure

```
agentic-sentinel/
├── .github/
│   └── workflows/
│       └── gitops.yml          # The entire pipeline (cron + approval)
├── scout.py                    # AI agent: research → draft → issue
├── publish.py                  # Deployment: issue body → DEV.to
├── main.py                     # Full Slack + X pipeline (mock mode)
├── test.py                     # Simplified Slack handshake prototype
├── .env.example                # Template — copy to .env, never commit .env
├── requirements.txt            # All dependencies
└── README.md                   # This file
```

---

## 🔭 Areas of Improvement (Honest Assessment)

These are real limitations with concrete solutions — this section exists to show engineering maturity, not to apologise.

### 1. LLM Output Validation
**Current state:** The article from Llama 3.3 is posted directly to the issue.
**Risk:** Hallucinated code, incorrect configurations, or off-topic content.
**Fix:** Add a second LLM call as a "critic" agent that scores the article on: technical accuracy (1-10), relevance to DevOps (1-10), presence of code blocks (bool). Only create the issue if all scores pass a threshold.

### 2. No Retry Logic on API Failures
**Current state:** If Tavily or Groq is down, the GitHub Action fails silently.
**Fix:** Wrap API calls in exponential backoff with a 3-attempt limit. On total failure, open a GitHub Issue with label `pipeline-error` so it's visible.

### 3. GitHub Issue as State Is Fragile
**Current state:** The article body lives in the issue. If the issue is accidentally closed or edited before approval, the content is lost.
**Fix:** Store the raw article body as a commit in a `drafts/` branch, and reference it in the issue. The issue becomes metadata; Git becomes the source of truth.

### 4. `GITHUB_USERNAME` Is Hardcoded
**Current state:** `scout.py` has `GITHUB_USERNAME = "YourGitHubUsername"`.
**Fix:** Derive it from the `GITHUB_ACTOR` environment variable injected by GitHub Actions, or read it from the `GITHUB_REPOSITORY` secret.

### 5. No Test Coverage
**Current state:** No unit tests exist.
**Fix:** Add `pytest` tests with mocked API responses for `create_approval_issue()`, `get_past_topics()`, and `publish()`. Mock `TavilyClient` and `ChatGroq` to test the prompt construction logic in isolation.

### 6. DEV.to Tags Are Static
**Current state:** Tags are hardcoded as `["devops", "ai", "automation"]`.
**Fix:** Have the LLM suggest 3 relevant tags as part of the article generation step, and inject them into the `publish.py` payload.

### 7. main.py Flask Server Requires ngrok
**Current state:** The Slack interactive endpoint needs a public URL via ngrok.
**Fix:** Deploy the Flask app to a free tier on Railway or Render, or replace it with a GitHub Actions `workflow_dispatch` webhook endpoint to eliminate the dependency entirely.

---

## 🧵 The Philosophy

This project is built on three convictions:

1. **Infrastructure should be code.** Every approval, every publication, every failure is a GitHub event with a full audit trail. No dashboard needed.

2. **AI should augment human judgment, not replace it.** The `/approve` gate is not a workaround — it's a feature. A senior engineer should always read the content before it goes live. The agent does the research; the human makes the call.

3. **Complexity earns its place.** The system uses six external APIs and a stateful GitOps workflow because each component solves a real problem. Nothing is added for aesthetic complexity.

---

## 📄 License

MIT — fork it, extend it, build on it.

---

*Built by [@vmprachi7](https://github.com/vmprachi7) · Powered by Groq × Tavily × GitHub Actions × DEV.to*
