#!/usr/bin/env python3
"""
Example scraper – JSON API (second most common pattern).

Use this when the venue's website loads events via a JavaScript widget
or internal API that returns JSON. You can find the API endpoint by
opening DevTools → Network → filter by Fetch/XHR, then reload the page.
"""

import sys
import os
import json
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

# ── Configuration – change these for your venue ───────────────────────────────
VENUE      = 'Example Venue'
SOURCE     = 'Example Venue'
EVENTS_URL = 'https://example.com/api/events.json'
# ──────────────────────────────────────────────────────────────────────────────


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; city-events/1.0)'},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def scrape():
    events = []
    now    = datetime.now()
    today  = now.strftime('%Y-%m-%d')

    print(f'📡 Hämtar {VENUE} via JSON API...')
    try:
        data = fetch_json(EVENTS_URL)
    except Exception as e:
        print(f'❌ API-anrop misslyckades: {e}')
        return events

    # Adjust the path into the JSON structure for your API.
    # Common patterns: data itself is a list, or data['events'], data['data'] etc.
    raw = data if isinstance(data, list) else data.get('events', [])
    print(f'✅ {len(raw)} events i API-svaret')

    for item in raw:
        try:
            # Adjust field names to match your API response
            date_str = item.get('date', '')      # e.g. "2026-05-15"
            time_str = item.get('time', '')      # e.g. "19:30" or "19:30:00"
            title    = item.get('title', '').strip()

            if not date_str or not time_str or not title:
                continue
            if date_str < today:
                continue

            # Normalise time to HH:MM
            time_str = time_str[:5]

            try:
                dt = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            except ValueError:
                print(f'  ⚠️  Kunde inte parsa datum: {date_str} {time_str}')
                continue

            if dt < now:
                continue

            link = item.get('url') or item.get('link') or ''

            events.append({
                'title':       title,
                'date':        dt.strftime('%Y-%m-%d %H:%M:%S'),
                'venue':       VENUE,
                'link':        link,
                'description': item.get('description', '')[:500],
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
        return 2


if __name__ == '__main__':
    sys.exit(main())
