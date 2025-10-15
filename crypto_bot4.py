import os
import re
import tweepy
import feedparser
import traceback

# --- Clean HTML (remove images, tags, extra spaces) ---
def clean_html(raw_html):
    # Remove <img> tags
    raw_html = re.sub(r'<img[^>]+>', '', raw_html)
    # Remove all other HTML tags
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    return clean_text.strip()

# --- Load Twitter client ---
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

# --- Fetch headline and clean summary ---
def fetch_headline_and_summary(rss_url):
    print(f"[INFO] Fetching from: {rss_url}")
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        print(f"[ERROR] Failed to parse feed: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        print("[WARN] No articles found.")
        return None, None

    entry = feed.entries[0]
    title = entry.title.strip()
    raw_summary = entry.get("summary", "") or entry.get("description", "")
    summary = clean_html(raw_summary)
    return title, summary

# --- Format tweet within 250 characters ---
def create_tweet_text(title, summary, hashtags="#crypto #news", max_length=250):
    text = f"📰 {title}\n\n{summary}\n\n{hashtags}"

    if len(text) <= max_length:
        return text

    # Truncate summary if too long
    reserved = len(f"📰 {title}\n\n\n\n{hashtags}")
    allowed_summary = max_length - reserved - 3  # for "..."
    if allowed_summary < 0:
        # Even the title + hashtags too long
        allowed_title = max_length - len(f"📰 \n\n\n\n{hashtags}") - 3
        title = title[:allowed_title].rstrip() + "..."
        return f"📰 {title}\n\n{hashtags}"

    summary = summary[:allowed_summary].rstrip() + "..."
    return f"📰 {title}\n\n{summary}\n\n{hashtags}"

# --- Post the tweet ---
def post_tweet(client, text):
    try:
        print(f"[INFO] Posting tweet ({len(text)} characters):")
        print(text)
        response = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted:", response.data.get("id"))
    except Exception as e:
        print("[ERROR] Failed to post tweet:", e)
        traceback.print_exc()

# --- Main workflow ---
def main():
    try:
        print("[INFO] Crypto News Bot Started")

        client = load_twitter_client()

        rss_feeds = [
            "https://feeds.feedburner.com/CoinDesk",
            "https://cointelegraph.com/rss",
            "https://cryptoslate.com/feed/"
        ]

        title, summary = None, None
        for feed in rss_feeds:
            title, summary = fetch_headline_and_summary(feed)
            if title and summary:
                break

        if not title:
            print("[WARN] No headline found.")
            tweet = "No crypto news available right now. #crypto #news"
        else:
            tweet = create_tweet_text(title, summary)

        post_tweet(client, tweet)

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
