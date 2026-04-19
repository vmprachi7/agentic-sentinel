import os
import re
import requests

# --- CREDENTIALS ---
DEV_TO_API_KEY  = os.getenv("DEV_TO_API_KEY")
HASHNODE_TOKEN  = os.getenv("HASHNODE_TOKEN")
HASHNODE_PUB_ID = os.getenv("HASHNODE_PUBLICATION_ID")
GROQ_KEY        = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
REPO            = os.getenv("GITHUB_REPOSITORY")
ISSUE_NUMBER    = os.getenv("ISSUE_NUMBER")

raw_body     = os.getenv("ISSUE_BODY", "")
ISSUE_TITLE  = os.getenv("ISSUE_TITLE", "").replace("📝 DRAFT: ", "").strip()
ARTICLE_BODY = raw_body.split("---", 1)[-1].strip()

# DEV.to max = 4 tags, Hashnode max = 5
DEVTO_BASE_TAGS    = ["devops", "ai"]
HASHNODE_BASE_TAGS = ["devops", "ai", "automation"]

TAG_MENU = [
    "kubernetes", "terraform", "docker", "aws", "gcp", "azure",
    "cicd", "githubactions", "linux", "python", "security",
    "monitoring", "sre", "microservices", "cloudnative", "postgresql",
    "nginx", "ansible", "prometheus", "incident", "gitops",
    "automation", "devsecops", "openai", "llm", "mlops",
    "observability", "iac", "serverless", "platform"
]


# ─────────────────────────────────────────────
# STEP 1 — Generate metadata
# ─────────────────────────────────────────────

def generate_metadata(title, body):
    from langchain_groq import ChatGroq
    llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")

    prompt = f"""You are a DevOps content strategist.

ARTICLE TITLE: {title}
ARTICLE BODY (first 800 chars): {body[:800]}

Return EXACTLY this format, no extra text:

DEVTO_TAGS: <exactly 2 comma-separated lowercase tags from: {', '.join(TAG_MENU)}>

HASHNODE_TAGS: <exactly 2 comma-separated lowercase tags from the same list>

SEO_DESC: <one sentence, max 150 chars, specific and technical, written so an engineer searching Google would click it>

MEDIUM_DRAFT: <The article ready to paste into Medium. Start with a one-sentence hook paragraph. Then write: [ARTICLE BODY FOLLOWS]. Do not add any commentary, instructions, or meta-text — just the hook line then the article.>

SUBSTACK_DRAFT: <2-3 sentences for a Substack Note. Hook on the problem, hint at the solution, end with "Full article →" followed by [DEVTO_LINK]. Engineer-to-engineer tone. No corporate language.>"""

    raw = llm.invoke(prompt).content.strip()

    def extract(key):
        match = re.search(rf"{key}:(.*?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
        return match.group(1).strip() if match else ""

    devto_specific  = [t.strip() for t in extract("DEVTO_TAGS").split(",") if t.strip()][:2]
    devto_tags      = list(dict.fromkeys(DEVTO_BASE_TAGS + devto_specific))[:4]

    hn_specific     = [t.strip() for t in extract("HASHNODE_TAGS").split(",") if t.strip()][:2]
    hashnode_tags   = list(dict.fromkeys(HASHNODE_BASE_TAGS + hn_specific))[:5]

    seo_desc        = extract("SEO_DESC")[:150]

    # Replace [ARTICLE BODY FOLLOWS] placeholder with actual article
    medium_draft    = extract("MEDIUM_DRAFT").replace("[ARTICLE BODY FOLLOWS]", ARTICLE_BODY)

    substack_draft  = extract("SUBSTACK_DRAFT")

    return devto_tags, hashnode_tags, seo_desc, medium_draft, substack_draft


# ─────────────────────────────────────────────
# STEP 2 — Publish to DEV.to
# ─────────────────────────────────────────────

def publish_to_devto(title, body, tags, description):
    headers = {"api-key": DEV_TO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "description": description,
            "tags": tags,
            "series": "Agentic Sentinel",
        }
    }
    res = requests.post("https://dev.to/api/articles", headers=headers, json=payload)
    if res.status_code == 201:
        url = res.json().get("url")
        print(f"✅ DEV.to: {url}")
        return url
    print(f"❌ DEV.to error {res.status_code}: {res.text}")
    return None


# ─────────────────────────────────────────────
# STEP 3 — Publish to Hashnode
# ─────────────────────────────────────────────

def publish_to_hashnode(title, body, tags, description, canonical_url):
    if not HASHNODE_TOKEN or not HASHNODE_PUB_ID:
        print("⚠️  Hashnode credentials missing — skipping.")
        return None

    headers       = {"Authorization": HASHNODE_TOKEN, "Content-Type": "application/json"}
    hashnode_tags = [{"slug": t.lower(), "name": t.capitalize()} for t in tags]
    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) { post { url } }
    }"""
    variables = {
        "input": {
            "title": title,
            "contentMarkdown": body,
            "publicationId": HASHNODE_PUB_ID,
            "subtitle": description,
            "tags": hashnode_tags,
            "originalArticleURL": canonical_url,
        }
    }
    res = requests.post(
        "https://gql.hashnode.com/", headers=headers,
        json={"query": mutation, "variables": variables}
    )
    if res.status_code == 200 and "errors" not in res.json():
        url = res.json()["data"]["publishPost"]["post"]["url"]
        print(f"✅ Hashnode: {url}")
        return url
    print(f"❌ Hashnode: {res.json().get('errors', res.text)}")
    return None


# ─────────────────────────────────────────────
# STEP 4 — Close issue with clean drafts
# ─────────────────────────────────────────────

def close_github_issue(issue_number, devto_url, hashnode_url,
                        medium_draft, substack_draft, devto_tags, hashnode_tags):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    substack_ready = substack_draft.replace("[DEVTO_LINK]", devto_url or "")

    comment = f"""## ✅ Published

| Platform | URL |
|---|---|
| DEV.to | {devto_url or '—'} |
| Hashnode | {hashnode_url or '—'} |

**DEV.to tags:** `{'` · `'.join(devto_tags)}`
**Hashnode tags:** `{'` · `'.join(hashnode_tags)}`

---

## Medium draft

**Tags to add:** {', '.join(devto_tags)}

```
{medium_draft}
```

---

## Substack note

```
{substack_ready}
```
"""

    requests.post(
        f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments",
        headers=headers,
        json={"body": comment}
    )
    requests.patch(
        f"https://api.github.com/repos/{REPO}/issues/{issue_number}",
        headers=headers,
        json={"state": "closed", "state_reason": "completed"}
    )
    print(f"🔒 Issue #{issue_number} closed.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n📝 Publishing: {ISSUE_TITLE}\n")

    print("🧠 Generating metadata and drafts...")
    devto_tags, hashnode_tags, seo_desc, medium_draft, substack_draft = generate_metadata(
        ISSUE_TITLE, ARTICLE_BODY
    )
    print(f"   DEV.to tags:   {devto_tags}")
    print(f"   Hashnode tags: {hashnode_tags}")
    print(f"   SEO desc:      {seo_desc}\n")

    print("📡 Publishing to DEV.to...")
    devto_url = publish_to_devto(ISSUE_TITLE, ARTICLE_BODY, devto_tags, seo_desc)
    if not devto_url:
        print("❌ DEV.to failed. Aborting.")
        exit(1)

    print("📡 Publishing to Hashnode...")
    hashnode_url = publish_to_hashnode(
        ISSUE_TITLE, ARTICLE_BODY, hashnode_tags, seo_desc, devto_url
    )

    print("\n🔒 Closing issue...")
    if ISSUE_NUMBER and GITHUB_TOKEN:
        close_github_issue(
            ISSUE_NUMBER, devto_url, hashnode_url,
            medium_draft, substack_draft, devto_tags, hashnode_tags
        )

    print("\n🎉 Done.")
