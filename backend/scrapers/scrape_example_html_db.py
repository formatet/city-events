#!/usr/bin/env python3
"""
Example scraper – static HTML with Scrapling (most common pattern).

This covers venues where all events are listed on a single page
with title, date and link visible in the HTML source.

Scrapling is the standard fetching library for this project.
Use it instead of requests+BeautifulSoup for all new scrapers.
"""

import sys
import os
import re
from datetime import datetime
from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

# ── Configuration – change these for your venue ───────────────────────────────
VENUE      = 'Example Venue'
SOURCE     = 'Example Venue'
EVENTS_URL = 'https://example.com/events/'
# ──────────────────────────────────────────────────────────────────────────────

SWEDISH_MONTHS = {
    'januari': 1, 'februari': 2, 'mars': 3, 'april': 4,
    'maj': 5, 'juni': 6, 'juli': 7, 'augusti': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12,
}


def scrape():
    events = []
    now    = datetime.now()
    fetcher = Fetcher()

    print(f'📡 Hämtar {VENUE}...')
    try:
        page = fetcher.get(EVENTS_URL, timeout=15)
    except Exception as e:
        print(f'❌ Kunde inte hämta sidan: {e}')
        return events

    # Adjust the CSS selector to match your venue's event cards.
    # Common patterns: 'article.event', 'li.event-item', 'div.programme-item'
    cards = page.css('article.event')
    print(f'✅ Hittade {len(cards)} event-kort')

    for card in cards:
        try:
            # Title – adjust selector as needed
            title_el = card.css_first('h2.event-title')
            if not title_el:
                continue
            title = str(title_el.text).strip()
            if not title:
                continue

            # Link
            link_el = card.css_first('a')
            link = str(link_el.attrib.get('href', '')) if link_el else ''
            if link and not link.startswith('http'):
                link = 'https://example.com' + link

            # Date – adjust to match the format on your venue's page.
            # This example parses "Fredag 18 april 19:30"
            date_el = card.css_first('time, .event-date, .date')
            if not date_el:
                continue
            date_text = str(date_el.text).strip().lower()

            match = re.search(
                r'(\d{1,2})\s+(\w+)\s+(\d{1,2})[\.:](\d{2})',
                date_text
            )
            if not match:
                print(f'  ⚠️  Kunde inte parsa datum: {date_text!r}')
                continue

            day    = int(match.group(1))
            month  = SWEDISH_MONTHS.get(match.group(2))
            hour   = int(match.group(3))
            minute = int(match.group(4))

            if not month:
                continue

            # Infer year: if the date has already passed this year, use next year
            year = now.year
            try:
                dt = datetime(year, month, day, hour, minute)
            except ValueError:
                continue
            if dt < now:
                dt = dt.replace(year=year + 1)
            if dt < now:
                continue

            events.append({
                'title':       title,
                'date':        dt.strftime('%Y-%m-%d %H:%M:%S'),
                'venue':       VENUE,
                'link':        link,
                'description': '',
            })
            print(f'  ✅ {title} – {dt.strftime("%Y-%m-%d %H:%M")}')

        except Exception as e:
            print(f'  ⚠️  Fel: {e}')
            continue

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
