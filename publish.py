import os
import requests

DEV_TO_API_KEY = os.getenv("DEV_TO_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER")

raw_body = os.getenv("ISSUE_BODY", "")
ISSUE_TITLE = os.getenv("ISSUE_TITLE", "").replace("📝 DRAFT: ", "")

# Strip the intro header that scout.py prepends — everything before "---"
# Article content starts after the first "---" separator
ARTICLE_BODY = raw_body.split("---", 1)[-1].strip()


def publish_to_devto(title, body):
    url = "https://dev.to/api/articles"
    headers = {"api-key": DEV_TO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "tags": ["devops", "ai", "automation"]
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        return res.json().get("url")
    else:
        print(f"❌ DEV.to error {res.status_code}: {res.text}")
        return None


def close_github_issue(issue_number, devto_url):
    """Close the issue and leave a comment with the live link."""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Post a comment with the live link
    comment_url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
    requests.post(comment_url, headers=headers, json={
        "body": f"✅ Published! Article is live: {devto_url}"
    })

    # 2. Close the issue
    patch_url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    requests.patch(patch_url, headers=headers, json={
        "state": "closed",
        "state_reason": "completed"
    })

    print(f"🔒 Issue #{issue_number} closed.")


if __name__ == "__main__":
    print(f"📝 Publishing: {ISSUE_TITLE}")
    devto_url = publish_to_devto(ISSUE_TITLE, ARTICLE_BODY)

    if devto_url:
        print(f"🎉 Live at: {devto_url}")
        if ISSUE_NUMBER and GITHUB_TOKEN:
            close_github_issue(ISSUE_NUMBER, devto_url)
    else:
        print("❌ Publish failed — issue left open.")
