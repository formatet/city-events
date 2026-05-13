#!/usr/bin/env python3
"""
Scraper för IFK Göteborg – hemmamatcher
Hämtar kommande hemmamatcher från https://www.ifkgoteborg.se/matcher/

Strategi:
  WordPress-sida som renderar kommande hemmamatcher i navigationsmenyn
  som statisk HTML. Inga hemmamatcher = tomt resultat (normalt).

  Selektorer:
    span.teams  → "IFK Göteborg – Motståndare"
    span.info   → "2 maj 13.00"

  Venue: Gamla Ullevi (samtliga hemmamatcher)
  Kategori: Fotboll (via VENUE_DEFAULTS i config.py)
"""

import sys
import os
import re
from datetime import datetime
from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import save_events

URL = 'https://www.ifkgoteborg.se/matcher/'

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'maj': 5, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12,
}


def parse_date(info_text):
    """Parsar '2 maj 13.00' → datetime"""
    m = re.search(
        r'(\d{1,2})\s+([a-zåäö]+)\s+(\d{1,2})[.:](\d{2})',
        info_text.strip().lower()
    )
    if not m:
        return None
    day, month_str, hour, minute = int(m.group(1)), m.group(2)[:3], int(m.group(3)), int(m.group(4))
    month = MONTHS.get(month_str)
    if not month:
        return None
    now = datetime.now()
    year = now.year if (month, day) >= (now.month, now.day) else now.year + 1
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def scrape():
    events = []
    print('📡 Hämtar IFK Göteborg hemmamatcher...')
    r = Fetcher().get(URL, stealthy_headers=True, timeout=20)

    teams_els = r.css('span.teams')
    info_els = r.css('span.info')
    links_els = r.css('a[href*="ebiljett"]')

    print(f'✅ Hittade {len(teams_els)} matcher')

    seen = set()
    for i, (team_el, info_el) in enumerate(zip(teams_els, info_els)):
        title = team_el.text.strip()
        if not title:
            continue

        dt = parse_date(info_el.text)
        if not dt:
            print(f'  ⚠️  Kunde inte parsa datum: {info_el.text!r}')
            continue

        key = (title, dt)
        if key in seen:
            continue
        seen.add(key)

        link = str(links_els[i].attrib.get('href', URL)) if i < len(links_els) else URL

        events.append({
            'title': title,
            'date': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'venue': 'Gamla Ullevi',
            'link': link,
            'description': 'Allsvenskan – hemmamatch',
            'category': 'Fotboll',
        })
        print(f'  ✅ {title} – {dt.strftime("%Y-%m-%d %H:%M")}')

    return events


def main():
    print('⚽ Startar IFK Göteborg-scraper...')
    events = scrape()
    if events:
        saved = save_events(events, source='IFK Göteborg')
        print(f'💾 Sparade {saved} events till databasen')
        return 0
    print('⚠️  Inga hemmamatcher hittades')
    return 1


if __name__ == '__main__':
    sys.exit(main())
