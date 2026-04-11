import os
import json
import requests
import tweepy
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from langchain_groq import ChatGroq
from tavily import TavilyClient
from dotenv import load_dotenv

# Load variables from a .env file for security
load_dotenv()

# --- 1. CONFIGURATION ---
# Replace these strings with your actual keys or use a .env file

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID")
GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
DEV_TO_KEY = os.getenv("DEV_TO_API_KEY")

# X Keys (Keep these even for Mocking)
X_KEY = os.getenv("X_CONSUMER_KEY", "your_x_key")
X_SECRET = os.getenv("X_CONSUMER_SECRET", "your_x_secret")
X_TOKEN = os.getenv("X_ACCESS_TOKEN", "your_x_token")
X_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "your_x_token_secret")

# Initialize Clients
slack_client = WebClient(token=SLACK_TOKEN)
tavily = TavilyClient(api_key=TAVILY_KEY)
llm = ChatGroq(groq_api_key=GROQ_KEY, model_name="llama-3.3-70b-versatile")
app = Flask(__name__)

# --- 2. GLOBAL STATE ---
# Bridges the gap between AI generation and Slack approval
LATEST_TWEET = ""
LATEST_ARTICLE = ""
ARTICLE_TITLE = "The Future of DevOps 2026"

# --- 3. PUBLISHING LOGIC ---

def post_to_x_mock(text):
    """Simulates posting to X due to API tier restrictions."""
    print(f"🎬 [MOCK X] Publishing: {text[:50]}...")
    return "MOCK_TWEET_12345"

def post_to_devto(title, body_markdown):
    """Publishes a technical article live to DEV.to."""
    url = "https://dev.to/api/articles"
    headers = {"api-key": DEV_TO_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": True, # Change to False to save as Draft
            "tags": ["devops", "ai", "automation"]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            return response.json().get("url")
        else:
            print(f"❌ DEV.to Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

# --- 4. AGENT WORKFLOW ---

def run_agentic_workflow():
    global LATEST_TWEET, LATEST_ARTICLE
    
    print("🔍 Step 1: Scouting DevOps trends...")
    search_query = "latest devops trends and AI automation April 2026"
    search_results = tavily.search(query=search_query)

    print("✍️ Step 2: Generating multi-platform content...")
    
    # Generate Tweet
    tweet_prompt = f"Write a 200-character punchy tweet about: {search_results}"
    LATEST_TWEET = llm.invoke(tweet_prompt).content

    # Generate Full Article
    article_prompt = f"Write a professional Markdown technical article (800 words) about: {search_results}"
    LATEST_ARTICLE = llm.invoke(article_prompt).content

    # Step 3: Send to Slack for Approval
    print("📡 Step 3: Sending to Slack for Human-in-the-Loop approval...")
    
    # Truncate preview for Slack's 3000 char limit
    preview_text = LATEST_TWEET if len(LATEST_TWEET) < 2500 else LATEST_TWEET[:2500] + "..."

    slack_client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text="🚀 *New Content Pipeline Ready*",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Proposed Tweet:* \n{preview_text}\n\n*Full Article:* Drafted for DEV.to"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve & Publish"},
                        "style": "primary",
                        "action_id": "approve_all"
                    }
                ]
            }
        ]
    )

# --- 5. SLACK HANDSHAKE ENDPOINT ---

@app.route("/slack/interactive", methods=["POST"])
def slack_interaction():
    global LATEST_TWEET, LATEST_ARTICLE, ARTICLE_TITLE
    
    # Parse the Slack payload
    payload = json.loads(request.form.get("payload"))
    
    if payload["actions"][0]["action_id"] == "approve_all":
        print("✅ Received approval from Slack. Commencing publication...")
        
        # Post to Mock X
        post_to_x_mock(LATEST_TWEET)
        
        # Post to DEV.to
        dev_url = post_to_devto(ARTICLE_TITLE, LATEST_ARTICLE)
        
        if dev_url:
            return jsonify({"text": f"🎉 *Success!* Content is live: {dev_url}"})
        else:
            return jsonify({"text": "❌ Handshake worked, but DEV.to API failed."})

    return jsonify({"text": "Action acknowledged."})

if __name__ == "__main__":
    # 1. Trigger the Agent to start the loop
    run_agentic_workflow()
    
    # 2. Run the Flask server on Port 3000
    # Remember to keep 'ngrok http 3000' running in a separate tab!
    app.run(port=3000)