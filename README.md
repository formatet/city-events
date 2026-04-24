# Kristall

A self-hosted cultural event calendar. Scrapers pull events from local venues every night and store them in MariaDB. A minimal Flask API serves a single-page frontend.

Live at [kristall.info](https://kristall.info) — Gothenburg, Sweden.

## How it works

```
57 scrapers → MariaDB → Flask API → single-page frontend
```

Scrapers run nightly at 03:00. Each scraper handles one venue and calls `save_events()` in `db_utils.py`, which normalizes titles, determines categories, deduplicates, and cleans up stale events.

The frontend is a plain HTML/CSS/JS table — no framework, no build step.

## Stack

- **Scrapers:** Python, [Scrapling](https://github.com/D4Vinci/Scrapling)
- **Database:** MariaDB
- **API:** Flask
- **Frontend:** Vanilla JS/HTML/CSS
- **Infrastructure:** Three LXC containers on Proxmox (DB, scraper, web)

## Cloning for your city

The core is generic. The only city-specific file is `backend/config.py`, which maps venue names to categories. Everything else — the database schema, API, frontend, scraper pattern — works as-is.

What you need to do:

1. Write scrapers for your local venues (see `backend/scrapers/` for examples)
2. Replace the venue mappings in `backend/config.py`
3. Update the city name and URLs in `web/static/`

The scraper pattern is simple: fetch events, return a list of dicts, call `save_events()`. Category detection, title normalization, deduplication and cleanup are handled automatically.

## Data

Upcoming events are available as:
- [`/static/events.json`](https://kristall.info/static/events.json)
- [`/static/events.csv`](https://kristall.info/static/events.csv)

Updated nightly. Licensed CC-BY 4.0.

## Contact

[hej@kristall.info](mailto:hej@kristall.info)

## License

MIT
