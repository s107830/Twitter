import os
import requests
import tweepy
import feedparser

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

def fetch_crypto_prices(ids=("bitcoin", "ethereum"), vs_currency="usd"):
    """Fetch current price and 24h change from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs_currency,
        "include_24hr_change": "true"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data

def fetch_news():
    """Fetch latest news headlines from CoinDesk."""
    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    feed = feedparser.parse(url)
    headlines = []
    for entry in feed.entries[:3]:  # Fetch top 3 news items
        headlines.append(f"📰 {entry.title} ({entry.link})")
    return "\n".join(headlines)

def format_tweet(crypto_data, news):
    """Format the tweet content."""
    lines = ["📈 Daily Crypto Update"]
    for coin, coin_info in crypto_data.items():
        price = coin_info.get("usd")
        change = coin_info.get("usd_24h_change")
        if price is None or change is None:
            continue
        sign = "+" if change >= 0 else ""
        lines.append(f"{coin.capitalize()}: ${price:,.2f} ({sign}{change:.2f}%)")
    lines.append("\nLatest News:\n" + news)
    lines.append("\n#crypto #Bitcoin #Ethereum")
    tweet = "\n".join(lines)
    return tweet

def post_tweet(client, text):
    """Post the tweet using the Tweepy client."""
    try:
        resp = client.create_tweet(text=text)
        print("Tweet posted successfully:", resp)
    except Exception as e:
        print("Error posting tweet:", e)

def main():
    client = load_twitter_client()
    crypto_data = fetch_crypto_prices()
    news = fetch_news()
    tweet_text = format_tweet(crypto_data, news)
    print("Tweet content:\n", tweet_text)
    post_tweet(client, tweet_text)

if __name__ == "__main__":
    main()
