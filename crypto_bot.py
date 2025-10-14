import os
import requests
import tweepy
from crypto_news_api import CryptoControlAPI
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
    return data

def format_tweet(data):
    """Format a tweet string based on fetched crypto data."""
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
    return tweet

def fetch_crypto_news(api_key, language="en"):
    """Fetch top crypto news using CryptoControl API."""
    api = CryptoControlAPI(api_key)
    api.enableSentiment()
    top_news = api.getTopNews(language=language)
    news_lines = ["📰 Top Crypto News"]
    for article in top_news:
        title = article.get("title")
        source = article.get("source", {}).get("name")
        url = article.get("url")
        if title and source and url:
            news_lines.append(f"{title} - {source}\n{url}")
    return "\n\n".join(news_lines)

def post_tweet(client, text):
    """Post a tweet using the Tweepy client."""
    try:
        resp = client.create_tweet(text=text)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)

def main():
    client = load_twitter_client()
    crypto_data = fetch_crypto_prices()
    tweet_text = format_tweet(crypto_data)
    print("Tweet content:\n", tweet_text)
    post_tweet(client, tweet_text)

    # Fetch and post crypto news
    api_key = os.getenv("CRYPTO_NEWS_API_KEY")
    if api_key:
        news_text = fetch_crypto_news(api_key)
        print("News content:\n", news_text)
        post_tweet(client, news_text)
    else:
        print("Crypto news API key is missing.")
    
if __name__ == "__main__":
    main()
