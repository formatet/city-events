#!/usr/bin/env python3
"""
Scraper för GBG Fotboll – matcher på utvalda planer i centrala Göteborg
Hämtar via https://www.gbgfotboll.se/api/matches-today/games/?associationId=7&date=YYYY-MM-DD

Strategi:
  API:et returnerar alla Göteborgsförbundets matcher per dag.
  Vi loopar 14 dagar framåt och filtrerar på planer som är relevanta
  ur ett besökarperspektiv (centrala/välkända planer).

  Planer som inkluderas:
    Guldheden (södra / IP / plan)
    Majvallen
    Backavallen
    Gröna vallen
    Generatorsplan
    Heden
    Färjenäsplan
"""

import sys
import os
import re
import json
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

API = 'https://www.gbgfotboll.se/api/matches-today/games/?associationId=7&date={date}'
BASE_URL = 'https://www.gbgfotboll.se'
DAYS_AHEAD = 14

# Planer som är intressanta för en stadsbor (partiell matchning, case-insensitive)
INCLUDED_LOCATIONS = [
    'guldheden',
    'majvallen',
    'backavallen',
    'gröna vallen',
    'generatorsplan',
    'heden',
    'färjenäsplan',
    'gamla ullevi',
    'anders svensson',
]


def is_included(location):
    loc = location.lower()
    return any(p in loc for p in INCLUDED_LOCATIONS)


def fetch_day(date_str):
    url = API.format(date=date_str)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def scrape():
    events = []
    seen = set()
    now = datetime.now()

    for day_offset in range(DAYS_AHEAD):
        date = now + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        data = fetch_day(date_str)

        for competition in data.get('competitions', []):
            comp_name = competition.get('name', '')
            age_cat = competition.get('ageCategoryName', '')
            # Bara Senior och Veteran — Barn/Ungdom skapar för mycket volym
            if age_cat not in ('Senior', 'Veteran'):
                continue
            for game in competition.get('games', []):
                location = game.get('location', '')
                if not is_included(location):
                    continue

                home = game.get('homeTeam', {}).get('name', '').strip()
                away = game.get('awayTeam', {}).get('name', '').strip()
                if not home or not away:
                    continue

                # Filtrera bort turneringsplatshållare
                if 'Fotboll Tillsammans' in (home, away):
                    continue

                dt_str = game.get('date', '')
                # Hoppa matcher utan angiven tid (00:00 = saknar tidsinformation)
                if dt_str[11:16] == '00:00':
                    continue
                try:
                    dt = datetime.strptime(dt_str[:19], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    continue

                if dt < now:
                    continue

                title = f'{home} – {away}'
                key = (title, dt_str[:16])
                if key in seen:
                    continue
                seen.add(key)

                link = BASE_URL + game.get('url', '/tavling2/matcher-idag/')

                clean_loc = (location
                    .replace(' Konstgräs', '').replace(' konstgräs', '')
                    .replace(' K.Gräs', '').replace(' KG', '')
                    .strip())
                clean_loc = re.sub(r'\s+\d+$', '', clean_loc).strip()
                events.append({
                    'title':       title,
                    'date':        dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'venue':       clean_loc,
                    'link':        link,
                    'category':    'Fotboll',
                    'description': comp_name,
                })
                print(f'  ✅ {title} | {clean_loc} | {dt.strftime("%Y-%m-%d %H:%M")}')

    return events


def main():
    print('⚽ Startar GBG Fotboll-scraper (lokala planer)...')
    events = scrape()
    print(f'✅ Hittade {len(events)} matcher på utvalda planer')
    if events:
        saved = save_events(events, source='GBG Fotboll')
        print(f'💾 Sparade {saved} events')
        return 0
    print('⚠️  Inga matcher på utvalda planer de närmaste {DAYS_AHEAD} dagarna')
    return 1


if __name__ == '__main__':
    sys.exit(main())
