import os
import tweepy
import feedparser
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

def fetch_headline_and_summary(rss_url):
    print(f"[INFO] Fetching headline and summary from {rss_url}")
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; CryptoBot/1.0)"
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        print(f"[ERROR] Feed parsing error: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        print("[WARN] No entries found in feed.")
        return None, None

    entry = feed.entries[0]
    title = entry.title.strip()
    # Try 'summary' or fallback to 'description'
    summary = entry.summary if "summary" in entry else (entry.get("description") or "")
    return title, summary

def create_tweet_text(title, summary, hashtags="#crypto #news"):
    # Reserve chars for hashtags and buffer
    max_length = 280 - len(hashtags) - 5  # emoji, spaces, line breaks

    full_text = f"📰 {title}\n\n{summary}"

    if len(full_text) > max_length:
        allowed_summary_length = max_length - len(f"📰 {title}\n\n") - 3  # for "..."
        summary_truncated = summary[:allowed_summary_length].rstrip() + "..."
        full_text = f"📰 {title}\n\n{summary_truncated}"

    full_text = f"{full_text}\n\n{hashtags}"
    return full_text

def post_tweet(client, text):
    try:
        if len(text) > 280:
            print("[WARN] Tweet too long, trimming...")
            text = text[:275] + "…"
        print("[INFO] Posting tweet...")
        resp = client.create_tweet(text=text)
        print("[INFO] Tweet posted:", resp)
    except Exception as e:
        print("[ERROR] Error posting tweet:", e)
        traceback.print_exc()

def main():
    try:
        print("[INFO] Starting crypto news headline + summary bot")

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
            print("[WARN] No headline found from any feed.")
            tweet_text = "No crypto news available at the moment. #crypto #news"
        else:
            tweet_text = create_tweet_text(headline, summary)

        print("[INFO] Tweet content:\n", tweet_text)
        post_tweet(client, tweet_text)

        print("[INFO] Bot run completed.")

    except Exception as e:
        print("[FATAL ERROR]", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
