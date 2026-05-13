#!/usr/bin/env python3
"""
Kristall scraper orchestrator – runs all scrapers and logs results.
"""

import sys
import os
import io
import contextlib
import logging
import importlib.util
from datetime import datetime
from pathlib import Path
import traceback
import time
import urllib.request
import urllib.parse
import json as _json
import db_utils as _db_utils
from db_utils import cleanup_old_events, cleanup_past_manual_events, get_event_stats

# Scrapling 0.4.x emits a WARNING on every Fetcher() instantiation due to
# an internal library bug (the warning is unconditional in __init__ and configure()
# does not accept the arguments the warning suggests). This filter suppresses only
# that specific message so that INFO logs (fetched URLs) remain visible as usual.
class _ScraplingDeprecationFilter(logging.Filter):
    def filter(self, record):
        return 'deprecated now' not in record.getMessage()

logging.getLogger('scrapling').addFilter(_ScraplingDeprecationFilter())

# Directories
SCRIPT_DIR = Path(__file__).parent
SCRAPERS_DIR = SCRIPT_DIR / 'scrapers'
LOGS_DIR = SCRIPT_DIR / 'logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Pause between scrapers (seconds)
SCRAPER_PAUSE = 10

NTFY_TOPIC = os.getenv('NTFY_TOPIC', '')

def send_ntfy(title, message, priority='default'):
    try:
        req = urllib.request.Request(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            data=message.encode('utf-8'),
            headers={'Title': urllib.parse.quote(title), 'Priority': priority},
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"  📱 ntfy skickat: {title}")
    except Exception as e:
        print(f"  ⚠️  ntfy misslyckades: {e}")

def fetch_llms_stats():
    try:
        resp = urllib.request.urlopen('http://localhost:5000/api/llms-stats', timeout=5)
        return _json.loads(resp.read())
    except Exception:
        return None

def load_scraper(scraper_file):
    """Dynamically load a scraper module."""
    spec = importlib.util.spec_from_file_location("scraper", scraper_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_scraper(scraper_path):
    """
    Run a single scraper. On real failure (exit 1 or exception), one retry after 60s.
    Exit code 2 means "no events found" – treated as a warning, no retry.

    Returns:
        (success, empty, scraper_stats, error_msg, captured_output)
        empty: True if scraper ran OK but found 0 events (exit code 2)
        captured_output: stdout from the scraper (used to enrich FAILED log entries)
    """
    scraper_name = scraper_path.stem

    for attempt in range(2):
        captured = io.StringIO()
        try:
            if attempt == 0:
                print(f"\n🔍 Kör {scraper_name}...")
            else:
                print(f"\n🔄 Omförsök {scraper_name} (väntar 60s)...")
                time.sleep(60)

            module = load_scraper(scraper_path)

            if not hasattr(module, 'main'):
                return (False, False, {}, "No main() function found", "")

            _db_utils.reset_run_stats()
            with contextlib.redirect_stdout(captured):
                result = module.main()
            output = captured.getvalue()
            print(output, end='')  # echo to terminal/log as before
            stats = _db_utils.get_run_stats()

            if result == 0:
                if attempt > 0:
                    print(f"  ✅ Lyckades vid omförsök")
                return (True, False, stats, None, output)
            elif result == 2:
                # Scraper ran fine but venue has no events – no retry
                return (True, True, stats, None, output)
            else:
                error_msg = f"Exit code {result}"
                if attempt == 0:
                    print(f"  ⚠️  Misslyckat ({error_msg}), försöker om 60s...")
                    continue
                return (False, False, stats, error_msg, output)

        except Exception as e:
            tb = traceback.format_exc()
            output = captured.getvalue()
            print(output, end='')
            print(tb)
            error_msg = f"{type(e).__name__}: {str(e)}\n{tb}"
            if attempt == 0:
                print(f"  ⚠️  Fel: {type(e).__name__}: {e}, försöker om 60s...")
                continue
            return (False, False, {}, error_msg, output)

    return (False, False, {}, "Misslyckades efter omförsök", "")

def main():
    """Main orchestrator function."""
    start_time = datetime.now()
    log_file = LOGS_DIR / f"scrape_{start_time.strftime('%Y%m%d_%H%M%S')}.log"

    print(f"🚀 Kristall Scraper Orchestra")
    print(f"📅 {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 Logg: {log_file}")
    print("=" * 60)

    # Find all scrapers
    scrapers = sorted(SCRAPERS_DIR.glob('scrape_*_db.py'))

    if not scrapers:
        print("⚠️  Inga scrapers hittades i scrapers/")
        return 1

    print(f"📂 Hittade {len(scrapers)} scrapers")

    # Run scrapers
    results = []
    for i, scraper in enumerate(scrapers):
        scraper_start = datetime.now()
        success, empty, stats, error, output = run_scraper(scraper)
        scraper_duration = (datetime.now() - scraper_start).total_seconds()

        results.append({
            'name': scraper.stem,
            'success': success,
            'empty': empty,
            'stats': stats,
            'error': error,
            'output': output,
            'duration': scraper_duration,
            'timestamp': scraper_start
        })

        # Pause between scrapers (except after the last one)
        if i < len(scrapers) - 1:
            print(f"⏸️  Pausar {SCRAPER_PAUSE}s innan nästa scraper...")
            time.sleep(SCRAPER_PAUSE)

    # Clean up old events
    print("\n🧹 Rensar gamla events...")
    deleted = cleanup_old_events(days=30)
    print(f"🗑️  Raderade {deleted} gamla events")
    deleted_manual = cleanup_past_manual_events()
    if deleted_manual:
        print(f"🗑️  Raderade {deleted_manual} passerade manuella events")

    # Statistics
    print("\n📊 Statistik:")
    db_stats = get_event_stats()
    if db_stats:
        print(f"   Totalt events: {db_stats['total']}")
        print(f"   Kommande events: {db_stats['upcoming']}")
        print(f"\n   Per kategori:")
        for cat in db_stats['by_category'][:5]:
            print(f"      {cat['category']}: {cat['count']}")

    # Per-scraper report
    print(f"\n   Per scraper:")
    for r in results:
        s = r['stats']
        if not s:
            if r['empty']:
                status = "⬜ TOM"
            elif not r['success']:
                status = "❌ FEL"
            else:
                status = "✅"
            print(f"      {r['name']}: {status}")
            continue
        parts = [f"hittade {s.get('found', '?')}",
                 f"sparade {s.get('saved', '?')}"]
        if s.get('skipped_cancelled'):
            parts.append(f"{s['skipped_cancelled']} inställda")
        if s.get('skipped_soldout'):
            parts.append(f"{s['skipped_soldout']} slutsålda")
        if s.get('skipped_booked'):
            parts.append(f"{s['skipped_booked']} abonnerade")
        if s.get('deleted'):
            parts.append(f"raderade {s['deleted']} gamla")
        if r['empty']:
            status = "⬜"
        elif r['success']:
            status = "✅"
        else:
            status = "❌"
        print(f"      {status} {r['name']}: {', '.join(parts)}")

    # Summary
    print("\n" + "=" * 60)
    print("📋 Sammanfattning:")

    successful = sum(1 for r in results if r['success'] and not r['empty'])
    empty_count = sum(1 for r in results if r['empty'])
    failed = sum(1 for r in results if not r['success'])

    print(f"   ✅ Lyckade: {successful}/{len(results)}")
    if empty_count:
        empty_names = [r['name'].replace('scrape_', '').replace('_db', '') for r in results if r['empty']]
        print(f"   ⬜ Tomma:    {empty_count}/{len(results)}  ({', '.join(empty_names)})")
    print(f"   ❌ Misslyckade: {failed}/{len(results)}")

    if failed > 0:
        print("\n⚠️  Misslyckade scrapers:")
        for r in results:
            if not r['success']:
                print(f"   - {r['name']}: {r['error']}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️  Total tid: {duration:.1f}s")

    # Write to log
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Kristall Scrape Run\n")
        f.write(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for r in results:
            if r['empty']:
                status = "EMPTY"
            elif r['success']:
                status = "SUCCESS"
            else:
                status = "FAILED"
            timestamp = r['timestamp'].strftime('%H:%M:%S')
            s = r['stats']

            f.write(f"[{timestamp}] {status} - {r['name']} ({r['duration']:.1f}s)\n")
            if s and not r['empty']:
                skips = []
                if s.get('skipped_cancelled'):
                    skips.append(f"{s['skipped_cancelled']} inställda")
                if s.get('skipped_soldout'):
                    skips.append(f"{s['skipped_soldout']} slutsålda")
                if s.get('skipped_booked'):
                    skips.append(f"{s['skipped_booked']} abonnerade")
                skip_str = f"  (exkluderade: {', '.join(skips)})" if skips else ""
                f.write(f"           Hittade: {s.get('found','?')}  "
                        f"Sparade: {s.get('saved','?')}  "
                        f"Raderade gamla: {s.get('deleted', 0)}"
                        f"{skip_str}\n")
            if r['empty']:
                f.write(f"           Inga events på sajten\n")
            elif r['error']:
                f.write(f"           Fel: {r['error']}\n")
                # Include last lines of scraper output to aid debugging
                last_lines = [l for l in r.get('output', '').splitlines() if l.strip()][-6:]
                for line in last_lines:
                    f.write(f"           > {line}\n")
            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"\nDatabase Stats:\n")
        if db_stats:
            f.write(f"  Total events: {db_stats['total']}\n")
            f.write(f"  Upcoming events: {db_stats['upcoming']}\n")
            f.write(f"\n  By category:\n")
            for cat in db_stats['by_category']:
                f.write(f"    {cat['category']}: {cat['count']}\n")

        f.write(f"\nCompleted: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total duration: {end_time - start_time}\n")
        f.write(f"Successful: {successful}/{len(results)}\n")
        f.write(f"Empty:      {empty_count}/{len(results)}\n")
        f.write(f"Failed:     {failed}/{len(results)}\n")

    print(f"✅ Logg sparad: {log_file}")

    # Write per-source run stats as JSON (read by web server health endpoint)
    import json as _json
    source_stats = {}
    for r in results:
        s = r.get('stats') or {}
        src = s.get('source') or r['name']
        source_stats[src] = {
            'found':    s.get('found', 0),
            'saved':    s.get('saved', 0),
            'deleted':  s.get('deleted', 0),
            'excluded': (s.get('skipped_cancelled', 0)
                         + s.get('skipped_soldout', 0)
                         + s.get('skipped_booked', 0)),
            'excl_cancelled': s.get('skipped_cancelled', 0),
            'excl_soldout':   s.get('skipped_soldout', 0),
            'excl_booked':    s.get('skipped_booked', 0),
            'status': 'empty' if r['empty'] else ('success' if r['success'] else 'failed'),
        }
    stats_path = SCRIPT_DIR / 'scrape_stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        _json.dump({'run_at': end_time.isoformat(), 'sources': source_stats}, f,
                   ensure_ascii=False, indent=2)
    print(f"📊 Körningsstatistik sparad: {stats_path}")

    # Rotate logs – keep only the 30 most recent
    all_logs = sorted(LOGS_DIR.glob('scrape_*.log'), key=lambda f: f.stat().st_mtime, reverse=True)
    for old_log in all_logs[30:]:
        old_log.unlink()
        print(f"🗑️  Roterade bort: {old_log.name}")

    # Pick one random featured event per calendar day
    print("\n⭐ Väljer featured events (ett per dag)...")
    try:
        conn = _db_utils.get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("UPDATE events SET featured = FALSE")
            cur.execute("""
                UPDATE events e
                JOIN (
                    SELECT id
                    FROM (
                        SELECT id, DATE(date) AS day,
                               ROW_NUMBER() OVER (PARTITION BY DATE(date) ORDER BY RAND()) AS rn
                        FROM events
                        WHERE date >= NOW()
                          AND date < NOW() + INTERVAL 24 DAY
                          AND manual = FALSE
                    ) ranked
                    WHERE rn = 1
                ) chosen ON e.id = chosen.id
                SET e.featured = TRUE
            """)
            conn.commit()
            count = cur.rowcount
            cur.close()
            conn.close()
            print(f"  ✅ {count} dagar fick ett featured event")
    except Exception as e:
        print(f"  ⚠️  Featured-val misslyckades: {e}")

    # Generate LLM data (CSV, JSON, llms.txt)
    print("\n" + "=" * 60)
    print("🤖 Genererar LLM-data...")
    print("=" * 60)
    import subprocess as _sp
    _sp.run([sys.executable, str(SCRIPT_DIR / 'generate_llm_data.py')])

    # Send ntfy notification
    print("\n📱 Skickar notis...")
    llms = fetch_llms_stats()
    date_str = end_time.strftime('%Y-%m-%d %H:%M')
    upcoming = db_stats['upcoming'] if db_stats else '?'

    empty_names = [r['name'].replace('scrape_', '').replace('_db', '') for r in results if r['empty']]
    failed_names = [r['name'].replace('scrape_', '').replace('_db', '') for r in results if not r['success']]

    if failed == 0:
        title = f"✅ Kristall {date_str}"
        lines = [f"{successful}/{len(results)} scrapers OK · {upcoming} kommande events"]
        priority = 'default'
    else:
        title = f"⚠️ Kristall {date_str} – {failed} fel"
        lines = [
            f"{successful}/{len(results)} OK · {upcoming} kommande events",
            f"Fel: {', '.join(failed_names)}",
        ]
        priority = 'high'

    if empty_names:
        lines.append(f"Tom (inga events): {', '.join(empty_names)}")

    if llms is not None:
        lines.append(f"llms.txt: {llms['last_24h']} anrop senaste dygnet ({llms['total']} totalt)")

    send_ntfy(title, '\n'.join(lines), priority)

    # Exit 0 if ≥90% non-empty scrapers succeeded.
    # Empty scrapers (exit 2) are not counted as failures.
    non_empty = len(results) - empty_count
    failure_rate = failed / non_empty if non_empty else 0
    return 0 if failure_rate < 0.1 else 1

if __name__ == '__main__':
    sys.exit(main())
