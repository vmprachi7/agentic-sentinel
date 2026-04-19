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

raw_body    = os.getenv("ISSUE_BODY", "")
ISSUE_TITLE = os.getenv("ISSUE_TITLE", "").replace("📝 DRAFT: ", "").strip()
ARTICLE_BODY = raw_body.split("---", 1)[-1].strip()


# ─────────────────────────────────────────────
# STEP 1 — Rich metadata generation
# ─────────────────────────────────────────────

# DEV.to allows max 4 tags. We use all 4 slots strategically:
# - 1 broad tag (devops) for general discovery
# - 1 AI/automation tag always (since that's the brand)
# - 2 specific tags extracted from article content
#
# Hashnode allows up to 5 — we use all 5.
# Tags are the single biggest lever for organic reach on both platforms.
# A post tagged "kubernetes" appears in the kubernetes feed, search results,
# and weekly digest emails sent to followers of that tag.

DEVTO_BASE_TAGS    = ["devops", "ai"]          # always included, broad discovery
HASHNODE_BASE_TAGS = ["devops", "ai", "automation"]  # hashnode gets one extra slot

# Full tag menu the LLM picks from — all are active feeds on DEV.to and Hashnode
TAG_MENU = [
    "kubernetes", "terraform", "docker", "aws", "gcp", "azure",
    "cicd", "githubactions", "linux", "python", "security",
    "monitoring", "sre", "microservices", "cloudnative", "postgresql",
    "nginx", "ansible", "prometheus", "incident", "gitops",
    "automation", "devsecops", "openai", "llm", "mlops",
    "observability", "iac", "serverless", "platform"
]


def generate_metadata(title, body):
    """
    Single Groq call returns:
    - 2 specific DEV.to tags (fills the remaining 2 of 4 slots)
    - 2 specific Hashnode tags (fills the remaining 2 of 5 slots)
    - SEO meta description (150 chars) — appears in Google search snippets
    - Medium copy-paste ready article (with Medium-friendly header block)
    - Substack teaser (2-3 sentence hook for newsletter note)
    """
    from langchain_groq import ChatGroq
    llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")

    prompt = f"""You are a DevOps content strategist helping an engineer grow their audience.

ARTICLE TITLE: {title}
ARTICLE BODY (first 800 chars): {body[:800]}

Produce these 5 outputs. Return EXACTLY this format with no extra text:

DEVTO_TAGS: <exactly 2 comma-separated lowercase tags from this list that best match the article content: {', '.join(TAG_MENU)}>

HASHNODE_TAGS: <exactly 2 comma-separated lowercase tags from the same list — can overlap with DEVTO_TAGS if they're the best fit>

SEO_DESC: <one sentence, max 150 chars, specific and technical, written so an engineer searching Google would click it — no fluff, no "in this article">

MEDIUM_HEADER: <A 3-line Medium-style opening. Line 1: a bold one-sentence hook that makes an engineer stop scrolling. Line 2: one sentence on what specifically went wrong or what the challenge is. Line 3: one sentence on what this article delivers. Then write: ---END HEADER---  This goes BEFORE the article body on Medium.>

SUBSTACK_NOTE: <2-3 sentences for a Substack Note. Sentence 1: the problem hook. Sentence 2: what the article reveals. Sentence 3: "Full deep-dive is live —" followed by a placeholder [LINK]. Tone: direct, engineer-to-engineer, never corporate.>"""

    raw = llm.invoke(prompt).content.strip()

    def extract(key):
        match = re.search(rf"{key}:(.*?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
        return match.group(1).strip() if match else ""

    # Build DEV.to tags: 2 base + 2 specific = 4 total (DEV.to max)
    devto_specific  = [t.strip() for t in extract("DEVTO_TAGS").split(",") if t.strip()][:2]
    devto_tags      = list(dict.fromkeys(DEVTO_BASE_TAGS + devto_specific))[:4]

    # Build Hashnode tags: 3 base + 2 specific = 5 total
    hn_specific     = [t.strip() for t in extract("HASHNODE_TAGS").split(",") if t.strip()][:2]
    hashnode_tags   = list(dict.fromkeys(HASHNODE_BASE_TAGS + hn_specific))[:5]

    seo_desc        = extract("SEO_DESC")[:150]
    medium_header   = extract("MEDIUM_HEADER").replace("---END HEADER---", "").strip()
    substack_note   = extract("SUBSTACK_NOTE")

    return devto_tags, hashnode_tags, seo_desc, medium_header, substack_note


# ─────────────────────────────────────────────
# STEP 2 — Publish to DEV.to
# ─────────────────────────────────────────────

def publish_to_devto(title, body, tags, description):
    """
    Primary recruiter platform.
    - 'series' groups all articles → readers follow the whole series
    - 'description' shows in Google search snippets
    - All 4 tag slots used → appears in 4 separate tag feeds
    """
    headers = {"api-key": DEV_TO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "description": description,
            "tags": tags,                    # exactly 4 — all slots used
            "series": "Agentic Sentinel",    # builds a navigable series on your profile
        }
    }
    res = requests.post("https://dev.to/api/articles", headers=headers, json=payload)
    if res.status_code == 201:
        data = res.json()
        print(f"✅ DEV.to: {data.get('url')}")
        return data.get("url")
    print(f"❌ DEV.to error {res.status_code}: {res.text}")
    return None


# ─────────────────────────────────────────────
# STEP 3 — Publish to Hashnode
# ─────────────────────────────────────────────

def publish_to_hashnode(title, body, tags, description, canonical_url):
    """
    Mirrors article with canonical URL → DEV.to.
    Google credits DEV.to as original (good for recruiter SEO).
    Hashnode's own feed + newsletter sends it to their 500k+ developer community.
    5 tags used = 5 separate Hashnode tag feeds.
    """
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
# STEP 4 — Close issue with everything ready to paste
# ─────────────────────────────────────────────

def close_github_issue(issue_number, devto_url, hashnode_url,
                        medium_header, substack_note, devto_tags, hashnode_tags):
    """
    Closes the issue and posts a comment with:
    - All live links
    - Medium-ready article (header + full body) to copy-paste
    - Substack note to copy-paste
    - Explanation of how money works on each platform
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    medium_full = f"{medium_header}\n\n---\n\n{ARTICLE_BODY}"
    substack_with_link = substack_note.replace("[LINK]", devto_url or hashnode_url or "")

    comment = f"""## ✅ Published

| Platform | URL | Purpose |
|---|---|---|
| DEV.to | {devto_url or '—'} | Recruiter SEO · Google indexed |
| Hashnode | {hashnode_url or '—'} | Mirror · Hashnode community feed |

**DEV.to tags used:** `{'` `'.join(devto_tags)}`
**Hashnode tags used:** `{'` `'.join(hashnode_tags)}`

---

## 💰 Your copy-paste earning tasks (5 mins total)

### 1. Medium — paste this as a new story

> **How Medium pays you:** Medium Partner Program pays per reading-time from paying Medium members. You earn roughly $1–5 per 1,000 reads. A well-tagged post that gets picked up by Medium's algorithm earns $20–200 in the first week. Just paste the content below as a new story, add the same tags, and publish.

```
{medium_full}
```

**Tags to add on Medium:** {', '.join(devto_tags)}

---

### 2. Substack — paste this as a new Note

> **How Substack pays you:** Substack itself doesn't pay per read. You earn when readers subscribe to your paid tier ($5–10/month). Use free posts to build subscribers. At 200 paid subscribers = ~$1,000/month recurring. This Note drives people to your free article, growing your list.

```
{substack_with_link}
```

> Post this as a **Note** (not a full post) — Notes appear in the Substack feed and get shared by followers.

---
*Agentic Sentinel · fully automated by AI agent*"""

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
    print(f"🔒 Issue #{issue_number} closed with publish summary.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n📝 Publishing: {ISSUE_TITLE}\n")

    # 1. Generate all metadata + copy-paste content
    print("🧠 Generating tags, SEO description, Medium header, Substack note...")
    devto_tags, hashnode_tags, seo_desc, medium_header, substack_note = generate_metadata(
        ISSUE_TITLE, ARTICLE_BODY
    )
    print(f"   DEV.to tags:  {devto_tags}")
    print(f"   Hashnode tags: {hashnode_tags}")
    print(f"   SEO: {seo_desc}\n")

    # 2. Publish to DEV.to
    print("📡 Publishing to DEV.to...")
    devto_url = publish_to_devto(ISSUE_TITLE, ARTICLE_BODY, devto_tags, seo_desc)
    if not devto_url:
        print("❌ DEV.to failed. Aborting.")
        exit(1)

    # 3. Publish to Hashnode (canonical → DEV.to)
    print("📡 Publishing to Hashnode...")
    hashnode_url = publish_to_hashnode(
        ISSUE_TITLE, ARTICLE_BODY, hashnode_tags, seo_desc, devto_url
    )

    # 4. Close issue with links + Medium/Substack copy-paste content
    print("\n🔒 Closing issue with full publish summary...")
    if ISSUE_NUMBER and GITHUB_TOKEN:
        close_github_issue(
            ISSUE_NUMBER, devto_url, hashnode_url,
            medium_header, substack_note, devto_tags, hashnode_tags
        )

    print("\n🎉 Automated pipeline complete.")
    print("📋 Open the closed GitHub issue to copy-paste to Medium and Substack.")
