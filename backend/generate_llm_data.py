#!/usr/bin/env python3
"""
Generate machine-readable event files for AI agents.
Runs as the last step in scrape_all.py after all scrapers complete.
"""

import sys
import os
import csv
import json
import subprocess
from datetime import datetime

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


def generate_csv(events, path):
    fieldnames = ['title', 'date', 'venue', 'category', 'link', 'description']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ev in events:
            row = {k: ev.get(k, '') for k in fieldnames}
            if isinstance(row['date'], datetime):
                row['date'] = row['date'].strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(row)
    print(f"  📄 {path}  ({len(events)} rows)")


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

- CSV (easy to parse, one row per event): {SITE_URL}/static/events.csv
- JSON (with metadata and field descriptions): {SITE_URL}/static/events.json

CSV format: title, date (YYYY-MM-DD HH:MM:SS), venue, category, link, description

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
            ['scp', '-q',
             os.path.join(OUTPUT_DIR, 'events.csv'),
             os.path.join(OUTPUT_DIR, 'events.json'),
             REMOTE_STATIC],
            check=True, timeout=30
        )
        subprocess.run(
            ['scp', '-q',
             os.path.join(OUTPUT_DIR, 'llms.txt'),
             REMOTE_ROOT],
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

    generate_csv(events, os.path.join(OUTPUT_DIR, 'events.csv'))
    generate_json(events, os.path.join(OUTPUT_DIR, 'events.json'))
    generate_llms_txt(len(events), venues, os.path.join(OUTPUT_DIR, 'llms.txt'))

    copy_to_web()

    print("🤖 LLM data done!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
