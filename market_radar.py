import os
import json
import requests
import feedparser
import yfinance as yf
from google import genai


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# NEWS SOURCES
# ============================================================

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


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()

    print("Telegram alert sent.")


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_stories():
    stories = []

    for category, feed_url in FEEDS:
        print(f"Checking {category}...")

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

    # Remove duplicate stories
    unique = {}

    for story in stories:
        unique[story["link"]] = story

    return list(unique.values())


# ============================================================
# GEMINI NEWS ANALYSIS
# ============================================================

def analyze_with_ai(stories):

    numbered_stories = []

    for i, story in enumerate(stories, start=1):
        numbered_stories.append(
            f"""
STORY {i}

Category:
{story['category']}

Title:
{story['title']}

Published:
{story['published']}

URL:
{story['link']}
"""
        )

    stories_text = "\n".join(numbered_stories)

    prompt = f"""
You are the filtering system for a LONG-ONLY market intelligence alert tool.

The user manually buys stocks through a brokerage and does not short stocks.

Your job is to identify ONLY NEW developments that could reasonably be
POSITIVE for a publicly traded company or sector.

Do NOT give investment advice.
Do NOT tell the user to buy or sell anything.
Do NOT predict that a stock will rise.

Only identify potentially positive market catalysts.

============================================================
WHAT SHOULD TRIGGER AN ALERT
============================================================

Alert when there is a concrete new development such as:

- A company receives a major government contract
- A company receives favourable regulatory treatment
- A tariff or trade policy could benefit a specific company or domestic sector
- A competitor faces a regulatory or supply-chain disadvantage
- A company announces a major partnership
- A company announces a major product or technology breakthrough
- A company receives important government approval
- A major supply disruption could benefit a specific company
- Oil or commodity developments that could benefit identifiable companies
- Positive developments involving semiconductors, AI, energy, defence,
  infrastructure, or other major market sectors
- A geopolitical development that creates a clearly identifiable positive
  catalyst for a public company or sector

============================================================
DO NOT ALERT ON
============================================================

Do NOT alert on:

- Negative company news
- Market crashes
- Generic political commentary
- Generic stock-market recaps
- Opinion pieces
- Old news
- Stories that merely mention Trump or another politician
- Stories where the positive market connection is unclear
- Stories where the only reason for an alert is that a stock went up
- General economic news with no identifiable company or sector beneficiary
- Speculation without a concrete new development

============================================================
IMPORTANT
============================================================

A story must contain a concrete EVENT.

Do not confuse "the stock rose" with a positive catalyst.

Prefer primary sources and high-quality financial sources when identifiable.

Do not assume that a company benefits merely because it operates in the
same industry.

Only identify companies when the connection to the event is reasonably clear.

Do not invent ticker symbols.

============================================================
OUTPUT
============================================================

For every selected story return:

- story_number
- alert_title
- importance: HIGH, MEDIUM, or LOW
- event
- affected_companies_or_sectors
- tickers
- market_relevance
- confidence

The alert_title should be short and describe the actual catalyst.

Examples:

"NEW TARIFF ANNOUNCED"
"MAJOR GOVERNMENT CONTRACT"
"NEW CHIP EXPORT POLICY"
"OIL SUPPLY DISRUPTION"
"REGULATORY APPROVAL"

For tickers:

Only include US-listed stock ticker symbols when the connection is
reasonably clear.

Do not invent ticker symbols.

If no specific public company can be identified, return an empty list.

Select no more than 3 stories.

If there are no genuinely positive market catalysts, return an empty list.

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
                                "story_number": {
                                    "type": "integer"
                                },
                                "alert_title": {
                                    "type": "string"
                                },
                                "importance": {
                                    "type": "string",
                                    "enum": [
                                        "HIGH",
                                        "MEDIUM",
                                        "LOW"
                                    ]
                                },
                                "event": {
                                    "type": "string"
                                },
                                "affected_companies_or_sectors": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "tickers": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "market_relevance": {
                                    "type": "string"
                                },
                                "confidence": {
                                    "type": "string",
                                    "enum": [
                                        "HIGH",
                                        "MEDIUM",
                                        "LOW"
                                    ]
                                }
                            },
                            "required": [
                                "story_number",
                                "alert_title",
                                "importance",
                                "event",
                                "affected_companies_or_sectors",
                                "tickers",
                                "market_relevance",
                                "confidence"
                            ]
                        }
                    }
                },
                "required": [
                    "alerts"
                ]
            }
        }
    )

    return json.loads(response.text)


# ============================================================
# PRICE / TECHNICAL ANALYSIS
# ============================================================

def get_price_setup(ticker):

    try:

        print(f"Getting price data for {ticker}...")

        stock = yf.Ticker(ticker)

        history = stock.history(
            period="3mo",
            interval="1d"
        )

        if history.empty or len(history) < 20:
            print(f"Not enough price data for {ticker}.")
            return None

        current_price = float(
            history["Close"].iloc[-1]
        )

        recent_20 = history.tail(20)

        support = float(
            recent_20["Low"].min()
        )

        resistance = float(
            recent_20["High"].max()
        )

        average_range = float(
            (recent_20["High"] - recent_20["Low"]).mean()
        )

        # Basic entry zone near recent support
        entry_low = support * 1.01

        entry_high = min(
            current_price,
            support + average_range
        )

        # First target = recent resistance
        target_1 = resistance

        # Second target = extension above resistance
        target_2 = resistance + (
            (resistance - support) * 0.5
        )

        # Technical invalidation below support
        invalidation = support * 0.97

        return {
            "current_price": round(current_price, 2),
            "entry_low": round(entry_low, 2),
            "entry_high": round(entry_high, 2),
            "target_1": round(target_1, 2),
            "target_2": round(target_2, 2),
            "invalidation": round(invalidation, 2),
        }

    except Exception as e:

        print(
            f"Could not get price data for {ticker}: {e}"
        )

        return None


# ============================================================
# FORMAT PRICE SETUP
# ============================================================

def format_price_setup(ticker):

    setup = get_price_setup(ticker)

    if not setup:
        return (
            f"{ticker}\n"
            f"Price data unavailable."
        )

    return (
        f"{ticker}\n"
        f"Current: ${setup['current_price']}\n"
        f"Entry zone: ${setup['entry_low']} - "
        f"${setup['entry_high']}\n"
        f"Target 1: ${setup['target_1']}\n"
        f"Target 2: ${setup['target_2']}\n"
        f"Invalidation: ${setup['invalidation']}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Market Radar started.")

    stories = collect_stories()

    print(
        f"Collected {len(stories)} stories."
    )

    if not stories:

        print("No stories found.")

        return

    analysis = analyze_with_ai(stories)

    alerts = analysis.get(
        "alerts",
        []
    )

    print(
        f"AI selected {len(alerts)} alerts."
    )

    if not alerts:

        print(
            "No positive market catalysts found."
        )

        return

    for alert in alerts:

        story_number = alert["story_number"]

        if (
            story_number < 1
            or story_number > len(stories)
        ):
            continue

        story = stories[
            story_number - 1
        ]

        companies = alert[
            "affected_companies_or_sectors"
        ]

        tickers = alert.get(
            "tickers",
            []
        )

        if companies:

            affected = "\n".join(
                f"• {company}"
                for company in companies
            )

        else:

            affected = (
                "No specific company identified."
            )

        if tickers:

            setups = []

            for ticker in tickers[:5]:

                setups.append(
                    format_price_setup(
                        ticker
                    )
                )

            market_setup = "\n\n".join(
                setups
            )

        else:

            market_setup = (
                "No specific public-company "
                "price setup available."
            )

        message = (
            f"🚨 {alert['alert_title']}\n\n"

            f"📰 WHAT HAPPENED\n"
            f"{alert['event']}\n\n"

            f"🏢 AFFECTED COMPANIES / SECTORS\n"
            f"{affected}\n\n"

            f"📈 MARKET RELEVANCE\n"
            f"{alert['market_relevance']}\n\n"

            f"📊 MARKET SETUP\n"
            f"{market_setup}\n\n"

            f"🎯 CONFIDENCE\n"
            f"{alert['confidence']}\n\n"

            f"🗂 IMPORTANCE\n"
            f"{alert['importance']}\n\n"

            f"🔗 SOURCE\n"
            f"{story['link']}"
        )

        send_telegram(
            message
        )

    print(
        "Market Radar finished."
    )


if __name__ == "__main__":
    main()
