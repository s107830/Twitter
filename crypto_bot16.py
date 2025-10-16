import os
import re
import random
import tweepy
import feedparser
import traceback

# ---------- SETTINGS ----------
USE_LONG_POST = True
LONG_POST_CHAR_LIMIT = 25000  # for X Premium Basic
STANDARD_CHAR_LIMIT = 280


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

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        missing = [name for name, val in [
            ("TWITTER_CONSUMER_KEY", consumer_key),
            ("TWITTER_CONSUMER_SECRET", consumer_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret)
        ] if not val]
        raise RuntimeError(f"Missing Twitter credentials: {missing}")

    return tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True
    )


# ---------- Hashtag Extraction ----------
def extract_hashtags_from_text(text, min_len=2):
    tags = set()

    for tag in re.findall(r"#([A-Za-z0-9_]+)", text):
        tags.add(tag)

    for w in re.findall(r"\b[A-Z]{2,}\b", text):
        tags.add(w)

    for phrase in re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text):
        tag = phrase.replace(" ", "")
        tags.add(tag)

    return {tag for tag in tags if len(tag) >= min_len}


# ---------- Fetch Relevant News ----------
def fetch_relevant_news(rss_url, crypto_keywords, market_keywords):
    print(f"[INFO] Checking feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        print(f"[WARN] Parse issue {rss_url}: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
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


# ---------- Create Tweet Text ----------
def create_tweet_text(title, summary, extra_hashtags=None):
    if not title:
        return "No relevant crypto or market news right now. #crypto #news"

    title = title.strip()
    summary = summary.strip() if summary else ""

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

    if summary:
        text = f"📰 {title}\n\n{summary}\n\n{hashtag_text}"
    else:
        text = f"📰 {title}\n\n{hashtag_text}"

    limit = LONG_POST_CHAR_LIMIT if USE_LONG_POST else STANDARD_CHAR_LIMIT

    if len(text) <= limit:
        return text

    # Truncate summary if too long
    reserve = len(f"📰 {title}\n\n{hashtag_text}") + 5
    allowed = limit - reserve
    if allowed <= 0:
        max_title = limit - len(f"📰 … {hashtag_text}") - 5
        trimmed = title[:max_title].rstrip() + "..."
        return f"📰 {trimmed}\n\n{hashtag_text}"
    else:
        trimmed = summary[:allowed].rstrip() + "..."
        return f"📰 {title}\n\n{trimmed}\n\n{hashtag_text}"


# ---------- Post Tweet ----------
def post_tweet(client, text):
    try:
        print(f"[INFO] Tweet length = {len(text)}")

        # ✅ FIXED: Use official API v2 "create_tweet" (supports long posts)
        response = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted:", response.data)

    except tweepy.TweepyException as e:
        print("[ERROR] Tweepy exception:", e)
        traceback.print_exc()
    except Exception as e:
        print("[ERROR] Failed to post:", e)
        traceback.print_exc()


# ---------- Main ----------
def main():
    try:
        print("[INFO] Bot starting")
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

        tweet_text = create_tweet_text(title, summary)
        print("[DEBUG] Final tweet text:\n", tweet_text)
        post_tweet(client, tweet_text)

    except Exception as e:
        print("[FATAL] Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
