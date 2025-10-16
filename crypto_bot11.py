import os
import re
import random
import tweepy
import feedparser
import traceback

# Optional: Set this flag if you have Premium Basic
USE_LONG_POST = True  
LONG_POST_CHAR_LIMIT = 25000  # Maximum characters for Premium Basic long posts
STANDARD_CHAR_LIMIT = 280     # Fallback limit if not long-post capable

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
    # same as yours
    print(f"[INFO] Checking feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        print(f"[WARN] Parse issue with {rss_url}: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        return None, None

    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "").strip()
        summary_fields = [
            getattr(entry, "summary", ""),
            getattr(entry, "description", ""),
            getattr(entry, "content", [{}])[0].get("value", "") if hasattr(entry, "content") else ""
        ]
        summary = next((clean_html(s) for s in summary_fields if s), "")

        text = f"{title} {summary}".lower()
        if any(k in text for k in crypto_keywords + market_keywords):
            print(f"[MATCH] Relevant news: {title}")
            return title, summary

    return None, None

# ---------- Create tweet text with more hashtags ----------
def create_tweet_text(title, summary, extra_hashtags=None):
    if not title:
        return "No relevant crypto or market news right now. #crypto #news"

    title = title.strip()
    summary = summary.strip() if summary else ""

    # Base hashtags
    hashtags = ["#crypto", "#markets", "#news"]

    # Add extra related tags automatically
    if extra_hashtags:
        hashtags += extra_hashtags

    # Remove duplicates
    hashtags = list(dict.fromkeys(hashtags))

    hashtag_text = " ".join(hashtags)

    if summary:
        text = f"📰 {title}\n\n{summary}\n\n{hashtag_text}"
    else:
        text = f"📰 {title}\n\n{hashtag_text}"

    # If using long posts and it's under that limit, return full
    if USE_LONG_POST and len(text) <= LONG_POST_CHAR_LIMIT:
        return text
    else:
        # Fallback / or we need to truncate
        limit = LONG_POST_CHAR_LIMIT if USE_LONG_POST else STANDARD_CHAR_LIMIT
        if len(text) <= limit:
            return text
        else:
            # Truncate summary part to fit
            # Reserve for title + hashtags + some buffer
            reserve = len(f"📰 {title}\n\n{hashtag_text}") + 5
            allowed_summary = limit - reserve
            if allowed_summary < 0:
                # Title + hashtags already too big => truncate title
                trimmed_title = title[:limit - len(f"📰 ... {hashtag_text}") - 5].rstrip() + "..."
                return f"📰 {trimmed_title}\n\n{hashtag_text}"
            else:
                trimmed_summary = summary[:allowed_summary].rstrip() + "..."
                return f"📰 {title}\n\n{trimmed_summary}\n\n{hashtag_text}"

# ---------- Post tweet or thread ----------
def post_tweet(client, text):
    try:
        print(f"[INFO] Tweet content length: {len(text)}")
        if USE_LONG_POST:
            # Try direct post (premium account)
            resp = client.create_tweet(text=text)
            print("[SUCCESS] Tweet posted (long post):", resp)
        else:
            # Fallback: if too long, split into thread
            if len(text) <= STANDARD_CHAR_LIMIT:
                resp = client.create_tweet(text=text)
                print("[SUCCESS] Tweet posted:", resp)
            else:
                print("[INFO] Splitting into thread because too long")
                parts = split_into_parts(text, STANDARD_CHAR_LIMIT)
                prev_id = None
                for part in parts:
                    if prev_id is None:
                        resp = client.create_tweet(text=part)
                    else:
                        resp = client.create_tweet(text=part, in_reply_to_tweet_id=prev_id)
                    prev_id = resp.data["id"]
                print("[SUCCESS] Thread posted.")
    except Exception as e:
        print("[ERROR] Failed to post:", e)
        traceback.print_exc()

def split_into_parts(text, limit):
    # Split by sentences or by words so threads read well
    words = text.split()
    parts = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= limit:
            current += (" " if current else "") + w
        else:
            parts.append(current)
            current = w
    if current:
        parts.append(current)
    return parts

# ---------- Main ----------
def main():
    try:
        print("[INFO] Bot started")

        client = load_twitter_client()

        rss_feeds = [
            # your feeds...
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

        # Extra hashtags you might want
        extra_tags = ["#Bitcoin", "#Ethereum", "#Altcoins", "#DeFi", "#Blockchain", "#CryptoNews"]

        random.shuffle(rss_feeds)
        title, summary = None, None

        for url in rss_feeds:
            t, s = fetch_relevant_news(url, crypto_keywords, market_keywords)
            if t:
                title, summary = t, s
                break

        tweet_text = create_tweet_text(title, summary, extra_hashtags=extra_tags)
        post_tweet(client, tweet_text)

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
