#!/usr/bin/env python3
"""
Example scraper – listing page + detail pages.

Use this when the listing page shows event titles and links but not
the full date/time. Each event's detail page must be visited to get
the exact time.

This pattern is slower (one HTTP request per event) so it includes
a short pause between requests to be a polite crawler.
"""

import sys
import os
import re
import time
from datetime import datetime
from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

# ── Configuration – change these for your venue ───────────────────────────────
VENUE       = 'Example Venue'
SOURCE      = 'Example Venue'
LISTING_URL = 'https://example.com/program/'
BASE_URL    = 'https://example.com'
PAUSE_S     = 0.5   # seconds between detail page requests
# ──────────────────────────────────────────────────────────────────────────────

SWEDISH_MONTHS = {
    'januari': 1, 'februari': 2, 'mars': 3, 'april': 4,
    'maj': 5, 'juni': 6, 'juli': 7, 'augusti': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'december': 12,
}


def collect_links(fetcher):
    """Return a set of event detail page URLs from the listing page."""
    links = set()
    try:
        page = fetcher.get(LISTING_URL, timeout=15)
    except Exception as e:
        print(f'❌ Kunde inte hämta listsida: {e}')
        return links

    # Adjust selector to match links to event detail pages
    for a in page.css('a.event-link, a[href*="/event/"]'):
        href = str(a.attrib.get('href', ''))
        if not href:
            continue
        if not href.startswith('http'):
            href = BASE_URL + href
        links.add(href)

    return links


def scrape_detail(fetcher, url):
    """
    Fetch one detail page and return an event dict, or None if it can't be parsed.
    Returning None causes the event to be skipped entirely – we never save
    events without a confirmed date and time.
    """
    try:
        page = fetcher.get(url, timeout=15)
    except Exception as e:
        print(f'  ❌ Kunde inte hämta {url}: {e}')
        return None

    # Title
    title_el = page.css_first('h1')
    if not title_el:
        return None
    title = str(title_el.text).strip()

    page_text = page.body.text if page.body else ''

    # Date – adjust regex to match the format on your venue's detail pages
    # This example parses "Lördag 18 april 2026" + "kl. 19:30"
    date_match = re.search(
        r'(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|'
        r'september|oktober|november|december)\s+(\d{4})',
        page_text, re.IGNORECASE
    )
    time_match = re.search(r'kl\.?\s*(\d{1,2})[\.:](\d{2})', page_text)

    if not date_match or not time_match:
        print(f'  ⚠️  Kunde inte parsa datum/tid från {url}')
        return None   # skip – never save with a fallback time

    day   = int(date_match.group(1))
    month = SWEDISH_MONTHS.get(date_match.group(2).lower())
    year  = int(date_match.group(3))
    hour  = int(time_match.group(1))
    minute = int(time_match.group(2))

    if not month:
        return None

    try:
        dt = datetime(year, month, day, hour, minute)
    except ValueError:
        return None

    return {
        'title': title,
        'date':  dt.strftime('%Y-%m-%d %H:%M:%S'),
        'venue': VENUE,
        'link':  url,
        'description': '',
    }


def scrape():
    events = []
    now    = datetime.now()
    seen   = set()
    fetcher = Fetcher()

    print(f'📡 Hämtar evenemangslista från {VENUE}...')
    links = collect_links(fetcher)
    print(f'✅ Hittade {len(links)} event-länkar')

    for url in sorted(links):
        print(f'  📄 Hämtar: {url}')
        result = scrape_detail(fetcher, url)
        time.sleep(PAUSE_S)

        if not result:
            continue

        try:
            dt = datetime.strptime(result['date'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue

        if dt < now:
            continue

        key = (result['title'], result['date'])
        if key in seen:
            continue
        seen.add(key)

        events.append(result)
        print(f'  ✅ {result["title"]} – {result["date"][:16]}')

    return events


def main():
    print(f'🎵 Startar {VENUE}-scraper...')
    events = scrape()
    if events:
        saved = save_events(events, source=SOURCE)
        print(f'💾 Sparade {saved} events till databasen')
        return 0
    else:
        print('⚠️  Inga events hittades')
        return 1


if __name__ == '__main__':
    sys.exit(main())
