import os
import requests

DEV_TO_KEY = os.getenv("DEV_TO_API_KEY")
# GitHub provides these via the 'issue_comment' event
ISSUE_BODY = os.getenv("ISSUE_BODY")
ISSUE_TITLE = os.getenv("ISSUE_TITLE").replace("📝 DRAFT: ", "")

def publish():
    url = "https://dev.to/api/articles"
    headers = {"api-key": DEV_TO_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": ISSUE_TITLE,
            "body_markdown": ISSUE_BODY,
            "published": True,
            "tags": ["devops", "automation"]
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        print(f"Article live: {res.json().get('url')}")

if __name__ == "__main__":
    publish()