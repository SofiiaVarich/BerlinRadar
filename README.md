# BerlinRadar 🚀

BerlinRadar is a Telegram bot for discovering upcoming technology, startup, and business events in Berlin. It collects structured event data from configured sources, normalizes and categorizes events, removes likely duplicates, stores them in SQLite, and delivers filtered results and daily recommendations through Telegram.

## Current capabilities

- Telegram command and button-based navigation.
- Upcoming, weekly, weekend, free, and keyword event searches.
- Category and free-event preferences.
- Daily send-once recommendations for subscribed users.
- SQLite event, preference, and notification-history storage.
- Scheduled collection with APScheduler.
- Deterministic professional-category classification.
- Duplicate detection within each collection run.
- Direct links to event registration pages.
- User preference and notification-history deletion.

BerlinRadar only stores events located in the configured city and matching at least one supported professional category.

## Commands

| Command | Description |
|---|---|
| `/start` | Open the bot and display the main menu |
| `/help` | Display usage instructions |
| `/events` | Show upcoming matching events |
| `/week` | Show events through the end of this week |
| `/weekend` | Show events during the upcoming/current weekend |
| `/free` | Show free events |
| `/search AI` | Search by title, description, or category |
| `/settings` | Select categories and the free-only preference |
| `/subscribe` | Enable or disable daily recommendations |
| `/delete_me` | Delete stored preferences and notification history |

The persistent Telegram keyboard provides buttons for the main search and settings actions.

## Categories

- AI & Machine Learning
- Software Development
- Cybersecurity
- Startups
- Business & Networking
- Venture Capital
- Product Management
- Marketing & Sales

Classification uses deterministic keyword and phrase matching. AI-based classification is not currently implemented.

## Event sources

Sources are opt-in and must comply with each platform's terms of service.

| Source | Current behavior | Configuration |
|---|---|---|
| Structured event pages | Parses Schema.org `Event` JSON-LD from explicitly permitted URLs | `EVENT_FEED_URLS` |
| Eventbrite | Imports live events owned by organizations associated with the authenticated account | `EVENTBRITE_TOKEN` |
| Meetup | Imports events available through the authenticated user's GraphQL `self.events` response | `MEETUP_ACCESS_TOKEN` |

The Eventbrite and Meetup adapters do **not** provide general Berlin-wide public discovery. Without a configured source, the bot runs normally but has no events to display. LinkedIn and arbitrary website scraping are not implemented because access restrictions and terms must be respected.

## Architecture

```text
Configured sources
       │
       ▼
Collectors ──► normalization and classification
       │
       ▼
In-run duplicate detection
       │
       ▼
SQLite repository
       │
       ├──► filtering and search ──► Telegram commands
       │
       └──► daily scheduler ──► send-once notifications
```

### Project structure

```text
BerlinRadar/
├── bot/
│   ├── main.py                 # Application composition and polling
│   ├── handlers/               # Commands and button handlers
│   └── keyboards/              # Reply and inline keyboards
├── collectors/
│   ├── base.py                 # Collector interface
│   ├── eventbrite.py
│   ├── meetup.py
│   └── websites.py             # Schema.org Event JSON-LD
├── services/
│   ├── event_service.py        # Collection and event queries
│   ├── filtering.py
│   ├── deduplication.py
│   └── notifications.py
├── database/
│   ├── models.py
│   └── repository.py
├── scheduler/jobs.py
├── tests/
├── config.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## Event model

Events use a timezone-aware normalized representation:

```json
{
  "id": 1,
  "external_id": "event_123",
  "title": "Berlin AI Meetup",
  "starts_at": "2026-11-25T17:30:00+00:00",
  "location": "Berlin Mitte, Berlin",
  "url": "https://example.com/event",
  "source": "website",
  "description": "AI networking event",
  "categories": ["AI & Machine Learning", "Business & Networking"],
  "price": 0,
  "currency": "EUR",
  "created_at": "2026-11-17T08:00:00+00:00"
}
```

Timestamps are normalized to UTC for persistence and converted to the configured timezone for Telegram display.

## Installation

Requirements: Python 3.12 or later.

```bash
git clone https://github.com/SofiiaVarich/BerlinRadar.git
cd BerlinRadar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Create a bot with [@BotFather](https://t.me/BotFather), then configure `.env`:

```env
TELEGRAM_BOT_TOKEN=your_botfather_token
DATABASE_URL=sqlite:///events.db
DEFAULT_CITY=Berlin
TIMEZONE=Europe/Berlin
EVENT_UPDATE_INTERVAL_HOURS=6
NOTIFICATION_HOUR=9

# Optional source configuration
EVENTBRITE_TOKEN=
MEETUP_ACCESS_TOKEN=
EVENT_FEED_URLS=https://example.org/events,https://example.net/meetups
```

`EVENT_FEED_URLS` is a comma-separated list of permitted pages containing Schema.org `Event` JSON-LD. Never commit `.env` or credentials.

### Run

```bash
python -m bot.main
```

On startup, the application initializes SQLite, performs one collection run, starts scheduled collection and daily notifications, and begins Telegram polling.

### Test

```bash
pytest
```

### Docker

```bash
docker compose up --build
```

Docker Compose loads `.env` and stores SQLite data in the persistent `berlin-radar-data` volume.

## Processing workflow

1. APScheduler triggers collection at the configured interval.
2. Enabled collectors retrieve event data.
3. Events are normalized to the shared model and UTC timestamps.
4. Keyword classification assigns supported professional categories.
5. Events outside the configured city or without a relevant category are discarded.
6. Likely duplicates from the current collection run are merged.
7. Events are inserted or updated in SQLite.
8. Commands filter stored events by date, keyword, price, and preferences.
9. The daily notification job sends up to five unsent events from the next seven days to each subscriber.

A notification is marked as sent only after Telegram accepts it. Explicit command searches may show an event again.

## Security and privacy

- Secrets are loaded from environment variables and excluded from Git and Docker build contexts.
- External requests use HTTPS and a bounded timeout.
- Only Telegram user IDs, preferences, subscription state, and notification history are stored.
- `/subscribe` disables or enables notifications.
- `/delete_me` removes a user's preferences and notification history.
- Source APIs and pages must be used according to their access rules, rate limits, and terms.

## Roadmap

The following are planned, not current capabilities:

- A verified public Berlin-focused event feed that works without organizer credentials.
- Persistent cross-run deduplication with multiple source links.
- Pagination, retries, rate-limit handling, and source scan health tracking.
- Cancellation, postponement, stale-event, and registration-link monitoring.
- Weekly digests and configurable notification times.
- Favorites and calendar export.
- AI classification, semantic search, and personalized ranking.
- Additional cities, languages, and an administration dashboard.
- PostgreSQL support for production-scale deployments.

## Project status

**Prototype / MVP foundation.** Telegram interaction, persistence, filtering, scheduling, notifications, and configurable collectors are implemented and tested. Broad automatic Berlin-wide discovery is not yet available; it depends on adding verified permitted sources.

## License

This repository does not currently include a license. Add a `LICENSE` file before publishing or distributing it under a chosen license.
