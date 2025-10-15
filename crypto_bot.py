import os
import requests
import tweepy
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
    print("DEBUG: CoinGecko status:", resp.status_code)
    text = resp.text
    print("DEBUG: CoinGecko resp text (short):", text[:200])
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

def post_tweet(client, text):
    try:
        resp = client.create_tweet(text=text, user_auth=True)
        print("Tweet posted, response:", resp)
    except Exception as e:
        print("Error posting tweet:", e)
        traceback.print_exc()

def main():
    try:
        client = load_twitter_client()
        crypto = fetch_crypto_prices()
        tweet_text = format_tweet(crypto)
        print("Tweet content:\n", tweet_text)
        post_tweet(client, tweet_text)
    except Exception as e:
        print("Fatal error in main:", e)
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
