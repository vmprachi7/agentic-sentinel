<<<<<<< HEAD
# agentic-content-sentinel
=======
# Agentic Content Sentinel 🤖📝

An autonomous, "Human-in-the-Loop" technical content pipeline. This agent researches trending DevOps and Cloud Computing topics, drafts high-quality technical articles, and waits for manual approval via GitHub Issues before publishing to DEV.to.

## 🚀 How It Works (The Handshake)
1. **Scout Phase:** Twice a week, a GitHub Action wakes up and uses **Tavily AI** to research real-time DevOps trends.
2. **Draft Phase:** **Llama 3.3 (via Groq)** processes the research and synthesizes a professional Markdown article.
3. **Governance Phase:** The agent opens a **GitHub Issue** containing the draft. 
4. **Approval Phase:** The user reviews the draft on their phone/web. By commenting `/approve`, the user triggers the final deployment.
5. **Publish Phase:** The article is instantly published to **DEV.to**, and a success notification is logged.

## 🛠️ Tool Stack
- **Orchestration:** GitHub Actions
- **AI Brain:** Llama 3.3-70b (Groq)
- **Real-time Research:** Tavily AI
- **Governance Layer:** GitHub Issues (GitOps)
- **Target Platform:** DEV.to API
- **Language:** Python 3.9+

## 📋 Prerequisites
- A **GitHub** account.
- A **Groq Cloud** API Key (Free tier).
- A **Tavily AI** API Key (Free tier).
- A **DEV.to** API Key (Settings > Extensions).

## 🔐 Setup & Installation

### 1. Configure GitHub Secrets
Go to your Repository **Settings > Secrets and variables > Actions** and add:
- `GROQ_API_KEY`: Your Groq key.
- `TAVILY_API_KEY`: Your Tavily key.
- `DEV_TO_API_KEY`: Your DEV.to API key.
- `GITHUB_TOKEN`: (Provided automatically by GitHub, no need to add manually).

### 2. Local Development (Optional)
To test the scouting logic locally:
```bash
# Clone the repo
git clone [https://github.com/your-username/agentic-sentinel.git](https://github.com/your-username/agentic-sentinel.git)
cd agentic-sentinel

# Install dependencies
pip install requests tavily-python langchain-groq python-dotenv

# Run scout
python scout.py
>>>>>>> 4342a8c (initial commit)
