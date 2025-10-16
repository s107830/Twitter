import os
import re
import random
import tweepy
import feedparser
import traceback

# ---------- Clean HTML ----------
def clean_html(raw_html):
    raw_html = re.sub(r'<img[^>]+>', '', raw_html)
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
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

# ---------- Fetch latest headline ----------
def fetch_headline_and_summary(rss_url):
    print(f"[INFO] Fetching from: {rss_url}")
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        print(f"[WARN] Parse issue with {rss_url}: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        print(f"[WARN] No entries found in {rss_url}")
        return None, None

    entry = feed.entries[0]
    title = getattr(entry, "title", "").strip()
    raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    summary = clean_html(raw_summary)
    return title, summary

# ---------- Create tweet ----------
def create_tweet_text(title, summary, hashtags="#crypto #news", max_length=250):
    if summary:
        text = f"📰 {title}\n\n{summary}\n\n{hashtags}"
    else:
        text = f"📰 {title}\n\n{hashtags}"

    if len(text) <= max_length:
        return text

    # If too long, truncate summary or title
    reserved = len(f"📰 {title}\n\n\n\n{hashtags}")
    allowed_summary = max_length - reserved - 3
    if summary and allowed_summary > 0:
        summary = summary[:allowed_summary].rstrip() + "..."
        return f"📰 {title}\n\n{summary}\n\n{hashtags}"

    allowed_title = max_length - len(f"📰 \n\n{hashtags}") - 3
    title = title[:allowed_title].rstrip() + "..."
    return f"📰 {title}\n\n{hashtags}"

# ---------- Post to Twitter ----------
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

        # ✅ Updated RSS feed list
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

        # Randomize order to reduce repetition
        random.shuffle(rss_feeds)

        title, summary = None, None
        for url in rss_feeds:
            t, s = fetch_headline_and_summary(url)
            if t:
                title, summary = t, s
                break

        if not title:
            print("[WARN] No headline found at all")
            tweet = "No crypto news available right now. #crypto #news"
        else:
            tweet = create_tweet_text(title, summary)

        post_tweet(client, tweet)

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
