import os
import requests
import feedparser
from datetime import datetime, timezone

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

FEEDS = [
    ("US Politics", "https://news.google.com/rss/search?q=US+politics+stocks+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Trump", "https://news.google.com/rss/search?q=Trump+stocks+tariffs+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("World / War", "https://news.google.com/rss/search?q=war+geopolitics+markets+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Tariffs / Trade", "https://news.google.com/rss/search?q=tariffs+trade+stocks+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Technology", "https://news.google.com/rss/search?q=technology+stocks+AI+semiconductors+when:1h&hl=en-US&gl=US&ceid=US:en"),
]

KEYWORDS = [
    "trump",
    "tariff",
    "tariffs",
    "trade war",
    "sanctions",
    "war",
    "invasion",
    "missile",
    "military",
    "iran",
    "israel",
    "russia",
    "ukraine",
    "china",
    "taiwan",
    "oil",
    "opec",
    "semiconductor",
    "chip",
    "tesla",
    "nvidia",
    "apple",
    "amazon",
    "microsoft",
    "google",
    "meta",
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=20,
    )

    print(response.json())


def main():
    print("Market Radar started.")

    found = []

    for category, feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")

            text = title.lower()

            if any(keyword in text for keyword in KEYWORDS):
                found.append({
                    "category": category,
                    "title": title,
                    "link": link,
                    "published": published,
                })

    # Remove duplicate stories
    unique = {}
    for story in found:
        unique[story["link"]] = story

    stories = list(unique.values())

    if not stories:
        print("No relevant stories found.")
        return

    # Only send the first 3 stories for now
    stories = stories[:3]

    for story in stories:
        message = (
            f"🚨 MARKET RADAR\n\n"
            f"Category: {story['category']}\n\n"
            f"{story['title']}\n\n"
            f"Published: {story['published']}\n\n"
            f"{story['link']}"
        )

        send_telegram(message)

    print(f"Sent {len(stories)} alerts.")


if __name__ == "__main__":
    main()
