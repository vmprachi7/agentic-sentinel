import os
import random
import requests
from tavily import TavilyClient
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN     = os.getenv("GITHUB_TOKEN")
REPO             = os.getenv("GITHUB_REPOSITORY")
TAVILY_KEY       = os.getenv("TAVILY_API_KEY")
GROQ_KEY         = os.getenv("GROQ_API_KEY")
GITHUB_USERNAME  = os.getenv("GITHUB_ACTOR", (REPO or "/").split("/")[0])

# ─────────────────────────────────────────────
# TOPIC AREAS — 9 categories, each with 3-4 specific queries
# One category is picked per run (rotates so content stays diverse)
# ─────────────────────────────────────────────

TOPIC_AREAS = {
    "AI for DevOps": [
        "AI agents for infrastructure automation 2026",
        "LLM-powered CI/CD pipeline optimisation production",
        "AI for incident detection and auto-remediation DevOps",
        "MLOps platform engineering patterns 2026",
    ],
    "MLOps and ML Infrastructure": [
        "ML model deployment production issues 2026",
        "ML infra cost optimisation GPU cluster kubernetes",
        "feature store architecture production MLOps",
        "LLM inference serving latency optimisation 2026",
    ],
    "Cost Optimisation": [
        "cloud cost reduction strategies engineering team 2026",
        "kubernetes resource right-sizing FinOps production",
        "AWS GCP Azure cost anomaly detection automation",
        "spot instance reliability patterns production workloads",
    ],
    "Security for DevOps": [
        "DevSecOps pipeline shift-left security 2026",
        "supply chain attack prevention CI/CD 2026",
        "secrets management vault kubernetes production",
        "zero trust architecture platform engineering",
    ],
    "Observability and Monitoring": [
        "OpenTelemetry adoption production engineering 2026",
        "distributed tracing microservices performance",
        "SLO error budget alerting production patterns",
        "eBPF observability kubernetes 2026",
    ],
    "GitOps and Platform Engineering": [
        "GitOps ArgoCD Flux production patterns 2026",
        "internal developer platform IDP adoption 2026",
        "platform engineering golden path templates",
        "GitOps multi-cluster management production",
    ],
    "Production Troubleshooting and Runbooks": [
        "production outage post-mortem kubernetes 2026",
        "database connection pool exhaustion production fix",
        "memory leak detection microservices production",
        "network latency debugging distributed systems 2026",
    ],
    "SRE Practices": [
        "SRE on-call burnout reduction automation 2026",
        "chaos engineering production SRE patterns",
        "capacity planning SRE kubernetes 2026",
        "toil reduction SRE automation engineering",
    ],
    "Terraform and IaC": [
        "Terraform at scale production patterns 2026",
        "infrastructure drift detection IaC GitOps",
        "Terraform module design enterprise 2026",
        "OpenTofu adoption Terraform alternative 2026",
    ],
}


def get_past_topics():
    """Fetches last 15 issue titles to prevent repetition across all categories."""
    url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=15"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return [i["title"].replace("📝 DRAFT: ", "") for i in res.json()]
    except Exception as e:
        print(f"⚠️  Could not fetch history: {e}")
    return []


def pick_topic_area(past_topics):
    """
    Picks a topic area that hasn't been recently covered.
    Falls back to random if all areas have been covered.
    """
    past_lower = " ".join(past_topics).lower()
    # Simple keyword match per area to detect recent coverage
    area_keywords = {
        "AI for DevOps":                    ["ai", "llm", "agent", "mlops"],
        "MLOps and ML Infrastructure":      ["mlops", "ml infra", "feature store", "inference"],
        "Cost Optimisation":                ["cost", "finops", "spot", "rightsiz"],
        "Security for DevOps":              ["security", "devsecops", "vault", "secret"],
        "Observability and Monitoring":     ["observ", "tracing", "slo", "ebpf", "monitor"],
        "GitOps and Platform Engineering":  ["gitops", "argocd", "platform", "idp"],
        "Production Troubleshooting":       ["outage", "post-mortem", "troubleshoot", "runbook"],
        "SRE Practices":                    ["sre", "chaos", "capacity", "toil"],
        "Terraform and IaC":                ["terraform", "opentofu", "iac", "drift"],
    }
    uncovered = [
        area for area, keywords in area_keywords.items()
        if not any(kw in past_lower for kw in keywords)
    ]
    if uncovered:
        return random.choice(uncovered)
    return random.choice(list(TOPIC_AREAS.keys()))


def create_approval_issue(title, body):
    tagged_body = (
        f"Hey @{GITHUB_USERNAME}, a new technical deep-dive is ready for your review.\n\n"
        f"Comment `/approve` on this issue to publish it live to DEV.to and Hashnode.\n\n"
        f"---\n\n{body}"
    )
    url     = f"https://api.github.com/repos/{REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "title":  f"📝 DRAFT: {title}",
        "body":   tagged_body,
        "labels": ["pending-approval"],
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        return True
    print(f"❌ Failed to create issue {res.status_code}: {res.text}")
    return False


def run_scout():
    tavily = TavilyClient(api_key=TAVILY_KEY)
    llm    = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")

    # 1. Get dedup history
    past_topics = get_past_topics()
    avoid_list  = ", ".join(past_topics) if past_topics else "None"

    # 2. Pick a topic area not recently covered
    area = pick_topic_area(past_topics)
    queries = TOPIC_AREAS[area]
    print(f"🎯 Topic area: {area}")

    # 3. Run all queries for the chosen area, merge results
    all_results = []
    for query in queries:
        print(f"🔍 Searching: {query}")
        try:
            res = tavily.search(
                query=query,
                search_depth="advanced",
                time_range="week",      # only fresh content
                max_results=3
            )
            all_results.extend(res.get("results", []))
        except Exception as e:
            print(f"⚠️  Search failed for '{query}': {e}")

    if not all_results:
        print("❌ No search results returned. Exiting.")
        return

    # 4. Write the article
    article_prompt = (
        f"You are a senior DevOps engineer writing for an engineering audience on DEV.to.\n"
        f"Topic area: {area}\n"
        f"Based on these search results: {all_results}\n\n"
        f"STRICT RULE: Do not write about any of these already-covered topics: [{avoid_list}]\n\n"
        "Pick ONE specific, highly technical topic from the results that would genuinely help a "
        "working DevOps or SRE engineer. Write a 600-800 word deep-dive article in Markdown. "
        "Structure:\n"
        "1. The Problem — what breaks in production and why it matters\n"
        "2. Technical Breakdown — include at least one code block, config snippet, or architecture detail\n"
        "3. The Fix / Pattern — concrete steps, commands, or design decisions\n"
        "4. Key Takeaway — one sentence an engineer would remember and share\n\n"
        "Use precise technical language. No fluff. No 'In this article we will...'. "
        "Write as if explaining to a colleague in a post-mortem."
    )

    print("✍️  Writing article...")
    article = llm.invoke(article_prompt).content

    # 5. Generate a sharp title
    title_prompt = (
        f"Write a concise, punchy technical title for this DevOps article (max 8 words). "
        f"It should sound like a real engineering blog post, not a textbook chapter. "
        f"No colons. No quotes. Just the title.\n\nArticle preview: {article[:300]}"
    )
    title = llm.invoke(title_prompt).content.strip().replace('"', "").replace("'", "")

    # 6. Create the GitHub approval issue
    success = create_approval_issue(title=title, body=article)
    if success:
        print(f"✅ Issue created: '{title}' — area: {area} — tagged @{GITHUB_USERNAME}")
    else:
        print("❌ Issue creation failed.")


if __name__ == "__main__":
    run_scout()
