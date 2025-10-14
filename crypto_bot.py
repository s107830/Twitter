# crypto_bot.py

import os
import requests
import tweepy
import time

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
    return data  # e.g. { "bitcoin": {"usd": 30000, "usd_24h_change": 2.5}, ... }

def format_tweet(data):
    """Format a tweet string based on fetched crypto data."""
    lines = ["📈 Daily Crypto Update"]
    for coin, coin_info in data.items():
        price = coin_info.get("usd")
        change = coin_info.get("usd_24h_change")
        if price is None or change is None:
            continue
        # Format change with sign
        sign = "+" if change >= 0 else ""
        lines.append(f"{coin.capitalize()}: ${price:,.2f} ({sign}{change:.2f}%)")
    lines.append("#crypto #Bitcoin #Ethereum")
    tweet = "\n".join(lines)
    return tweet

def post_tweet(client, text):
    """Post a tweet using the Tweepy client."""
    try:
        resp = client.create_tweet(text=text)
        # resp.data contains tweet info (e.g. id)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)

def main():
    client = load_twitter_client()
    crypto = fetch_crypto_prices()
    tweet_text = format_tweet(crypto)
    print("Tweet content:\n", tweet_text)
    post_tweet(client, tweet_text)

if __name__ == "__main__":
    main()
