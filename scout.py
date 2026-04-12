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

def create_approval_issue(title, body):
    url = f"https://api.github.com/repos/{REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"title": f"📝 DRAFT: {title}", "body": body, "labels": ["pending-approval"]}
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code == 201

def run_scout():
    tavily = TavilyClient(api_key=TAVILY_KEY)
    llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")
    
    # Focused Query: Looking for "The Big Story" of the week
    search_query = (
        "Major cloud production outage post-mortem 2026, "
        "new critical Kubernetes security fix, "
        "advanced Terraform configuration pattern for scale, "
        "common production issues in microservices April 2026"
    )
    
    print("🔍 Scouting for a single high-impact technical topic...")
    results = tavily.search(query=search_query, search_depth="advanced")
    
    # Prompting the LLM to pick ONE topic and go deep
    prompt = (
        f"Based on these results: {results}, identify ONE specific, highly technical topic. "
        "It should be either a real-world production issue, a new critical cloud setup, or a major release update. "
        "Write a 600-word deep-dive article. Structure it as follows: \n"
        "1. The Problem/Context\n"
        "2. Technical Breakdown (Config/Architecture)\n"
        "3. The DevOps Solution/Workaround\n"
        "4. Key Lesson for Engineers.\n"
        "Use Markdown with code blocks where applicable."
    )
    
    article = llm.invoke(prompt).content
    
    # Extracting a sharp title from the content
    title_prompt = f"Create a short, punchy technical title for this article: {article[:200]}"
    title = llm.invoke(title_prompt).content.strip().replace('"', '')

    success = create_approval_issue(title=title, body=article)
    if success:
        print(f"✅ Issue created: {title}")

if __name__ == "__main__":
    run_scout()
