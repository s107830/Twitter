import os
import re
import random
import tweepy
import feedparser
import traceback

# ---------- Clean HTML ----------
def clean_html(raw_html):
    if not raw_html:
        return ""
    raw_html = re.sub(r'<img[^>]+>', '', raw_html)
    raw_html = re.sub(r'<a[^>]+>(.*?)</a>', r'\1', raw_html)
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

# ---------- Twitter Client ----------
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

    return tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

# ---------- Fetch news with filter ----------
def fetch_relevant_news(rss_url, crypto_keywords, market_keywords):
    print(f"[INFO] Checking feed: {rss_url}")
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        print(f"[WARN] Parse issue with {rss_url}: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        return None, None

    # Check up to 5 latest entries
    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "").strip()
        summary_fields = [
            getattr(entry, "summary", ""),
            getattr(entry, "description", ""),
            getattr(entry, "content", [{}])[0].get("value", "") if hasattr(entry, "content") else ""
        ]
        summary = next((clean_html(s) for s in summary_fields if s), "")

        text = f"{title} {summary}".lower()

        # Match either crypto or market/trump related terms
        if any(k in text for k in crypto_keywords + market_keywords):
            print(f"[MATCH] Relevant news: {title}")
            return title, summary

    return None, None

# ---------- Create tweet ----------
def create_tweet_text(title, summary, hashtags="#crypto #markets #news", max_length=260):
    if not title:
        return "No relevant crypto or market news right now. #crypto #news"

    title = title.strip()
    summary = summary.strip() if summary else ""
    base = f"📰 {title}"

    if summary:
        text = f"{base}\n\n{summary}\n\n{hashtags}"
    else:
        text = f"{base}\n\n{hashtags}"

    # Truncate total length to 260 characters
    if len(text) > max_length:
        reserve = len(f"\n\n{hashtags}")
        allowed = max_length - reserve - len("📰 ") - 3
        combined = f"{title}. {summary}" if summary else title
        trimmed = combined[:allowed].rstrip() + "..."
        text = f"📰 {trimmed}\n\n{hashtags}"

    return text

# ---------- Post tweet ----------
def post_tweet(client, text):
    try:
        print(f"[INFO] Tweet length: {len(text)}")
        print("[INFO] Tweet content:\n", text)
        resp = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted:", resp)
    except Exception as e:
        print("[ERROR] Failed to post tweet:", e)
        traceback.print_exc()

# ---------- Main ----------
def main():
    try:
        print("[INFO] Bot started")

        client = load_twitter_client()

        rss_feeds = [
            "https://feeds.feedburner.com/CoinDesk",
            "https://cointelegraph.com/rss",
            "https://cryptoslate.com/feed/",
            "https://bitcoinmagazine.com/feed/",
            "https://cryptonews.com/news/feed/",
            "https://www.ccn.com/news/crypto-news/feeds/",
            "https://blockchain.news/feed",
            "https://ambcrypto.com/feed/",
            "https://u.today/rss",
            "https://coingape.com/feed/",
            "https://cryptopotato.com/feed/",
            "https://newsbtc.com/feed/",
            "https://zycrypto.com/feed/"
        ]

        # 🎯 Keyword lists
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
        title, summary = None, None

        for url in rss_feeds:
            t, s = fetch_relevant_news(url, crypto_keywords, market_keywords)
            if t:
                title, summary = t, s
                break

        tweet = create_tweet_text(title, summary)
        post_tweet(client, tweet)

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
