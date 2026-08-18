# Kristall

A self-hosted cultural event calendar. Scrapers pull events from local venues every night and store them in MariaDB. A minimal Flask API serves a single-page frontend.

Live at [kristall.info](https://kristall.info) — Gothenburg, Sweden.

## How it works

```
57 scrapers → MariaDB → Flask API → single-page frontend
```

Scrapers run nightly at 03:00. Each scraper handles one venue and calls `save_events()` in `db_utils.py`, which normalizes titles, determines categories, deduplicates, and cleans up stale events.

The frontend is a plain HTML/CSS/JS table — no framework, no build step.

## Features

- **Nightly scraping** – 57 scrapers cover theatres, music venues, cinemas, galleries, libraries and more
- **Category detection** – keyword matching + venue defaults, configurable in `config.py`
- **Event submission** – visitors can submit missing events at `/anmal`; submissions go into a moderation queue
- **Admin dashboard** – tab-based UI at `/admin` for managing manual events, reviewing submissions (approve/reject), and monitoring scraper health
- **Email notifications** – confirmation on submit, approval and rejection emails via local Postfix
- **LLM data** – events exposed as `/llms.txt`, `events.json` and `events.csv` for AI assistants and third-party use

## Stack

- **Scrapers:** Python, [Scrapling](https://github.com/D4Vinci/Scrapling)
- **Database:** MariaDB
- **API:** Flask + Gunicorn
- **Frontend:** Vanilla JS/HTML/CSS, [Inter](https://rsms.me/inter/) font
- **Analytics:** [Umami](https://umami.is) (self-hosted, privacy-friendly)
- **Notifications:** [ntfy](https://ntfy.sh)
- **Infrastructure:** Three LXC containers on Proxmox (DB, scraper, web), [Caddy](https://caddyserver.com) reverse proxy

## Cloning for your city

The core is generic. The only city-specific file is `backend/config.py`, which maps venue names to categories. Everything else — the database schema, API, frontend, scraper pattern — works as-is.

What you need to do:

1. Write scrapers for your local venues (see `backend/scrapers/` for examples)
2. Replace the venue mappings in `backend/config.py`
3. Update the city name, URLs and contact details in `web/static/`

The scraper pattern is simple: fetch events, return a list of dicts, call `save_events()`. Category detection, title normalization, deduplication and cleanup are handled automatically.

See `SETUP.md` for full installation instructions and `SCRAPER_GUIDE.md` for writing scrapers.

## Event submission flow

Visitors submit events via `/anmal`. Submissions are stored in `pending_submissions` and trigger an ntfy notification. The admin reviews them at `/admin` (Väntande tab) and approves or rejects with one click. Approved events become `manual=TRUE` entries; both outcomes send an email to the submitter if an address was provided.

## Data

Upcoming events are available as:
- [`/static/events.json`](https://kristall.info/static/events.json)
- [`/static/events.csv`](https://kristall.info/static/events.csv)

Updated nightly. Licensed CC-BY 4.0.

## Contact

[hej@kristall.info](mailto:hej@kristall.info)

## License

MIT
