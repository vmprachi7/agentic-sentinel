import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
import tweepy
from langchain_groq import ChatGroq
from tavily import TavilyClient

# --- 1. CONFIGURATION ---


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

# Global variable to store the draft between steps
LATEST_DRAFT = "No draft available"

# --- 2. FUNCTIONS ---

def post_to_x(text):
    try:
        client = tweepy.Client(
            consumer_key=X_KEY, consumer_secret=X_SECRET,
            access_token=X_TOKEN, access_token_secret=X_TOKEN_SECRET
        )
        response = client.create_tweet(text=text[:280]) # X Limit
        return response.data['id']
    except Exception as e:
        print(f"❌ X Error: {e}")
        return None

def start_workflow():
    global LATEST_DRAFT
    print("🔍 Searching for trends...")
    results = tavily.search(query="Top 2026 DevOps and AI trends")
    
    print("✍️ Drafting...")
    prompt = f"Write one punchy tweet (max 200 chars) about: {results}"
    draft = llm.invoke(prompt)
    LATEST_DRAFT = draft.content

    # Send to Slack
    slack_client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text="New Draft Ready!",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Draft:* \n{LATEST_DRAFT}"}},
            {"type": "actions", "elements": [{"type": "button", "text": {"type": "plain_text", "text": "APPROVE"}, "style": "primary", "action_id": "approve"}]}
        ]
    )

# --- 3. THE HANDSHAKE ENDPOINT ---

@app.route("/slack/interactive", methods=["POST"])
def slack_interaction():
    global LATEST_DRAFT
    print("✅ Button clicked in Slack!")
    
    tweet_id = post_to_x(LATEST_DRAFT)
    
    if tweet_id:
        print(f"🚀 Live on X: https://x.com/i/status/{tweet_id}")
        return jsonify({"text": "✅ Successfully posted to X!"})
    else:
        return jsonify({"text": "❌ Failed to post. Check terminal logs."})

if __name__ == "__main__":
    # Start the AI research
    start_workflow()
    # Start the listener
    app.run(port=3000)