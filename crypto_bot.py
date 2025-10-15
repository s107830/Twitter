import os
import requests
import tweepy
import random
from bs4 import BeautifulSoup
import traceback

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

def fetch_headlines(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    headlines = [h.get_text(strip=True) for h in soup.find_all('h2')]
    return headlines[:5]  # Limit to top 5 headlines

def get_random_headline():
    urls = [
        'https://cointelegraph.com/',
        'https://www.coindesk.com/',
        'https://decrypt.co/',
        'https://beincrypto.com/',
        'https://u.today/'
    ]
    url = random.choice(urls)
    headlines = fetch_headlines(url)
    return random.choice(headlines) if headlines else None

def post_tweet(client, text):
    try:
        resp = client.create_tweet(text=text)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)
        traceback.print_exc()

def main():
    try:
        client = load_twitter_client()
        crypto_data = fetch_crypto_prices()
        tweet_text = format_tweet(crypto_data)
        print("Tweet content:\n", tweet_text)
        post_tweet(client, tweet_text)

        headline = get_random_headline()
        if headline:
            headline_tweet = f"📰 Crypto News: {headline} #CryptoNews"
            print("Headline tweet content:\n", headline_tweet)
            post_tweet(client, headline_tweet)
        else:
            print("No headlines found to post.")

    except Exception as e:
        print("Fatal error in main:", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
