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
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs_currency,
        "include_24hr_change": "true"
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data

# Format the tweet content for crypto prices
def format_tweet(data):
    lines = ["📈 Daily Crypto Update"]
    for coin, coin_info in data.items():
        price = coin_info.get("usd")
        change = coin_info.get("usd_24h_change")
        if price is None or change is None:
            continue
        sign = "+" if change >= 0 else ""
        lines.append(f"{coin.capitalize()}: ${price:,.2f} ({sign}{change:.2f}%)")
    lines.append("#crypto #Bitcoin #Ethereum")
    return "\n".join(lines)

# Fetch latest headlines from CoinDesk's RSS feed
def fetch_coindesk_headlines(limit=5):
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return "No CoinDesk news available."

    headlines = []
    for entry in feed.entries[:limit]:
        headlines.append(f"• {entry.title}")
    return "\n".join(headlines)

# Post a tweet using the Twitter API client
def post_tweet(client, text):
    try:
        resp = client.create_tweet(text=text)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)
        traceback.print_exc()

# Main function to fetch data and post tweets
def main():
    try:
        # Load Twitter client
        client = load_twitter_client()

        # --- Post Crypto Prices ---
        crypto_data = fetch_crypto_prices()
        tweet_text = format_tweet(crypto_data)
        print("Tweeting price update:\n", tweet_text)
        post_tweet(client, tweet_text)

        # --- Post CoinDesk Headlines ---
        headlines = fetch_coindesk_headlines(limit=5)
        news_tweet = f"📰 CoinDesk News:\n{headlines}\n#crypto #news"
        print("Tweeting news update:\n", news_tweet)
        post_tweet(client, news_tweet)

    except Exception as e:
        print("Fatal error in main:", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
