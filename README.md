# 🛡️ Agentic Content Sentinel
### *Autonomous Technical Intelligence & GitOps-Driven Publication Pipeline*

The **Agentic Content Sentinel** is a high-performance "Content-as-Code" pipeline. It uses Agentic AI to scout the cloud ecosystem for critical production failures, security patches, and architectural shifts, delivering a curated technical "Deep-Dive" via a structured GitOps approval workflow.

---

## 🏗️ Architecture & System Design

The system is built on a **Decoupled, Event-Driven Architecture**. Instead of a brittle, always-on server, it leverages GitHub’s native infrastructure to handle state, security, and execution triggers.

1.  **Ingestion (Tavily AI):** Scans the web for high-signal technical events (RCAs, K8s patches, Terraform patterns).
2.  **Synthesis (Llama 3.3 via Groq):** An LLM agent analyzes the raw data, cross-references it with **History State** to prevent repetition, and drafts a technical post-mortem.
3.  **Governance (GitHub Issues):** The draft is pushed to a GitHub Issue. This acts as our **Control Plane**.
4.  **Human-in-the-Loop (Approval):** A `/approve` comment triggers a second-stage workflow.
5.  **Deployment (DEV.to API):** The finalized artifact is deployed to the production community.

---

## 🧠 The "Agentic AI" Advantage
Unlike standard automation scripts, this system utilizes **Agentic AI** principles to ensure content quality and relevance:
* **Self-Correction:** The agent generates its own titles and verifies Markdown formatting before submission.
* **Stateful Memory:** By querying the GitHub API for past issues, the agent maintains a "Memory" of published content to ensure 100% entropy and zero redundancy.
* **Contextual Filtering:** It prioritizes "Production Issues" and "Config Shifts," mimicking the logic of a Senior SRE.

---

## 🛠️ Strategic Tech Stack
* **Brain:** Llama 3.3-70b (Model-as-a-Service via Groq)
* **Search Engine:** Tavily AI (Optimized for LLM retrieval)
* **Orchestration:** GitHub Actions (Cron-based & Event-based)
* **Protocol:** GitOps (Issue-based approvals)
* **Target:** DEV.to (Professional technical community)

---

## ⚖️ Architectural Decisions (ADRs)

### Why DEV.to instead of X (Twitter)?
* **Technical Depth:** DevOps topics require code blocks, architectural diagrams, and long-form nuance that social platforms cannot provide.
* **API Reliability:** DEV.to provides a stable, developer-first REST API that aligns with open-source values.
* **Audience Targeting:** Ensures the content reaches engineers looking for solutions, not generic social media engagement.

### Why the GitOps Approval Flow?
* **Audit Trail:** Every post has a corresponding GitHub Issue showing exactly when it was drafted and who approved it.
* **Zero-Infrastructure:** No need to host a Flask/Django server. GitHub Actions provides the compute for free.
* **Security:** Secrets are stored in GitHub Key Vault, never touching the local environment or third-party middleware.

---

## 📸 Proof of Execution (System in Action)

### 1. The Automated Approval Ticket
*The agent scouts a topic and opens an issue for review.*
> **[INSERT SCREENSHOT OF GITHUB ISSUE HERE]**

### 2. The Approval Comment
*Triggering the deployment via a simple chat command.*
> **[INSERT SCREENSHOT OF /APPROVE COMMENT HERE]**

### 3. The Live Production Post
*The final artifact deployed to the community.*
> **[INSERT SCREENSHOT OF DEV.TO POST HERE]**

---

## 🚀 Local Development & Setup

### Prerequisites
* Python 3.9+
* API Keys: Groq, Tavily, DEV.to

### 1. Installation
```bash
git clone [https://github.com/your-username/agentic-sentinel.git](https://github.com/your-username/agentic-sentinel.git)
cd agentic-sentinel
pip install requests tavily-python langchain-groq python-dotenv
```

### 2. Environment Configuration

Create a .env file for local testing:

```text
Plaintext
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
DEV_TO_API_KEY=your_key
GITHUB_TOKEN=your_pat_token
GITHUB_REPOSITORY=user/repo
GITHUB_USERNAME=your_handle
```

3. Run Locally

```bash
# To trigger the scouting and issue creation
python scout.py
```

### 🔧 Automated Setup (GitHub)
Secrets: Add all API keys to Settings > Secrets and variables > Actions.

Permissions: Go to Settings > Actions > General and set Workflow Permissions to "Read and Write".

Watch: Click "Watch" on your repo to receive the bi-weekly approval emails.


Live Project Link: [Link to your DEV.to Profile or Repo]
