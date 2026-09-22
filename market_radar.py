import os
import json
import time
import requests
import feedparser
import yfinance as yf
from google import genai


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-3.5-flash-lite"

MEMORY_FILE = "seen_stories.json"

MAX_SEEN_STORIES = 2000


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
# MEMORY
# ============================================================

def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return set()

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return set(data)

    except Exception as e:

        print(
            f"Could not load memory: {e}"
        )

        return set()


def save_memory(seen):

    # Keep the file from becoming enormous
    recent = list(seen)[-MAX_SEEN_STORIES:]

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            recent,
            file,
            indent=2,
        )


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

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

    print(
        "Telegram alert sent."
    )


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_stories():

    stories = []

    for category, feed_url in FEEDS:

        print(
            f"Checking {category}..."
        )

        try:

            feed = feedparser.parse(
                feed_url
            )

            for entry in feed.entries[:10]:

                title = entry.get(
                    "title",
                    "",
                ).strip()

                link = entry.get(
                    "link",
                    "",
                ).strip()

                published = entry.get(
                    "published",
                    "",
                ).strip()

                if title and link:

                    stories.append(
                        {
                            "category": category,
                            "title": title,
                            "link": link,
                            "published": published,
                        }
                    )

        except Exception as e:

            print(
                f"Feed error: {e}"
            )

    unique = {}

    for story in stories:

        unique[
            story["link"]
        ] = story

    return list(
        unique.values()
    )


# ============================================================
# AI ANALYSIS
# ============================================================

def analyze_with_ai(stories):

    numbered = []

    for i, story in enumerate(
        stories,
        start=1,
    ):

        numbered.append(
            f"""
STORY {i}

Category: {story['category']}

Title: {story['title']}

Published: {story['published']}

URL: {story['link']}
"""
        )

    stories_text = "\n".join(
        numbered
    )

    prompt = f"""
You are an extremely selective LONG-ONLY market intelligence system.

The user manually buys stocks and does not short stocks.

Your most important instruction:

WHEN IN DOUBT, RETURN NO ALERT.

The user does NOT want a constant stream of market news.

They only want an alert when there is an unusually strong, concrete,
new and potentially positive catalyst for a specific publicly traded
company or sector.

============================================================
REQUIRED CONDITIONS
============================================================

A story should normally satisfy ALL of these:

1. It describes a concrete NEW development.

2. The development is potentially positive for a specific company
   or clearly identifiable sector.

3. The connection between the event and the beneficiary is strong.

4. The development could materially affect the company's business,
   addressable market, costs, supply, regulation, revenue opportunity,
   or competitive position.

5. The information comes from a credible source or is sufficiently
   concrete to justify high confidence.

6. The catalyst appears materially more important than ordinary
   daily market news.

============================================================
HIGH-VALUE CATALYSTS
============================================================

Pay particular attention to rare developments such as:

- Major government contracts
- Major regulatory approvals
- Important new government policy
- Tariff changes that clearly create beneficiaries
- Major semiconductor export-policy changes
- Major AI infrastructure developments
- Major energy supply changes
- Major defense contracts
- Large strategic partnerships
- Major technology breakthroughs
- Entry into a large previously inaccessible market
- Major competitor disruption
- Important supply shortages benefiting a specific producer
- Government programs creating significant new demand
- Major acquisitions or strategic transactions
- Other developments that could materially change a company's economics

============================================================
ASYMMETRIC CATALYSTS
============================================================

Also identify rare "ASYMMETRIC" situations.

An asymmetric situation is NOT a claim that the stock will rise 4x,
5x, 10x, or any other amount.

Instead, it means the event could potentially have an unusually large
effect on the company's future economics relative to its current size.

Examples include:

- A small public company gaining access to a huge new market
- A major regulatory approval for a company with a small existing business
- A transformative government contract
- A technology breakthrough with a very large addressable market
- A supply disruption that strongly benefits one identifiable producer
- A major competitor losing access to an important market

Only classify something as ASYMMETRIC when the evidence is unusually strong.

============================================================
DO NOT ALERT
============================================================

Do NOT alert on:

- Ordinary stock price movements
- Market recaps
- Generic political news
- Generic Trump commentary
- Opinions
- Analyst commentary alone
- Rumors
- Weak speculation
- Old news
- Negative catalysts
- Companies merely mentioned in a story
- Stories where the beneficiary is unclear
- Stories where the market relevance is weak
- Stories that merely say a stock "could rise"
- Stories that merely say a stock "is rallying"

============================================================
CONFIDENCE
============================================================

Only select stories with very high confidence.

Use:

95-100 = exceptional confidence
90-94 = very strong confidence
Below 90 = DO NOT ALERT

The confidence score represents confidence that:

- the event is real and new
- the event is material
- the company/sector connection is reasonable
- the catalyst is potentially positive

It does NOT represent the probability that a stock will rise.

============================================================
TICKERS
============================================================

Only include US-listed ticker symbols.

Never invent a ticker.

Only include a ticker if the company is clearly connected to the event.

============================================================
OUTPUT
============================================================

Return no more than ONE alert.

If nothing meets the threshold, return:

{{"alerts":[]}}

If something qualifies, return:

- story_number
- alert_title
- catalyst_type
- importance
- event
- affected_companies_or_sectors
- tickers
- market_relevance
- confidence
- asymmetric

catalyst_type must be one of:

"POLICY"
"REGULATION"
"CONTRACT"
"TECHNOLOGY"
"SUPPLY"
"ENERGY"
"GEOPOLITICS"
"COMPETITOR"
"PARTNERSHIP"
"OTHER"

importance must be:

"HIGH"

confidence must be an integer from 90 to 100.

asymmetric must be either:

true
false

The alert_title should be extremely concise.

Examples:

"NEW CHIP EXPORT POLICY"
"MAJOR DEFENSE CONTRACT"
"REGULATORY APPROVAL"
"MAJOR AI PARTNERSHIP"
"NEW MARKET ACCESS"

The event should be 1-2 concise sentences.

The market_relevance should be 1 concise sentence.

Do NOT provide investment advice.

Do NOT say "buy".

Do NOT say "sell".

Do NOT say "this stock will rise".

============================================================
STORIES
============================================================

{stories_text}
"""

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
                                        "catalyst_type": {
                                            "type": "string",
                                            "enum": [
                                                "POLICY",
                                                "REGULATION",
                                                "CONTRACT",
                                                "TECHNOLOGY",
                                                "SUPPLY",
                                                "ENERGY",
                                                "GEOPOLITICS",
                                                "COMPETITOR",
                                                "PARTNERSHIP",
                                                "OTHER",
                                            ],
                                        },
                                        "importance": {
                                            "type": "string",
                                            "enum": [
                                                "HIGH"
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
                                            "type": "integer"
                                        },
                                        "asymmetric": {
                                            "type": "boolean"
                                        },
                                    },
                                    "required": [
                                        "story_number",
                                        "alert_title",
                                        "catalyst_type",
                                        "importance",
                                        "event",
                                        "affected_companies_or_sectors",
                                        "tickers",
                                        "market_relevance",
                                        "confidence",
                                        "asymmetric",
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
                f"Gemini attempt "
                f"{attempt + 1} failed: {e}"
            )

            if attempt < 2:

                time.sleep(
                    5 * (attempt + 1)
                )

            else:

                raise


# ============================================================
# TECHNICAL MARKET DATA
# ============================================================

def get_price_setup(ticker):

    try:

        stock = yf.Ticker(
            ticker
        )

        history = stock.history(
            period="3mo",
            interval="1d",
            auto_adjust=True,
        )

        if history.empty:

            return None

        if len(history) < 20:

            return None

        current = float(
            history["Close"].iloc[-1]
        )

        recent = history.tail(
            20
        )

        support = float(
            recent["Low"].min()
        )

        resistance = float(
            recent["High"].max()
        )

        average_range = float(
            (
                recent["High"]
                - recent["Low"]
            ).mean()
        )

        entry_low = support * 1.01

        entry_high = min(
            current,
            support + average_range,
        )

        target_1 = resistance

        target_2 = resistance + (
            (resistance - support)
            * 0.5
        )

        invalidation = (
            support * 0.97
        )

        return {
            "current": round(
                current,
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
            f"Price data error "
            f"{ticker}: {e}"
        )

        return None


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "MARKET RADAR STARTED"
    )

    seen = load_memory()

    print(
        f"Memory contains "
        f"{len(seen)} stories."
    )

    stories = collect_stories()

    print(
        f"Collected "
        f"{len(stories)} total stories."
    )

    # --------------------------------------------------------
    # REMOVE ALREADY PROCESSED STORIES
    # --------------------------------------------------------

    new_stories = []

    for story in stories:

        if story["link"] not in seen:

            new_stories.append(
                story
            )

    print(
        f"Found "
        f"{len(new_stories)} new stories."
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Mark every retrieved story as processed.
    # This prevents the same story from triggering repeatedly.
    # --------------------------------------------------------

    for story in new_stories:

        seen.add(
            story["link"]
        )

    save_memory(
        seen
    )

    if not new_stories:

        print(
            "No new stories."
        )

        return

    # Limit AI workload
    new_stories = new_stories[
        :30
    ]

    # --------------------------------------------------------
    # AI FILTER
    # --------------------------------------------------------

    analysis = analyze_with_ai(
        new_stories
    )

    alerts = analysis.get(
        "alerts",
        []
    )

    print(
        f"AI returned "
        f"{len(alerts)} possible alerts."
    )

    if not alerts:

        print(
            "Nothing meets the alert threshold."
        )

        return

    # --------------------------------------------------------
    # STRICT CONFIDENCE CHECK
    # --------------------------------------------------------

    qualified = []

    for alert in alerts:

        confidence = alert.get(
            "confidence",
            0,
        )

        if confidence >= 90:

            qualified.append(
                alert
            )

    if not qualified:

        print(
            "No alert passed the "
            "90% confidence threshold."
        )

        return

    # Only ONE alert per run
    alert = qualified[0]

    story_number = alert.get(
        "story_number"
    )

    if not isinstance(
        story_number,
        int,
    ):

        print(
            "Invalid story number."
        )

        return

    if (
        story_number < 1
        or story_number > len(
            new_stories
        )
    ):

        print(
            "Story number out of range."
        )

        return

    story = new_stories[
        story_number - 1
    ]

    # --------------------------------------------------------
    # TICKERS
    # --------------------------------------------------------

    tickers = alert.get(
        "tickers",
        []
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

        if (
            ticker
            and ticker not in valid_tickers
        ):

            valid_tickers.append(
                ticker
            )

    # --------------------------------------------------------
    # MARKET SETUPS
    # --------------------------------------------------------

    setups = []

    for ticker in valid_tickers[:3]:

        setup = get_price_setup(
            ticker
        )

        if setup:

            setups.append(
                f"{ticker}: "
                f"${setup['current']} current | "
                f"${setup['entry_low']}-"
                f"${setup['entry_high']} reference entry | "
                f"${setup['target_1']} T1 | "
                f"${setup['target_2']} T2 | "
                f"${setup['invalidation']} invalidation"
            )

    if setups:

        setup_text = "\n".join(
            setups
        )

    else:

        setup_text = (
            "Market setup unavailable."
        )

    # --------------------------------------------------------
    # AFFECTED COMPANIES
    # --------------------------------------------------------

    companies = alert.get(
        "affected_companies_or_sectors",
        []
    )

    if companies:

        company_text = ", ".join(
            companies
        )

    else:

        company_text = (
            "Not specifically identified."
        )

    # --------------------------------------------------------
    # ASYMMETRIC LABEL
    # --------------------------------------------------------

    asymmetric = alert.get(
        "asymmetric",
        False,
    )

    if asymmetric:

        asymmetric_text = (
            "\n\nASYMMETRIC CATALYST\n"
            "Potentially unusually large "
            "economic impact relative to "
            "the company's current scale. "
            "Highly uncertain."
        )

    else:

        asymmetric_text = ""

    # --------------------------------------------------------
    # FINAL ALERT
    # --------------------------------------------------------

    message = (
        f"{alert['alert_title']}\n\n"

        f"What happened:\n"
        f"{alert['event']}\n\n"

        f"Affected:\n"
        f"{company_text}\n\n"

        f"Why it matters:\n"
        f"{alert['market_relevance']}\n\n"

        f"Market setup:\n"
        f"{setup_text}\n\n"

        f"Confidence: "
        f"{alert['confidence']}/100\n"

        f"Type: "
        f"{alert['catalyst_type']}"
        f"{asymmetric_text}\n\n"

        f"Source:\n"
        f"{story['link']}"
    )

    send_telegram(
        message
    )

    print(
        "Alert sent."
    )

    print(
        "MARKET RADAR FINISHED"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
