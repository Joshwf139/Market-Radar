import os
import json
import time
import requests
import feedparser
import yfinance as yf
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-3.5-flash-lite"


# ============================================================
# NEWS FEEDS
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
        "Trade / Tariffs",
        "https://news.google.com/rss/search?q=tariffs+trade+markets+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Geopolitics",
        "https://news.google.com/rss/search?q=geopolitics+markets+stocks+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "China / Taiwan",
        "https://news.google.com/rss/search?q=China+Taiwan+markets+stocks+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Technology / Semiconductors",
        "https://news.google.com/rss/search?q=AI+semiconductors+chips+stocks+when:1h&hl=en-US&gl=US&ceid=US:en",
    ),
    (
        "Energy / Oil",
        "https://news.google.com/rss/search?q=oil+OPEC+energy+stocks+when:1h&hl=en-US&gl=US&ceid=US:en",
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

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:10]:

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                published = entry.get("published", "").strip()

                source_name = ""

                source = entry.get("source")

                if isinstance(source, dict):
                    source_name = source.get("title", "")

                if not source_name:
                    source_name = "Google News"

                if title and link:

                    stories.append(
                        {
                            "category": category,
                            "title": title,
                            "link": link,
                            "published": published,
                            "source": source_name,
                        }
                    )

        except Exception as e:

            print(
                f"Could not read {category}: {e}"
            )

    # Remove duplicate URLs
    unique = {}

    for story in stories:
        unique[story["link"]] = story

    return list(unique.values())


# ============================================================
# GEMINI ANALYSIS
# ============================================================

def analyze_with_ai(stories):

    numbered_stories = []

    for i, story in enumerate(stories, start=1):

        numbered_stories.append(
            f"""
STORY {i}

Category:
{story['category']}

Source:
{story['source']}

Title:
{story['title']}

Published:
{story['published']}

URL:
{story['link']}
"""
        )

    stories_text = "\n".join(
        numbered_stories
    )

    prompt = f"""
You are the filtering system for a LONG-ONLY market intelligence alert tool.

The user manually buys stocks through a brokerage and does not short stocks.

Your job is to identify ONLY NEW developments that could reasonably be
POSITIVE for a publicly traded company or sector.

Do NOT give investment advice.

Do NOT tell the user to buy or sell anything.

Do NOT claim that a stock will definitely rise.

Your job is to identify potentially positive market catalysts and explain
why they may matter.

============================================================
ALERT CRITERIA
============================================================

Alert when there is a concrete NEW development such as:

- A company receives a major government contract.
- A company receives favorable regulatory treatment.
- A tariff or trade policy could benefit a specific company or domestic sector.
- A competitor faces a regulatory or supply-chain disadvantage.
- A company announces a major partnership.
- A company announces a major product or technology breakthrough.
- A company receives important government approval.
- A major supply disruption could benefit an identifiable company.
- Oil or commodity developments could benefit identifiable companies.
- Positive developments involving semiconductors, AI, energy, defense,
  infrastructure, manufacturing, or other major sectors.
- A geopolitical development creates a clearly identifiable positive catalyst
  for a public company or sector.
- A major policy announcement creates a plausible positive catalyst for
  a specific public company.

============================================================
DO NOT ALERT
============================================================

Do NOT alert on:

- Negative company news.
- Market crashes.
- Generic political commentary.
- Generic stock-market recaps.
- Opinion pieces.
- Old news.
- Stories that merely mention Trump or another politician.
- Stories that merely mention tariffs without a concrete new development.
- Stories where the positive market connection is unclear.
- Stories where the only reason for an alert is that a stock went up.
- General economic news with no identifiable beneficiary.
- Rumors with no credible supporting information.
- Predictions about what politicians or companies might do without evidence
  of an actual new development.

============================================================
IMPORTANT
============================================================

A story must contain a concrete EVENT.

The event must be NEW or DEVELOPING.

Do not confuse "the stock rose" with a positive catalyst.

Prefer primary sources and high-quality financial sources.

Do not assume a company benefits merely because it operates in the same
industry.

Only identify companies when the connection to the event is reasonably clear.

Do not invent ticker symbols.

For example, if a story discusses a tariff affecting a specific product,
identify companies only when there is a reasonable basis for saying that
the policy could benefit those companies.

============================================================
TICKERS
============================================================

Only include US-listed stock ticker symbols.

Examples:

NVIDIA = NVDA
Apple = AAPL
Amazon = AMZN
Microsoft = MSFT
Tesla = TSLA

Only provide a ticker when you are reasonably confident it is correct.

If there is no clearly identifiable public-company beneficiary, use:

[]

============================================================
OUTPUT
============================================================

For every selected story return:

- story_number
- alert_title
- importance
- event
- affected_companies_or_sectors
- tickers
- market_relevance
- confidence

importance must be one of:

HIGH
MEDIUM
LOW

confidence must be one of:

HIGH
MEDIUM
LOW

The alert_title should be short and describe the actual catalyst.

Examples:

"NEW TARIFF ANNOUNCED"
"MAJOR GOVERNMENT CONTRACT"
"NEW CHIP EXPORT POLICY"
"OIL SUPPLY DISRUPTION"
"REGULATORY APPROVAL"
"MAJOR AI PARTNERSHIP"

The event should explain what actually happened.

The market_relevance should explain why the event could potentially benefit
the identified companies or sectors.

Do not say:

"Buy NVDA."

Do not say:

"NVDA will rise."

Instead say something like:

"This could improve demand for US-based semiconductor suppliers."

Select no more than 3 stories.

If there are no genuinely positive market catalysts, return an empty list.

Stories:

{stories_text}
"""

    # Retry temporary Gemini server failures
    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=GEMINI_MODEL,
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
                                                "LOW",
                                            ],
                                        },
                                        "event": {
                                            "type": "string"
                                        },
                                        "affected_companies_or_sectors": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                        },
                                        "tickers": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                        },
                                        "market_relevance": {
                                            "type": "string"
                                        },
                                        "confidence": {
                                            "type": "string",
                                            "enum": [
                                                "HIGH",
                                                "MEDIUM",
                                                "LOW",
                                            ],
                                        },
                                    },
                                    "required": [
                                        "story_number",
                                        "alert_title",
                                        "importance",
                                        "event",
                                        "affected_companies_or_sectors",
                                        "tickers",
                                        "market_relevance",
                                        "confidence",
                                    ],
                                },
                            }
                        },
                        "required": [
                            "alerts"
                        ],
                    },
                },
            )

            return json.loads(
                response.text
            )

        except Exception as e:

            print(
                f"Gemini attempt {attempt + 1} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (
                    attempt + 1
                )

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

            else:

                raise


# ============================================================
# PRICE / TECHNICAL ANALYSIS
# ============================================================

def get_price_setup(ticker):

    try:

        print(
            f"Getting market data for {ticker}..."
        )

        stock = yf.Ticker(ticker)

        history = stock.history(
            period="3mo",
            interval="1d",
            auto_adjust=True,
        )

        if history.empty:

            print(
                f"No market data for {ticker}."
            )

            return None

        if len(history) < 20:

            print(
                f"Not enough market data for {ticker}."
            )

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
            (
                recent_20["High"]
                - recent_20["Low"]
            ).mean()
        )

        # Technical reference entry zone
        entry_low = support * 1.01

        entry_high = min(
            current_price,
            support + average_range,
        )

        # Recent resistance
        target_1 = resistance

        # Simple resistance extension
        target_2 = resistance + (
            (resistance - support) * 0.5
        )

        # Invalidation below recent support
        invalidation = support * 0.97

        return {
            "current_price": round(
                current_price,
                2,
            ),
            "entry_low": round(
                entry_low,
                2,
            ),
            "entry_high": round(
                entry_high,
                2,
            ),
            "target_1": round(
                target_1,
                2,
            ),
            "target_2": round(
                target_2,
                2,
            ),
            "invalidation": round(
                invalidation,
                2,
            ),
        }

    except Exception as e:

        print(
            f"Could not get price data for {ticker}: {e}"
        )

        return None


# ============================================================
# FORMAT MARKET SETUP
# ============================================================

def format_market_setup(ticker):

    setup = get_price_setup(
        ticker
    )

    if not setup:

        return (
            f"{ticker}\n"
            f"Market data unavailable."
        )

    return (
        f"{ticker}\n"
        f"Current: ${setup['current_price']}\n"
        f"Entry zone: "
        f"${setup['entry_low']} - "
        f"${setup['entry_high']}\n"
        f"Target 1: "
        f"${setup['target_1']}\n"
        f"Target 2: "
        f"${setup['target_2']}\n"
        f"Invalidation: "
        f"${setup['invalidation']}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "================================"
    )

    print(
        "MARKET RADAR STARTED"
    )

    print(
        "================================"
    )

    # --------------------------------------------------------
    # COLLECT NEWS
    # --------------------------------------------------------

    stories = collect_stories()

    print(
        f"Collected {len(stories)} stories."
    )

    if not stories:

        print(
            "No stories found."
        )

        return

    # --------------------------------------------------------
    # AI FILTER
    # --------------------------------------------------------

    analysis = analyze_with_ai(
        stories
    )

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

    # --------------------------------------------------------
    # SEND ALERTS
    # --------------------------------------------------------

    for alert in alerts[:3]:

        story_number = alert.get(
            "story_number"
        )

        if not isinstance(
            story_number,
            int,
        ):

            continue

        if (
            story_number < 1
            or story_number > len(stories)
        ):

            continue

        story = stories[
            story_number - 1
        ]

        # ----------------------------------------------------
        # COMPANIES / SECTORS
        # ----------------------------------------------------

        companies = alert.get(
            "affected_companies_or_sectors",
            [],
        )

        if companies:

            affected = "\n".join(
                f"• {company}"
                for company in companies
            )

        else:

            affected = (
                "No specific public-company "
                "beneficiary identified."
            )

        # ----------------------------------------------------
        # MARKET SETUPS
        # ----------------------------------------------------

        tickers = alert.get(
            "tickers",
            [],
        )

        valid_tickers = []

        for ticker in tickers:

            if not isinstance(
                ticker,
                str,
            ):

                continue

            ticker = (
                ticker
                .strip()
                .upper()
            )

            if ticker and ticker not in valid_tickers:

                valid_tickers.append(
                    ticker
                )

        if valid_tickers:

            setups = []

            for ticker in valid_tickers[:5]:

                setups.append(
                    format_market_setup(
                        ticker
                    )
                )

            market_setup = (
                "\n\n".join(setups)
            )

        else:

            market_setup = (
                "No specific public-company "
                "technical setup available."
            )

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        source_name = story.get(
            "source",
            "Google News",
        )

        source_text = (
            f"{source_name}\n"
            f"{story['link']}"
        )

        # ----------------------------------------------------
        # TELEGRAM MESSAGE
        # ----------------------------------------------------

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

            f"⚡ IMPORTANCE\n"
            f"{alert['importance']}\n\n"

            f"🔗 SOURCE\n"
            f"{source_text}\n\n"

            f"⚠️ Technical levels are reference levels "
            f"based on recent price history, not guarantees."
        )

        try:

            send_telegram(
                message
            )

        except Exception as e:

            print(
                f"Telegram error: {e}"
            )

    print(
        "================================"
    )

    print(
        "MARKET RADAR FINISHED"
    )

    print(
        "================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
