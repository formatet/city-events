#!/usr/bin/env python3
"""
Import events.json into the database.
Used for test data and initial population.
"""

import json
import mysql.connector
from datetime import datetime
import os
import sys

DB_CONFIG = {
    'host':     os.getenv('DB_HOST',     'localhost'),
    'user':     os.getenv('DB_USER',     'cityevents'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME',     'cityevents_db'),
}

def import_events(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Accept both a plain list and the wrapped {events: [...]} format
    events = data if isinstance(data, list) else data.get('events', [])
    print(f"📖 Reading {len(events)} events from {json_file}")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # WARNING: clears the table before importing – remove in production
        cursor.execute("DELETE FROM events")
        print("🗑️  Cleared existing events")

        insert_query = """
            INSERT INTO events (title, date, venue, category, link, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        imported = 0
        for event in events:
            try:
                event_date = datetime.fromisoformat(str(event['date']).replace('Z', '+00:00'))
                cursor.execute(insert_query, (
                    event['title'],
                    event_date,
                    event['venue'],
                    event.get('category', 'Övrigt'),
                    event.get('link', ''),
                    'import',
                ))
                imported += 1
            except Exception as e:
                print(f"❌ Error importing '{event.get('title', 'Unknown')}': {e}")
                continue

        conn.commit()
        print(f"✅ Imported {imported}/{len(events)} events")

        cursor.execute("SELECT COUNT(*) FROM events")
        print(f"📊 Total {cursor.fetchone()[0]} events in database")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 import_events.py <events.json>")
        sys.exit(1)
    import_events(sys.argv[1])
