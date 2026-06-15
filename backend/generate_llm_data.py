#!/usr/bin/env python3
"""
Generate machine-readable event files for AI agents.
Runs as the last step in scrape_all.py after all scrapers complete.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from collections import defaultdict

import mysql.connector

# ── Configuration – set via environment variables ─────────────────────────────
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'cityevents')
DB_PASS = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'cityevents_db')

OUTPUT_DIR    = os.getenv('LLM_OUTPUT_DIR', '/opt/city-events/llm_output')
REMOTE_STATIC = os.getenv('REMOTE_STATIC', '')   # e.g. 'user@web-server:/var/www/city-events/static/'
REMOTE_ROOT   = os.getenv('REMOTE_ROOT',   '')   # e.g. 'user@web-server:/var/www/city-events/llms.txt'

# ── Site metadata – update for your deployment ────────────────────────────────
SITE_URL     = os.getenv('SITE_URL',     'https://your-city-events.example')
SITE_NAME    = os.getenv('SITE_NAME',    'City Events')
SITE_CONTACT = os.getenv('SITE_CONTACT', 'hello@your-city-events.example')
CITY_NAME    = os.getenv('CITY_NAME',    'Your City')
# ──────────────────────────────────────────────────────────────────────────────

EVENTS_SQL = """
    SELECT title, date, venue, category, link, description
    FROM events
    WHERE date >= NOW()
    ORDER BY date ASC
"""


def fetch_events():
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        charset='utf8mb4'
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(EVENTS_SQL)
        return cursor.fetchall()
    finally:
        conn.close()


WEEKDAY_SV = {
    0: 'Måndag', 1: 'Tisdag', 2: 'Onsdag', 3: 'Torsdag',
    4: 'Fredag', 5: 'Lördag', 6: 'Söndag',
}
MONTH_SV = {
    1: 'januari', 2: 'februari', 3: 'mars', 4: 'april',
    5: 'maj', 6: 'juni', 7: 'juli', 8: 'augusti',
    9: 'september', 10: 'oktober', 11: 'november', 12: 'december',
}


def generate_markdown(events, path):
    """
    Grupperar events per datum och skriver ett Markdown-dokument.
    Format per event: **Titel** · Plats · HH:MM · Kategori · [→](url)
    """
    by_date = defaultdict(list)
    for ev in events:
        dt = ev['date']
        if isinstance(dt, datetime):
            pass
        else:
            dt = datetime.strptime(str(dt), '%Y-%m-%d %H:%M:%S')
        by_date[dt.date()].append((dt, ev))

    generated = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    lines = [
        f'# {SITE_NAME} – Upcoming Events in {CITY_NAME}',
        '',
        f'Source: {SITE_URL}  ',
        f'Updated: {generated} (daily ~03:00 local time)  ',
        f'License: CC-BY 4.0 – Credit "{SITE_NAME}"  ',
        f'Contact: {SITE_CONTACT}',
        '',
        '---',
        '',
    ]

    for date in sorted(by_date):
        wd = WEEKDAY_SV[date.weekday()]
        mo = MONTH_SV[date.month]
        lines.append(f'## {wd} {date.day} {mo} {date.year}')
        lines.append('')
        for dt, ev in sorted(by_date[date], key=lambda x: x[0]):
            title    = ev.get('title', '').replace('|', '·')
            venue    = ev.get('venue', '').replace('|', '·')
            category = ev.get('category', '')
            link     = ev.get('link', '')
            time_str = dt.strftime('%H:%M')
            desc     = (ev.get('description') or '').strip().replace('\n', ' ')

            line = f'- **{title}** · {venue} · {time_str} · {category}'
            if link:
                line += f' · [→]({link})'
            if desc:
                line += f'  \n  _{desc[:120]}_'
            lines.append(line)
        lines.append('')

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  📄 {path}  ({len(events)} events)")


def generate_json(events, path):
    serializable = []
    for ev in events:
        row = dict(ev)
        if isinstance(row.get('date'), datetime):
            row['date'] = row['date'].strftime('%Y-%m-%dT%H:%M:%S')
        serializable.append(row)

    payload = {
        'meta': {
            'source':           SITE_URL,
            'description':      f'Events in {CITY_NAME}',
            'license':          'CC-BY 4.0 – https://creativecommons.org/licenses/by/4.0/',
            'attribution':      f'Data from {SITE_NAME}',
            'generated':        datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'update_frequency': 'Daily ~03:00 local time',
            'contact':          SITE_CONTACT,
            'fields': {
                'title':       'Event name',
                'date':        'Date and time, ISO 8601',
                'venue':       'Venue name',
                'category':    'Event category',
                'link':        'URL to ticket/info at source',
                'description': 'Short description (may be empty)',
            },
            'known_issues': (
                'Data quality varies between venues. '
                'Times may be missing (shown as 00:00). '
                'Descriptions may be empty. '
                f'Bug reports welcome – see contact above.'
            ),
        },
        'event_count': len(serializable),
        'events': serializable,
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  📄 {path}  ({len(serializable)} events)")


def generate_llms_txt(event_count, venues, path):
    generated = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    venues_list = '\n'.join(f'- {v}' for v in sorted(venues))
    content = f"""\
# {SITE_NAME}
> {SITE_URL}/llms.txt

## What is this?
{SITE_NAME} is an independent event calendar for {CITY_NAME}.
We aggregate performances, concerts, and events from {len(venues)} venues
into a unified, searchable calendar. Data is scraped automatically every night.

Last updated: {generated} (daily ~03:00–04:00 local time)
Currently: {event_count} upcoming events

## Machine-readable data

- Markdown (human- and LLM-readable, events grouped by date): {SITE_URL}/static/events.md
- JSON (with metadata and field descriptions): {SITE_URL}/static/events.json

Markdown format: grouped by date, one event per line:
`**Title** · Venue · HH:MM · Category · [→](url)`

## Venues covered

{venues_list}

## License
CC-BY 4.0 – Free to use, share, and adapt.
Credit "{SITE_NAME}" as the source.
https://creativecommons.org/licenses/by/4.0/

## Data quality
Scraped data – quality varies between venues:
- Times may be missing (shown as 00:00)
- Descriptions may be empty
- Occasional miscategorised events

Bug reports welcome: {SITE_CONTACT}

## For humans
{SITE_URL}
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  📄 {path}")


def copy_to_web():
    if not REMOTE_STATIC or not REMOTE_ROOT:
        print("  ⚠️  REMOTE_STATIC / REMOTE_ROOT not set, skipping scp")
        return
    try:
        subprocess.run(
            ['/usr/bin/scp', '-q',
             os.path.join(OUTPUT_DIR, 'events.md'),
             os.path.join(OUTPUT_DIR, 'events.json'),
             REMOTE_STATIC],
            check=True, timeout=30
        )
        subprocess.run(
            ['/usr/bin/scp', '-q',
             os.path.join(OUTPUT_DIR, 'llms.txt'),
             REMOTE_ROOT],
            check=True, timeout=30
        )
        # Copy scrape run stats for health dashboard (written by scrape_all.py)
        stats_src = os.path.join(os.path.dirname(OUTPUT_DIR), 'scrape_stats.json')
        remote_stats = REMOTE_ROOT.rsplit('/', 1)[0] + '/scrape_stats.json'
        if os.path.exists(stats_src):
            subprocess.run(
                ['/usr/bin/scp', '-q', stats_src, remote_stats],
                check=True, timeout=30
            )
        print("  ✅ Files copied to web server")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  SCP failed: {e}")
    except subprocess.TimeoutExpired:
        print("  ⚠️  SCP timeout")


def main():
    print("🤖 Generating LLM data...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    events = fetch_events()
    if not events:
        print("  ⚠️  No upcoming events in database")
        return 1

    print(f"  📊 {len(events)} upcoming events")

    venues = sorted({ev['venue'] for ev in events if ev.get('venue')})

    generate_markdown(events, os.path.join(OUTPUT_DIR, 'events.md'))
    generate_json(events, os.path.join(OUTPUT_DIR, 'events.json'))
    generate_llms_txt(len(events), venues, os.path.join(OUTPUT_DIR, 'llms.txt'))

    copy_to_web()

    print("🤖 LLM data done!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
