import os
import requests
import tweepy
import feedparser
import traceback

# Load Twitter API credentials from environment variables
def load_twitter_client():
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        missing = [name for name, val in [
            ("TWITTER_CONSUMER_KEY", consumer_key),
            ("TWITTER_CONSUMER_SECRET", consumer_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret)
        ] if not val]
        raise RuntimeError(f"Missing Twitter credentials: {missing}")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return client

# Fetch cryptocurrency prices from CoinGecko API
def fetch_crypto_prices(ids=("bitcoin", "ethereum"), vs_currency="usd"):
    print("[INFO] Fetching crypto prices from CoinGecko...")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs_currency,
        "include_24hr_change": "true"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print("[INFO] Crypto price data received:", data)
        return data
    except Exception as e:
        print("[ERROR] Failed to fetch crypto prices:", e)
        return {}

# Format tweet text for crypto price update
def format_tweet(data):
    print("[INFO] Formatting crypto price tweet...")
    lines = ["📈 Daily Crypto Update"]
    for coin, coin_info in data.items():
        price = coin_info.get("usd")
        change = coin_info.get("usd_24h_change")
        if price is None or change is None:
            continue
        sign = "+" if change >= 0 else ""
        lines.append(f"{coin.capitalize()}: ${price:,.2f} ({sign}{change:.2f}%)")
    lines.append("#crypto #Bitcoin #Ethereum")
    tweet = "\n".join(lines)
    print("[DEBUG] Formatted price tweet:\n", tweet)
    return tweet

# Fetch latest headlines from CoinDesk RSS
def fetch_coindesk_headlines(limit=5):
    print("[INFO] Fetching CoinDesk headlines...")
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("[WARN] No CoinDesk entries found.")
        return "No CoinDesk news available."

    headlines = []
    for entry in feed.entries[:limit]:
        print("[DEBUG] Headline:", entry.title)
        headlines.append(f"• {entry.title}")
    
    headline_text = "\n".join(headlines)
    print("[DEBUG] Formatted headlines:\n", headline_text)
    return headline_text

# Post a tweet
def post_tweet(client, text):
    try:
        if len(text) > 280:
            print("[WARN] Tweet too long, trimming...")
            text = text[:275] + "…"
        print("[INFO] Posting tweet...")
        resp = client.create_tweet(text=text)
        print("[INFO] Tweet posted:", resp)
    except Exception as e:
        print("[ERROR] Error posting tweet:", e)
        traceback.print_exc()

# Main logic
def main():
    try:
        print("[INFO] Starting Crypto Twitter Bot")
        
        client = load_twitter_client()

        # --- Price Update ---
        crypto_data = fetch_crypto_prices()
        if crypto_data:
            tweet_text = format_tweet(crypto_data)
            post_tweet(client, tweet_text)
        else:
            print("[ERROR] No crypto data available, skipping price tweet.")

        # --- CoinDesk News Update ---
        headlines = fetch_coindesk_headlines(limit=5)
        if headlines and "No CoinDesk" not in headlines:
            news_tweet = f"📰 CoinDesk News:\n{headlines}\n#crypto #news"
            post_tweet(client, news_tweet)
        else:
            print("[ERROR] No news headlines to post.")

        print("[INFO] Bot run completed.")

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
