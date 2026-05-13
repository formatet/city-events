#!/usr/bin/env python3
"""
Scraper för BK Häcken – hemmamatcher
Hämtar kommande hemmamatcher från https://bkhacken.se/api/matches/coming/1/20

Strategi:
  Häcken exponerar ett JSON-API. pivot.side="home" → hemmamatch på Bravida Arena.
  Tid i UTC (Z) → konvertera till lokal tid (+1/+2 beroende på sommar/vintertid).
"""

import sys
import os
from datetime import datetime, timezone, timedelta
import urllib.request
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

API_URL = 'https://bkhacken.se/api/matches/coming/1/20'
VENUE   = 'Bravida Arena'


def fetch_matches():
    req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def to_local(utc_str):
    """'2026-05-10T13:00:00.000000Z' → lokal datetime"""
    dt = datetime.strptime(utc_str[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    # Sverige är UTC+1 (vinter) eller UTC+2 (sommar)
    # Enkel approximation: +2 april-oktober, +1 resten
    offset = 2 if 4 <= dt.month <= 10 else 1
    return dt + timedelta(hours=offset)


def scrape():
    events = []
    print('📡 Hämtar BK Häcken matcher...')
    matches = fetch_matches()
    print(f'✅ Hittade {len(matches)} matcher totalt')

    for m in matches:
        if m.get('pivot', {}).get('side') != 'home':
            continue

        home_list = m.get('home_team', [])
        away_list = m.get('away_team', [])
        if not home_list or not away_list:
            continue

        home = home_list[0].get('name', '').strip()
        away = away_list[0].get('name', '').strip()
        if not home or not away:
            continue

        dt = to_local(m['time'])
        if dt < datetime.now(timezone.utc) + timedelta(hours=1):
            continue

        slug = m.get('slug', '')
        link = f'https://www.bkhacken.se/matcher/{slug}' if slug else 'https://www.bkhacken.se/matcher/'
        ticket = m.get('ticket_url') or m.get('ticket_link') or link

        title = f'{home} – {away}'
        events.append({
            'title':    title,
            'date':     dt.strftime('%Y-%m-%d %H:%M:%S'),
            'venue':    VENUE,
            'link':     ticket,
            'category': 'Fotboll',
            'description': 'Allsvenskan – hemmamatch',
        })
        print(f'  ✅ {title} – {dt.strftime("%Y-%m-%d %H:%M")}')

    return events


def main():
    print('⚽ Startar BK Häcken-scraper...')
    events = scrape()
    if events:
        saved = save_events(events, source='BK Häcken')
        print(f'💾 Sparade {saved} events')
        return 0
    print('⚠️  Inga hemmamatcher')
    return 1


if __name__ == '__main__':
    sys.exit(main())
