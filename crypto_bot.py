import os
import requests
import tweepy
import time
from datetime import datetime

# Define the selected news source
NEWS_SOURCE = "Cointelegraph"

def load_twitter_client():
    """Load Twitter client using credentials from environment variables."""
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise RuntimeError("One or more Twitter credentials are missing in environment variables")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return client

def fetch_latest_news(source):
    """Fetch the latest crypto news headline from the selected source."""
    if source == "Cointelegraph":
        url = "https://cointelegraph.com/api/v1/articles"
    else:
        raise ValueError("Unsupported news source")

    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    latest_article = data[0]  # Assuming the latest article is the first in the list
    headline = latest_article["title"]
    return headline

def format_tweet(news):
    """Format a tweet string based on the latest news."""
    lines = [f"📰 Top Crypto News Today: {news['headline']}", f"Source: {news['source']}", "\n#crypto #Bitcoin #Ethereum"]
    tweet = "\n".join(lines)
    return tweet

def post_tweet(client, text):
    """Post a tweet using the Tweepy client."""
    try:
        resp = client.create_tweet(text=text)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)

def main():
    client = load_twitter_client()
    latest_news = fetch_latest_news(NEWS_SOURCE)
    news = {"source": NEWS_SOURCE, "headline": latest_news}
    tweet_text = format_tweet(news)
    print("Tweet content:\n", tweet_text)
    post_tweet(client, tweet_text)

if __name__ == "__main__":
    main()
