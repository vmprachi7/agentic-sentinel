import os
import requests
from tavily import TavilyClient
from langchain_groq import ChatGroq

# Config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY") # Automatically provided by GitHub Actions
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

def create_github_issue(title, body):
    url = f"https://api.github.com/repos/{REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # We add a special label 'pending-approval' so our second action can find it
    payload = {"title": f"📝 DRAFT: {title}", "body": body, "labels": ["pending-approval"]}
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code == 201

def run_scout():
    tavily = TavilyClient(api_key=TAVILY_KEY)
    llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")
    
    results = tavily.search(query="Top DevOps trends April 2026")
    article = llm.invoke(f"Write a 500-word technical post about: {results}").content
    
    # We put the article in the issue body
    success = create_github_issue(title="Weekly DevOps Trend", body=article)
    print(f"Issue created: {success}")

if __name__ == "__main__":
    run_scout()