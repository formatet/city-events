#!/usr/bin/env python3
"""
Scraper för Got Event – stora konserter på Scandinavium, Ullevi och Ullevi Plaza
API: POST https://gotevent.se/api/v2/event/GetEventsTeasers

Strategi:
  Hämtar events för arenorna Scandinavium (2063), Ullevi (2035) och Ullevi Plaza (4377).
  Gamla Ullevi (2041) ingår INTE – täcks redan av fotbollsscrapers.

  Datumhantering:
    - Enstaka datum ("fredag 12 juni, 2026, 19:30"): använd eventStartDate direkt
    - Spann ≤ 3 dagar ("28 aug – 29 aug, 2026"): ett event per dag med starttidens tid
    - Spann > 3 dagar ("21 aug – 27 aug, 2026"): turnering/festival → ett event (startdag)
    - Oläsbar dateSpan ("Fotbollssäsongen 2026"): ett event med eventStartDate

  Lägg till i config.py innan aktivering:
    VENUE_DEFAULTS: 'Scandinavium': 'Konsert', 'Ullevi': 'Konsert'
"""

import sys
import os
import re
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

API_URL = 'https://gotevent.se/api/v2/event/GetEventsTeasers'
BASE_URL = 'https://gotevent.se'
ARENA_IDS = [2063, 2035, 4377]  # Scandinavium, Ullevi, Ullevi Plaza
SOURCE = 'Got Event'

SWEDISH_MONTHS = {
    'januari': 1, 'februari': 2, 'mars': 3, 'april': 4,
    'maj': 5, 'juni': 6, 'juli': 7, 'augusti': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'december': 12,
}

_RANGE_RE = re.compile(
    r'(\d{1,2})\s+([a-zåäö]+)\s*[–-]\s*(\d{1,2})\s+([a-zåäö]+),\s*(\d{4})',
    re.IGNORECASE,
)


def _dates_from_span(date_span, start_dt):
    """
    Returnerar lista med datetime för ett event.
    Spann ≤ 3 dagar → ett datum per dag.
    Spann > 3 dagar → bara startdagen.
    Inget spann → [start_dt].
    """
    m = _RANGE_RE.search(date_span)
    if not m:
        return [start_dt]

    month1 = SWEDISH_MONTHS.get(m.group(2).lower())
    month2 = SWEDISH_MONTHS.get(m.group(4).lower())
    if not month1 or not month2:
        return [start_dt]

    year = int(m.group(5))
    try:
        d1 = datetime(year, month1, int(m.group(1)), start_dt.hour, start_dt.minute)
        d2 = datetime(year, month2, int(m.group(3)), start_dt.hour, start_dt.minute)
    except ValueError:
        return [start_dt]

    delta = (d2 - d1).days
    if delta <= 0:
        return [start_dt]
    elif delta <= 3:
        return [d1 + timedelta(days=i) for i in range(delta + 1)]
    else:
        return [d1]


def scrape():
    events = []
    now = datetime.now()

    print('📡 Hämtar Got Event-program...')
    try:
        resp = requests.post(
            API_URL,
            json={'categories': [], 'arenas': ARENA_IDS, 'dates': [], 'searchWord': '', 'skip': 0, 'take': 100},
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'x-language': 'sv'},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f'❌ Nätverksfel: {e}')
        return []

    teasers = data.get('teaserCards', {}).get('$values', [])
    print(f'✅ {len(teasers)} events i API-svaret')

    for teaser in teasers:
        title = teaser.get('title', '').strip()
        if not title:
            continue

        date_span = teaser.get('dateSpan', '')
        # Hoppa över events markerade som flyttade till annan venue
        if 'Flyttad' in date_span or 'Inställd' in date_span or 'Inställt' in date_span:
            print(f'  ⏭️  Hoppar (flytt/inställt): {title}')
            continue

        start_str = teaser.get('eventStartDate', '')
        if not start_str:
            continue
        try:
            start_dt = datetime.strptime(start_str[:19], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            continue

        arena = teaser.get('arena', '')
        venue = 'Ullevi' if 'Ullevi' in arena else arena

        page_url = teaser.get('toPageUrl') or {}
        link = BASE_URL + page_url.get('url', '') if page_url.get('url') else ''

        for dt in _dates_from_span(date_span, start_dt):
            if dt < now:
                continue
            events.append({
                'title': title,
                'date': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'venue': venue,
                'link': link,
                'category': 'Konsert',
            })
            print(f'  ✅ {title} | {venue} | {dt.strftime("%Y-%m-%d %H:%M")}')

    return events


def main():
    print('🎸 Startar Got Event-scraper...')
    events = scrape()
    print(f'✅ Totalt {len(events)} kommande events')
    if events:
        saved = save_events(events, source=SOURCE)
        print(f'💾 Sparade {saved} events till databasen')
        return 0
    print('⚠️  Inga kommande events på Got Event-arenorna')
    return 2


if __name__ == '__main__':
    sys.exit(main())
