import os
import requests
import tweepy
import random
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

# Fetch the latest crypto news headlines using NewsData.io API
def fetch_crypto_news(api_key, query="crypto", language="en"):
    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": api_key,
        "q": query,
        "language": language,
        "category": "crypto"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching news: {response.status_code}")
        return None

# Extract and format the top 5 headlines from the news data
def extract_headlines(news_data):
    if news_data and "results" in news_data:
        headlines = [article["title"] for article in news_data["results"]]
        return "\n".join(headlines[:5])  # Limit to top 5 headlines
    return "No news available."

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
        client = load_twitter_client()
        crypto_data = fetch_crypto_prices()
        tweet_text = format_tweet(crypto_data)
        print("Tweet content:\n", tweet_text)
        post_tweet(client, tweet_text)

        news_data = fetch_crypto_news("pub_19d1c9837f4e4a0c96da1e25d79e7a54")
        headlines = extract_headlines(news_data)
        print("Headlines:\n", headlines)
        post_tweet(client, f"📰 Crypto News:\n{headlines}")

    except Exception as e:
        print("Fatal error in main:", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
