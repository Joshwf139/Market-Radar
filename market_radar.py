import os
import json
import requests
import feedparser
from google import genai

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

FEEDS = [
    (
        "US Politics",
        "https://news.google.com/rss/search?q=US+politics+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Trump / Policy",
        "https://news.google.com/rss/search?q=Trump+tariffs+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Geopolitics",
        "https://news.google.com/rss/search?q=war+geopolitics+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Trade / Tariffs",
        "https://news.google.com/rss/search?q=tariffs+trade+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Technology",
        "https://news.google.com/rss/search?q=AI+semiconductors+technology+stocks+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Energy",
        "https://news.google.com/rss/search?q=oil+OPEC+energy+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
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

    response.raise_for_status()


def collect_stories():
    stories = []

    for category, feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            published = entry.get("published", "").strip()

            if title and link:
                stories.append(
                    {
                        "category": category,
                        "title": title,
                        "link": link,
                        "published": published,
                    }
                )

    # Remove duplicate URLs
    unique = {}

    for story in stories:
        unique[story["link"]] = story

    return list(unique.values())


def analyze_with_ai(stories):
    numbered_stories = []

    for i, story in enumerate(stories, start=1):
        numbered_stories.append(
            f"""
STORY {i}
Category: {story['category']}
Title: {story['title']}
Published: {story['published']}
URL: {story['link']}
"""
        )

    stories_text = "\n".join(numbered_stories)

    prompt = f"""
You are the filtering system for a personal market-intelligence alert tool.

Your job is NOT to give investment advice and NOT to say whether someone should
buy or sell anything.

Review the news stories below and identify ONLY stories that appear potentially
important to financial markets because of a concrete new development.

Prioritize:
- major US government policy changes
- presidential statements or actions that could affect markets
- tariffs and trade restrictions
- sanctions
- wars or major military developments
- major geopolitical developments
- oil supply disruptions
- OPEC decisions
- China/Taiwan developments
- major semiconductor developments
- major technology-company developments
- significant regulatory actions affecting large public companies
- major company-specific political developments

Ignore:
- generic political commentary
- opinion pieces
- routine political news
- stories that merely mention Trump or another politician
- ordinary stock-market recaps
- generic "markets may..." articles
- old news being republished
- celebrity or entertainment stories
- stories with no clear connection to financial markets

For each selected story return:
- story_number
- importance: HIGH, MEDIUM, or LOW
- event: short description of what actually happened
- market_relevance: why the event could matter to markets
- affected_companies_or_sectors: specific companies or sectors if clearly relevant
- confidence: HIGH, MEDIUM, or LOW

Select no more than 3 stories.

If nothing is genuinely important, return an empty list.

Stories:
{stories_text}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "alerts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "story_number": {"type": "integer"},
                                "importance": {
                                    "type": "string",
                                    "enum": ["HIGH", "MEDIUM", "LOW"],
                                },
                                "event": {"type": "string"},
                                "market_relevance": {"type": "string"},
                                "affected_companies_or_sectors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "confidence": {
                                    "type": "string",
                                    "enum": ["HIGH", "MEDIUM", "LOW"],
                                },
                            },
                            "required": [
                                "story_number",
                                "importance",
                                "event",
                                "market_relevance",
                                "affected_companies_or_sectors",
                                "confidence",
                            ],
                        },
                    }
                },
                "required": ["alerts"],
            },
        },
    )

    return json.loads(response.text)


def main():
    print("Market Radar started.")

    stories = collect_stories()

    print(f"Collected {len(stories)} stories.")

    if not stories:
        print("No stories found.")
        return

    analysis = analyze_with_ai(stories)
    alerts = analysis.get("alerts", [])

    print(f"AI selected {len(alerts)} alerts.")

    for alert in alerts:
        story_number = alert["story_number"]

        if story_number < 1 or story_number > len(stories):
            continue

        story = stories[story_number - 1]

        companies = alert["affected_companies_or_sectors"]

        if companies:
            affected = ", ".join(companies)
        else:
            affected = "Not clearly identified"

        message = (
            f"🚨 MARKET RADAR\n\n"
            f"Importance: {alert['importance']}\n"
            f"Confidence: {alert['confidence']}\n\n"
            f"📰 {story['title']}\n\n"
            f"EVENT\n"
            f"{alert['event']}\n\n"
            f"MARKET RELEVANCE\n"
            f"{alert['market_relevance']}\n\n"
            f"EXPOSED COMPANIES / SECTORS\n"
            f"{affected}\n\n"
            f"Source:\n"
            f"{story['link']}"
        )

        send_telegram(message)

    print("Market Radar finished.")


if __name__ == "__main__":
    main()
