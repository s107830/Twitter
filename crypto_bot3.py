import os
import re
import tweepy
import feedparser
import traceback

# --- Clean HTML from summaries ---
def clean_html(raw_html):
    clean_text = re.sub('<[^<]+?>', '', raw_html)  # Remove all HTML tags
    return clean_text.strip()

# --- Load Twitter API client from environment variables ---
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

# --- Fetch headline and cleaned summary from RSS ---
def fetch_headline_and_summary(rss_url):
    print(f"[INFO] Fetching from {rss_url}")
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; CryptoBot/1.0)"
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        print(f"[ERROR] Feed parsing error: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        print("[WARN] No entries found.")
        return None, None

    entry = feed.entries[0]
    title = entry.title.strip()
    raw_summary = entry.summary if "summary" in entry else entry.get("description", "")
    summary = clean_html(raw_summary)
    return title, summary

# --- Format tweet text under 250 characters ---
def create_tweet_text(title, summary, hashtags="#crypto #news", max_length=250):
    tweet = f"📰 {title}\n\n{summary}\n\n{hashtags}"

    if len(tweet) <= max_length:
        return tweet

    # If too long, trim the summary
    reserved = len(f"📰 {title}\n\n\n\n{hashtags}")
    allowed_summary_len = max_length - reserved - 3  # for "..."
    if allowed_summary_len < 0:
        # Even title + hashtags too long — trim title
        allowed_title_len = max_length - len(f"📰 \n\n\n\n{hashtags}") - 3
        title = title[:allowed_title_len].rstrip() + "..."
        return f"📰 {title}\n\n{hashtags}"

    summary = summary[:allowed_summary_len].rstrip() + "..."
    return f"📰 {title}\n\n{summary}\n\n{hashtags}"

# --- Post to Twitter ---
def post_tweet(client, text):
    try:
        print(f"[INFO] Tweet length: {len(text)}")
        print(f"[INFO] Tweet content:\n{text}\n")
        resp = client.create_tweet(text=text)
        print("[SUCCESS] Tweet posted. ID:", resp.data.get("id"))
    except Exception as e:
        print("[ERROR] Failed to post tweet:", e)
        traceback.print_exc()

# --- Main execution ---
def main():
    try:
        print("[INFO] Starting crypto news bot...")

        client = load_twitter_client()

        rss_feeds = [
            "https://feeds.feedburner.com/CoinDesk",
            "https://cointelegraph.com/rss",
            "https://cryptoslate.com/feed/"
        ]

        headline = None
        summary = None

        for rss in rss_feeds:
            headline, summary = fetch_headline_and_summary(rss)
            if headline and summary:
                break

        if not headline:
            print("[WARN] No valid news found.")
            tweet_text = "No crypto news available at the moment. #crypto #news"
        else:
            tweet_text = create_tweet_text(headline, summary)

        post_tweet(client, tweet_text)

        print("[INFO] Done.")

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()

# --- Run ---
if __name__ == "__main__":
    main()
