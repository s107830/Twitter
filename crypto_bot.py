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
def format_price_tweet(data):
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

# Fetch headlines from a single RSS feed URL
def fetch_headlines_from_rss(rss_url, limit=5):
    print(f"[INFO] Fetching headlines from {rss_url} ...")
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; CryptoBot/1.0)"
    feed = feedparser.parse(rss_url)

    print("[DEBUG] Feed status:", feed.get("status", "unknown"))
    print("[DEBUG] Feed bozo:", feed.bozo)
    if feed.bozo:
        print("[ERROR] Feed parsing error:", feed.bozo_exception)
    print("[DEBUG] Total entries found:", len(feed.entries))

    if not feed.entries:
        return []

    headlines = []
    for entry in feed.entries[:limit]:
        headlines.append(entry.title.strip())
    return headlines

# Fetch and combine headlines from multiple RSS feeds
def fetch_combined_crypto_news(rss_feeds, max_headlines=10):
    all_headlines = []
    seen = set()

    for rss_url in rss_feeds:
        headlines = fetch_headlines_from_rss(rss_url, limit=max_headlines)
        for h in headlines:
            if h not in seen:
                seen.add(h)
                all_headlines.append(h)
            if len(all_headlines) >= max_headlines:
                break
        if len(all_headlines) >= max_headlines:
            break

    if not all_headlines:
        return "No crypto news available."

    formatted_headlines = "\n".join(f"• {h}" for h in all_headlines)
    return formatted_headlines

# Post a tweet using the Twitter API client
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

def main():
    try:
        print("[INFO] Starting Crypto Twitter Bot")

        client = load_twitter_client()

        # Post Crypto Price Update
        crypto_data = fetch_crypto_prices()
        if crypto_data:
            price_tweet = format_price_tweet(crypto_data)
            post_tweet(client, price_tweet)
        else:
            print("[WARN] No crypto price data to tweet.")

        # RSS Feeds to fetch news from
        rss_feeds = [
            "https://feeds.feedburner.com/CoinDesk",  # CoinDesk
            "https://cointelegraph.com/rss",          # CoinTelegraph
            "https://cryptoslate.com/feed/"           # CryptoSlate
        ]

        # Fetch combined news headlines from all 3 sources
        headlines = fetch_combined_crypto_news(rss_feeds, max_headlines=10)
        print("[INFO] Combined Headlines:\n", headlines)

        news_tweet = f"📰 Top Crypto News:\n{headlines}\n#crypto #news"
        post_tweet(client, news_tweet)

        print("[INFO] Bot run completed.")

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
