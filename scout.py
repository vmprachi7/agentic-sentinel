import os
import requests
from tavily import TavilyClient
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
GITHUB_USERNAME = "YourGitHubUsername" # Replace with your actual GitHub handle

def create_approval_issue(title, body):
    # Adding @mention to the top of the body to trigger email notifications
    tagged_body = f"Hey @{GITHUB_USERNAME}, a new technical deep-dive is ready for review!\n\n---\n\n{body}"
    
    url = f"https://api.github.com/repos/{REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": f"📝 DRAFT: {title}", 
        "body": tagged_body, 
        "labels": ["pending-approval"]
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code == 201

def get_past_topics():
    """Fetches titles of the last 10 issues to prevent repetition."""
    url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=10"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            issues = response.json()
            return [issue['title'].replace("📝 DRAFT: ", "") for issue in issues]
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch history ({e})")
    return []

def run_scout():
    tavily = TavilyClient(api_key=TAVILY_KEY)
    llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")
    
    # 1. Deduplication: Check what we've already written
    past_topics = get_past_topics()
    avoid_list = ", ".join(past_topics) if past_topics else "None"
    
    # 2. Focused Scouting with Time Filtering
    search_query = (
        "Major cloud production outage post-mortem 2026, "
        "new critical Kubernetes security fix, "
        "advanced Terraform configuration pattern for scale, "
        "common production issues in microservices April 2026"
    )
    
    print(f"🔍 Scouting (Avoid List: {avoid_list[:50]}...)")
    # 'time_range="week"' is a natural deduplicator - ignores old news
    results = tavily.search(query=search_query, search_depth="advanced", time_range="week")
    
    # 3. History-Aware Deep Dive Prompt
    prompt = (
        f"Based on these results: {results}, identify ONE specific, highly technical topic. "
        f"STRICT RULE: Do not repeat or write about these previous topics: [{avoid_list}]. "
        "Write a 600-word deep-dive article. Structure it as follows: \n"
        "1. The Problem/Context\n"
        "2. Technical Breakdown (Config/Architecture)\n"
        "3. The DevOps Solution/Workaround\n"
        "4. Key Lesson for Engineers.\n"
        "Use Markdown with code blocks where applicable."
    )
    
    print("✍️ Generating fresh deep-dive...")
    article = llm.invoke(prompt).content
    
    # 4. Extracting a sharp title
    title_prompt = f"Create a short, punchy technical title for this article (Max 6 words): {article[:200]}"
    title = llm.invoke(title_prompt).content.strip().replace('"', '')

    # 5. Delivery
    success = create_approval_issue(title=title, body=article)
    if success:
        print(f"✅ Issue created: {title} (Tagged @{GITHUB_USERNAME})")

if __name__ == "__main__":
    run_scout()
