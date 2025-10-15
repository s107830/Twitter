import os
import requests
import tweepy
import time
import traceback

def load_twitter_client():
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    print("DEBUG: consumer_key set? ", bool(consumer_key))
    print("DEBUG: consumer_secret set? ", bool(consumer_secret))
    print("DEBUG: access_token set? ", bool(access_token))
    print("DEBUG: access_token_secret set? ", bool(access_token_secret))

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        missing = [name for name, val in [
            ("TWITTER_CONSUMER_KEY", consumer_key),
            ("TWITTER_CONSUMER_SECRET", consumer_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret),
        ] if not val]
        raise RuntimeError(f"Missing Twitter credentials: {missing}")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return client

def fetch_latest_news():
    url = "https://cointelegraph.com/api/v1/articles"
    try:
        resp = requests.get(url, timeout=10)
        print("DEBUG: news API status:", resp.status_code)
        text = resp.text
        print("DEBUG: news API response text (first 500 chars):", text[:500])
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("Error fetching news:", e)
        traceback.print_exc()
        raise

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError("Unexpected news data format: not a non-empty list")

    latest = data[0]
    headline = latest.get("title")
    if not headline:
        raise RuntimeError(f"No title found in news item: {latest}")
    return headline

def format_tweet(news):
    lines = [
        f"📰 Top Crypto News Today: {news['headline']}",
        f"Source: {news['source']}",
        "\n#crypto #Bitcoin #Ethereum"
    ]
    return "\n".join(lines)

def post_tweet(client, text):
    try:
        # try with user_auth = True
        resp = client.create_tweet(text=text, user_auth=True)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)
        traceback.print_exc()
        raise

def main():
    client = load_twitter_client()
    latest_news = fetch_latest_news()
    news = {"source": "Cointelegraph", "headline": latest_news}
    tweet_text = format_tweet(news)
    print("Tweet content:\n", tweet_text)
    post_tweet(client, tweet_text)

if __name__ == "__main__":
    main()
