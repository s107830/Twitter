import os
import re
import random
import json
import requests
import tweepy
import feedparser
import traceback
from datetime import datetime

# ---------- SETTINGS ----------
USE_LONG_POST = True
LONG_POST_CHAR_LIMIT = 25000
STANDARD_CHAR_LIMIT = 280
LIQUIDATION_THRESHOLD = 100_000_000
MEMORY_FILE = "seen_news.json"

# ---------- Memory Handling ----------
def load_seen_news():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_news(seen_set):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(sorted(list(seen_set)), f, indent=2)
    except Exception as e:
        print("[WARN] Could not save seen_news.json:", e)

# ---------- Clean HTML ----------
def clean_html(raw_html):
    if not raw_html:
        return ""
    raw_html = re.sub(r'<img[^>]+>', '', raw_html)
    raw_html = re.sub(r'<a[^>]+>(.*?)</a>', r'\1', raw_html)
    text = re.sub(r'<[^>]+>', '', raw_html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ---------- Twitter Client ----------
def load_twitter_client():
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    return tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True
    )

# ---------- Hashtags ----------
def extract_hashtags_from_text(text, min_len=2):
    tags = set()
    for tag in re.findall(r"#([A-Za-z0-9_]+)", text):
        tags.add(tag)
    for w in re.findall(r"\b[A-Z]{2,}\b", text):
        tags.add(w)
    for phrase in re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text):
        tags.add(phrase.replace(" ", ""))
    return {tag for tag in tags if len(tag) >= min_len}

# ---------- Tweet Builder ----------
def create_tweet_text(title, summary):
    if not title:
        return None
    default_hashtags = ["crypto", "news"]
    found = extract_hashtags_from_text(title + " " + summary)
    all_tags = default_hashtags + list(found)
    seen = set()
    formatted = []
    for tag in all_tags:
        t = tag if tag.startswith("#") else "#" + tag
        if t.lower() not in seen:
            formatted.append(t)
            seen.add(t.lower())
    hashtag_text = " ".join(formatted)
    text = f"📰 {title}\n\n{summary}\n\n{hashtag_text}"
    limit = LONG_POST_CHAR_LIMIT if USE_LONG_POST else STANDARD_CHAR_LIMIT
    return text[:limit]

# ---------- Tweet Poster ----------
def post_tweet(client, text):
    try:
        if not text:
            print("[INFO] No text to post, skipping.")
            return
        print(f"[INFO] Tweet length = {len(text)}")
        response = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted:", response.data)
    except Exception as e:
        print("[ERROR] Failed to post tweet:", e)
        traceback.print_exc()

# ---------- RSS Reader ----------
def fetch_relevant_news(rss_url, crypto_keywords, market_keywords):
    print(f"[INFO] Checking feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    if feed.bozo or not feed.entries:
        return None, None

    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "").strip()
        summary_fields = [
            getattr(entry, "summary", ""),
            getattr(entry, "description", ""),
            (entry.content[0].get("value", "") if hasattr(entry, "content") else "")
        ]
        summary = next((clean_html(s) for s in summary_fields if s), "")
        text = (title + " " + summary).lower()
        if any(k in text for k in crypto_keywords + market_keywords):
            print(f"[MATCH] {title}")
            return title, summary
    return None, None

# ---------- Liquidation Alert ----------
def check_liquidations():
    try:
        url = "https://fapi.coinglass.com/api/futures/liquidation?timeType=1"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        total = data.get("data", {}).get("totalSumUsd", 0)
        if total and total > LIQUIDATION_THRESHOLD:
            msg = f"JUST IN: ${total:,.0f} liquidated from the cryptocurrency market in the past 60 minutes. #crypto #btc #liquidation"
            return msg
    except Exception:
        pass
    return None

# ---------- ETF Placeholder ----------
def check_etf_inflows():
    return None  # (future enhancement)

# ---------- MAIN ----------
def main():
    print("[INFO] Bot starting...")
    client = load_twitter_client()
    seen = load_seen_news()

    # 1️⃣ Liquidation
    alert = check_liquidations()
    if alert and alert not in seen:
        post_tweet(client, alert)
        seen.add(alert)
        save_seen_news(seen)
        return

    # 2️⃣ ETF
    etf_text = check_etf_inflows()
    if etf_text and etf_text not in seen:
        post_tweet(client, etf_text)
        seen.add(etf_text)
        save_seen_news(seen)
        return

    # 3️⃣ News
    rss_feeds = [
        "https://feeds.feedburner.com/CoinDesk",
        "https://cointelegraph.com/rss",
        "https://cryptoslate.com/feed/",
        "https://bitcoinmagazine.com/feed/",
        "https://cryptonews.com/news/feed/",
        "https://blockchain.news/feed",
        "https://ambcrypto.com/feed/",
        "https://u.today/rss",
        "https://coingape.com/feed/",
        "https://cryptopotato.com/feed/",
        "https://newsbtc.com/feed/",
        "https://zycrypto.com/feed/"
    ]
    crypto_keywords = [
        "crypto", "bitcoin", "ethereum", "altcoin", "btc", "eth",
        "blockchain", "web3", "defi", "nft"
    ]
    market_keywords = [
        "trump", "biden", "election", "market", "stocks", "nasdaq",
        "s&p", "dow jones", "price", "rally", "selloff", "economy",
        "inflation", "interest rate", "fed", "policy"
    ]

    random.shuffle(rss_feeds)
    for url in rss_feeds:
        title, summary = fetch_relevant_news(url, crypto_keywords, market_keywords)
        if title and title not in seen:
            tweet_text = create_tweet_text(title, summary)
            post_tweet(client, tweet_text)
            seen.add(title)
            save_seen_news(seen)
            return

    print("[INFO] No new posts today.")

if __name__ == "__main__":
    main()
