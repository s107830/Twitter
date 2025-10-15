import os
import re
import tweepy
import feedparser
import traceback

def clean_html(raw_html):
    raw_html = re.sub(r'<img[^>]+>', '', raw_html)
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    return clean_text.strip()

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

def fetch_headline_and_summary(rss_url):
    print(f"[INFO] Fetching from: {rss_url}")
    feed = feedparser.parse(rss_url)

    print("[DEBUG] feed.status:", feed.get("status"))
    print("[DEBUG] feed.bozo:", feed.bozo)
    if feed.bozo:
        print("[ERROR] feed parsing error:", feed.bozo_exception)
    print("[DEBUG] entries count:", len(feed.entries))

    if not feed.entries:
        return None, None

    entry = feed.entries[0]
    title = entry.title.strip() if hasattr(entry, "title") else None
    raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    summary = clean_html(raw_summary)
    return title, summary

def create_tweet_text(title, summary, hashtags="#crypto #news", max_length=250):
    if summary:
        text = f"📰 {title}\n\n{summary}\n\n{hashtags}"
    else:
        text = f"📰 {title}\n\n{hashtags}"

    if len(text) <= max_length:
        return text

    # If too long, try truncating summary
    if summary:
        reserved = len(f"📰 {title}\n\n\n\n{hashtags}")
        allowed_summary = max_length - reserved - 3
        if allowed_summary > 0:
            summary = summary[:allowed_summary].rstrip() + "..."
            return f"📰 {title}\n\n{summary}\n\n{hashtags}"
        else:
            # Summary has no room; drop it altogether
            allowed_title = max_length - len(f"📰 \n\n{hashtags}") - 3
            title = title[:allowed_title].rstrip() + "..."
            return f"📰 {title}\n\n{hashtags}"
    else:
        # No summary, just title + hashtags already fits or truncated
        if len(text) > max_length:
            allowed_title = max_length - len(f"📰 \n\n{hashtags}") - 3
            title = title[:allowed_title].rstrip() + "..."
            return f"📰 {title}\n\n{hashtags}"
        return text

def post_tweet(client, text):
    try:
        print(f"[INFO] Tweet length: {len(text)}")
        print("[INFO] Tweet content:\n", text)
        resp = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted:", resp)
    except Exception as e:
        print("[ERROR] Failed to post tweet:", e)
        traceback.print_exc()

def main():
    try:
        print("[INFO] Bot started")

        client = load_twitter_client()

        rss_feeds = [
            "https://feeds.feedburner.com/CoinDesk",
            "https://cointelegraph.com/rss",
            "https://cryptoslate.com/feed/"
        ]

        title, summary = None, None
        for url in rss_feeds:
            t, s = fetch_headline_and_summary(url)
            print("[DEBUG] got:", t, "| summary length:", len(s) if s else 0)
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
