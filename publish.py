import os
import re
import base64
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

MEDIUM_HOOK: <one punchy opening sentence for Medium — makes an engineer stop scrolling. Max 200 chars. No "In this article". Just the hook.>

SUBSTACK_NOTE: <2 sentences max. Sentence 1: the problem hook. Sentence 2: "Full article →" followed by [DEVTO_LINK]. Engineer tone. Total must be under 300 chars.>"""

    raw = llm.invoke(prompt).content.strip()

    def extract(key):
        match = re.search(rf"{key}:(.*?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
        return match.group(1).strip() if match else ""

    devto_specific = [t.strip() for t in extract("DEVTO_TAGS").split(",") if t.strip()][:2]
    devto_tags     = list(dict.fromkeys(DEVTO_BASE_TAGS + devto_specific))[:4]

    hn_specific    = [t.strip() for t in extract("HASHNODE_TAGS").split(",") if t.strip()][:2]
    hashnode_tags  = list(dict.fromkeys(HASHNODE_BASE_TAGS + hn_specific))[:5]

    seo_desc       = extract("SEO_DESC")[:150]
    medium_hook    = extract("MEDIUM_HOOK")[:200]
    substack_note  = extract("SUBSTACK_NOTE")[:300]

    return devto_tags, hashnode_tags, seo_desc, medium_hook, substack_note


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
# STEP 4 — Save Medium draft as a file in the repo
# ─────────────────────────────────────────────

def save_medium_draft_to_repo(title, medium_hook, body, tags):
    """
    Saves the full Medium-ready article as a .md file inside drafts/medium/
    in the repo. This avoids GitHub Issue comment character limits entirely.
    The issue comment will link directly to this file.

    File is committed directly via the GitHub Contents API — no checkout needed.
    """
    if not GITHUB_TOKEN or not REPO:
        print("⚠️  Cannot save Medium draft — missing GITHUB_TOKEN or REPO.")
        return None

    # Build the full Medium article:
    # hook paragraph + separator + original article body
    medium_content = f"{medium_hook}\n\n---\n\n{body}"

    # Slugify the title for the filename
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    filename = f"drafts/medium/{slug}.md"

    # Add a small header so it's clear what the file is for
    file_body = (
        f"# {title}\n\n"
        f"> Medium draft — tags to add: {', '.join(tags)}\n\n"
        f"{medium_content}"
    )

    encoded = base64.b64encode(file_body.encode("utf-8")).decode("utf-8")

    url     = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Check if the file already exists (needed to provide sha for update)
    existing = requests.get(url, headers=headers)
    payload  = {
        "message": f"chore: add Medium draft for '{title}'",
        "content": encoded,
    }
    if existing.status_code == 200:
        payload["sha"] = existing.json()["sha"]

    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in (200, 201):
        file_url = f"https://github.com/{REPO}/blob/main/{filename}"
        print(f"✅ Medium draft saved: {file_url}")
        return file_url, filename
    print(f"❌ Could not save Medium draft: {res.status_code} {res.text}")
    return None, None


# ─────────────────────────────────────────────
# STEP 5 — Close issue with clean, short comment
# ─────────────────────────────────────────────

def close_github_issue(issue_number, devto_url, hashnode_url,
                        medium_file_url, medium_filename,
                        substack_note, devto_tags, hashnode_tags):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    substack_ready = substack_note.replace("[DEVTO_LINK]", devto_url or "")

    # Two options for Medium cross-posting explained cleanly
    medium_section = ""
    if medium_file_url:
        medium_section = (
            f"### Medium\n\n"
            f"**Option A — import from URL (recommended, 2 clicks):**\n"
            f"1. Go to [medium.com/p/import](https://medium.com/p/import)\n"
            f"2. Paste: `{devto_url}`\n"
            f"3. Medium imports the full article and sets the canonical URL automatically\n\n"
            f"**Option B — copy full draft from repo:**\n"
            f"[Open Medium draft ↗]({medium_file_url})\n"
            f"Tags to add: `{'` `'.join(devto_tags)}`\n"
        )
    else:
        medium_section = (
            f"### Medium\n\n"
            f"**Import from URL (2 clicks):**\n"
            f"1. Go to [medium.com/p/import](https://medium.com/p/import)\n"
            f"2. Paste: `{devto_url}`\n"
        )

    comment = f"""## ✅ Published

| Platform | URL |
|---|---|
| DEV.to | {devto_url or '—'} |
| Hashnode | {hashnode_url or '—'} |

**DEV.to tags:** `{'` · `'.join(devto_tags)}`
**Hashnode tags:** `{'` · `'.join(hashnode_tags)}`

---

{medium_section}

---

### Substack note

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

    print("🧠 Generating metadata...")
    devto_tags, hashnode_tags, seo_desc, medium_hook, substack_note = generate_metadata(
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

    print("💾 Saving Medium draft to repo...")
    medium_file_url, medium_filename = save_medium_draft_to_repo(
        ISSUE_TITLE, medium_hook, ARTICLE_BODY, devto_tags
    )

    print("\n🔒 Closing issue...")
    if ISSUE_NUMBER and GITHUB_TOKEN:
        close_github_issue(
            ISSUE_NUMBER, devto_url, hashnode_url,
            medium_file_url, medium_filename,
            substack_note, devto_tags, hashnode_tags
        )

    print("\n🎉 Done.")
