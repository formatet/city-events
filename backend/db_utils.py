#!/usr/bin/env python3
"""
Database utilities – connections, event persistence, title normalisation,
category detection, and stale-event cleanup.
"""

import re
import logging
import mysql.connector
from datetime import datetime, timedelta
import os

# Scrapling 0.4.x fires a spurious "deprecated" WARNING on every Fetcher()
# instantiation even when no arguments are passed. Suppress it globally.
logging.getLogger('scrapling').setLevel(logging.ERROR)

class _SkipEvent(Exception):
    pass

# ---------------------------------------------------------------------------
# Title normalisation
# ---------------------------------------------------------------------------
# Goal: fix titles written in ALL CAPS (common on concert sites).
# Leaves titles that are already correctly capitalised untouched.
#
# English titles → Title Case  (function words in lowercase, except first/last)
# Swedish titles  → Sentence case (first letter capitalised, rest lowercase)
#
# Language detection: simple heuristic based on å/ä/ö and common Swedish words.
# ---------------------------------------------------------------------------

# Function words kept lowercase in title case (not first or last word in title)
_EN_FUNCTION_WORDS = {
    'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'so', 'yet',
    'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'if', 'it',
    'vs', 'via', 'from', 'into', 'with', 'than', 'over',
}

_SV_FUNCTION_WORDS = {
    'en', 'ett', 'och', 'med', 'på', 'av', 'för', 'till', 'från', 'som',
    'i', 'om', 'men', 'eller', 'ur', 'vid', 'mot', 'hos', 'under', 'över',
    'efter', 'bland', 'utan', 'den', 'det', 'de', 'är', 'att', 'ha',
}

# English indicators – clear English words that determine language classification
_EN_INDICATORS = {
    'the', 'and', 'with', 'from', 'this', 'that', 'are', 'was', 'were',
    'you', 'your', 'our', 'their', 'its', 'my', 'his', 'her',
    'have', 'has', 'not', 'all', 'been', 'will', 'can', 'more',
}

# Swedish words/characters for language detection
_SV_INDICATORS = {
    'och', 'med', 'för', 'på', 'av', 'är', 'till', 'från', 'som', 'men',
    'eller', 'efter', 'under', 'över', 'om', 'mot', 'att', 'ett',
}

# Short function words (≤3 chars) to normalise to lowercase despite the length
# threshold in _normalize_inline_caps.
_NORMALIZE_SHORT = {'TO', 'FÖR'}

# Abbreviations and acronyms that must always be preserved in all-caps,
# even when they appear in a title being normalised from ALL CAPS.
_PRESERVE_CAPS = {
    'IFK',   # IFK Göteborg and other sports clubs
    'GAIS',  # Gothenburg football club
    'ABF',   # Swedish workers' education association
    'RFSL',  # Swedish LGBTQ rights federation
    'HBTQ',  # identity term
    'HBTQI', # identity term
    'LGBT',  # identity term
    'LGBTQ', # identity term
    'KMFDM', # industrial band – always all-caps
    'ABBA',  # always all-caps
    'DJ',    # common music title prefix
    'MC',    # common music title prefix
}


def _is_allcaps(title):
    """True if the title is written entirely in ALL CAPS.
    Single-word titles are normalised only if the word is ≥4 chars (avoids DJ, MC, OK).
    """
    words = [w for w in re.split(r'[\s/&+]+', title) if re.search(r'[A-Za-zÅÄÖåäö]', w)]
    if not words:
        return False
    alpha_words = [w for w in words if re.match(r'^[A-Za-zÅÄÖåäö]+$', w)]
    if not alpha_words:
        return False
    if len(alpha_words) == 1 and len(alpha_words[0]) < 4:
        return False
    return all(w == w.upper() for w in alpha_words)


def _is_alllower(title):
    """True if the title is written entirely in all-lowercase (≥2 alpha words).
    Catches Squarespace/CSS sites that store titles lowercase in HTML.
    """
    words = [w for w in re.split(r'[\s/&+]+', title) if re.search(r'[A-Za-zÅÄÖåäö]', w)]
    if len(words) < 2:
        return False
    alpha_words = [w for w in words if re.match(r'^[A-Za-zÅÄÖåäö]+$', w)]
    if len(alpha_words) < 2:
        return False
    return all(w == w.lower() for w in alpha_words)


def _is_swedish(title):
    """
    Simple heuristic. Defaults to Swedish (we are a Gothenburg calendar)
    if no clear English indicators are found.
    """
    lower = title.lower()
    if any(c in lower for c in 'åäö'):
        return True
    words = set(re.split(r'\W+', lower))
    if words & _SV_INDICATORS:
        return True
    # Not Swedish if English indicators are present
    return not bool(words & _EN_INDICATORS)


def _title_case(title, function_words):
    """
    Title case: capitalise all words except function_words
    (never the first or last word – those are always capitalised).
    Words in _PRESERVE_CAPS are always kept in all-caps.
    """
    words = title.lower().split()
    if not words:
        return title
    result = []
    for i, word in enumerate(words):
        if word.upper() in _PRESERVE_CAPS:
            result.append(word.upper())
        elif i == 0 or i == len(words) - 1 or word not in function_words:
            result.append(word.capitalize())
        else:
            result.append(word)
    return ' '.join(result)


def _normalize_inline_caps(title):
    """Converts embedded ALL CAPS words (≥4 letters) to Title Case.
    Used when the title is otherwise correctly capitalised but contains all-caps words,
    e.g. 'Releasegig – support WYCKED ANGEL' → '... Wycked Angel'.
    Words in _PRESERVE_CAPS (ABBA, GAIS, …) are kept in all-caps.
    Words of 3 chars or fewer are normally not matched (ABF, DJ etc. remain untouched),
    but words in _NORMALIZE_SHORT (TO, FÖR) are always lowercased.
    """
    def _fix(m):
        w = m.group(0)
        return w if w in _PRESERVE_CAPS else w.capitalize()
    result = re.sub(r'\b[A-ZÅÄÖ]{4,}\b', _fix, title)
    if _NORMALIZE_SHORT:
        pat = r'\b(' + '|'.join(re.escape(w) for w in _NORMALIZE_SHORT) + r')\b'
        result = re.sub(pat, lambda m: m.group(0).lower(), result)
    return result


def normalize_title(title):
    """
    Normalises titles written in ALL CAPS or all-lowercase.
    Leaves correctly capitalised titles untouched.

    English titles → Title Case  (non-function words capitalised)
    Swedish titles  → Swedish Title Case (same principle, Swedish function words)
    Mixed titles → inline ALL-CAPS sequences (2+ words of ≥4 letters) are normalised.

    Called automatically by save_events() for all events.
    """
    if not title:
        return title
    if _is_allcaps(title) or _is_alllower(title):
        function_words = _SV_FUNCTION_WORDS if _is_swedish(title) else _EN_FUNCTION_WORDS
        return _title_case(title, function_words)
    return _normalize_inline_caps(title)

# Database connection – read from env or use defaults
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'cityevents'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'cityevents_db'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

from config import CATEGORY_KEYWORDS, VENUE_DEFAULTS

# Title prefixes that are always filtered out – school performances from the City of Gothenburg
_SKIP_TITLE_PREFIXES = ('Skolkonsert', 'Skolvisning', 'Skolteater', 'Kubo')

# Title substrings that are always filtered out – not cultural events
_SKIP_TITLE_SUBSTRINGS = ('vinprovning', 'ölprovning')

# Stats and start time for the current scraper run (read by scrape_all.py after each scraper)
_run_stats = {}
_run_start_time = None

def reset_run_stats():
    """Reset stats and set start time before a new scraper. Called by scrape_all.py."""
    global _run_stats, _run_start_time
    _run_stats = {}
    _run_start_time = datetime.now()

def get_run_stats():
    """Return stats from the last save_events() run."""
    return dict(_run_stats)


_CHURCH_PATTERNS = ('kyrka', 'kapell', 'domkyrka', 'katedral', 'församling')


def get_venue_default(venue):
    """
    Return venue-based default category.
    Explicit VENUE_DEFAULTS lookup first; then pattern-match for churches.
    """
    cat = VENUE_DEFAULTS.get(venue)
    if cat:
        return cat
    v = venue.lower()
    if any(p in v for p in _CHURCH_PATTERNS):
        return 'Klassisk'
    return 'Övrigt'


def determine_category(venue, title, description=''):
    """
    Determine category for an event.

    Priority:
      1. Keyword match in title+description (first match wins, ordered by specificity)
      2. Scraper-supplied category (handled by caller)
      3. Venue default (get_venue_default)

    Returns the keyword-matched category, or the venue default if no keyword matched.
    Callers that have a scraper-supplied category should prefer it over venue default
    when no keyword match occurs.
    """
    # Strip venue name from description to prevent spurious matches
    # (e.g. "house" in "Contrast Public House" description text)
    clean_desc = description.replace(venue, '') if description else ''
    text = (title + ' ' + clean_desc).lower()

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            kw = keyword.strip()
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return cat

    return get_venue_default(venue)


def get_db_connection():
    """Create database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None

def save_events(events, source='unknown'):
    """
    Save events to the database.

    Args:
        events: List of event dictionaries
        source: Name of the scraper source

    Returns:
        Number of saved events
    """
    global _run_stats
    _run_stats = {
        'source': source,
        'found': len(events),
        'saved': 0,
        'skipped_cancelled': 0,
        'skipped_soldout': 0,
        'skipped_booked': 0,
        'deleted': 0,
    }

    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()

        # INSERT/UPDATE query with ON DUPLICATE KEY UPDATE
        # Respect manual=TRUE events (do not overwrite them)
        insert_query = """
            INSERT INTO events (title, date, venue, category, link, source, description, manual)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
                title = IF(manual = FALSE, VALUES(title), title),
                category = IF(manual = FALSE, VALUES(category), category),
                link = IF(manual = FALSE, VALUES(link), link),
                description = IF(manual = FALSE, VALUES(description), description),
                source = IF(manual = FALSE, VALUES(source), source),
                updated_at = CURRENT_TIMESTAMP
        """

        # Fetch all manual events (venue, date) for deduplication
        cursor.execute("""
            SELECT venue, date FROM events
            WHERE manual = TRUE AND date >= NOW() - INTERVAL 1 DAY
        """)
        manual_slots = [(r[0], r[1]) for r in cursor.fetchall()]

        saved = 0
        for event in events:
            try:
                # Skip cancelled and sold-out events (case-insensitive)
                title = event.get('title', '').lower()
                description = event.get('description', '').lower()
                combined = f"{title} {description}"

                if 'inställt' in combined or 'inställd' in combined:
                    print(f"⏭️  Skippar inställt event: {event.get('title')}")
                    _run_stats['skipped_cancelled'] += 1
                    continue

                if 'slutsålt' in combined or 'slutsåld' in combined:
                    print(f"⏭️  Skippar slutsålt event: {event.get('title')}")
                    _run_stats['skipped_soldout'] += 1
                    continue

                if 'abonnerad' in combined or 'abbonerad' in combined:
                    print(f"⏭️  Skippar abonnerat event: {event.get('title')}")
                    _run_stats['skipped_booked'] += 1
                    continue

                if 'fullbokat' in combined:
                    print(f"⏭️  Skippar fullbokat event: {event.get('title')}")
                    _run_stats['skipped_cancelled'] += 1
                    continue

                raw_title = event.get('title', '')
                # Rätta all-gemener-titlar (sajten publicerade i lowercase)
                if raw_title and raw_title == raw_title.lower() and any(c.isalpha() for c in raw_title):
                    raw_title = raw_title.title()
                if any(raw_title.startswith(p) for p in _SKIP_TITLE_PREFIXES):
                    print(f"⏭️  Skippar skolföreställning: {raw_title}")
                    _run_stats['skipped_cancelled'] += 1
                    continue
                if any(s in raw_title.lower() for s in _SKIP_TITLE_SUBSTRINGS):
                    print(f"⏭️  Skippar icke-kulturhändelse: {raw_title}")
                    _run_stats['skipped_cancelled'] += 1
                    continue

                # Skip scraped events that match a manual event (same venue, date ±60 min)
                try:
                    from datetime import datetime as _dt
                    ev_date = event['date']
                    if isinstance(ev_date, str):
                        ev_date = _dt.strptime(ev_date[:19], '%Y-%m-%d %H:%M:%S')
                    ev_venue = event.get('venue', '')
                    for m_venue, m_date in manual_slots:
                        if m_venue == ev_venue and abs((ev_date - m_date).total_seconds()) <= 3600:
                            print(f"⏭️  Skippar (manuell finns): {event.get('title')}")
                            _run_stats['skipped_cancelled'] += 1
                            raise _SkipEvent()
                except _SkipEvent:
                    continue

                # Normalise ALL CAPS titles
                clean_title = normalize_title(event['title'])

                # Category priority:
                #  1. Keyword match (always wins – specific beats generic)
                #  2. Scraper-supplied category (scraper knows its source)
                #  3. Venue default (including church pattern matching)
                venue_default = get_venue_default(event['venue'])
                clean_desc    = event.get('description', '')

                # Check keywords only (no venue fallback)
                text = (clean_title + ' ' + clean_desc.replace(event['venue'], '')).lower()
                keyword_cat = None
                for cat, keywords in CATEGORY_KEYWORDS.items():
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw.strip()) + r'\b', text):
                            keyword_cat = cat
                            break
                    if keyword_cat:
                        break

                if keyword_cat:
                    category = keyword_cat
                elif event.get('category') and event['category'] not in ('Övrigt',):
                    category = event['category']
                else:
                    category = venue_default

                cursor.execute(insert_query, (
                    clean_title,
                    event['date'],
                    event['venue'],
                    category,
                    event.get('link', ''),
                    source,
                    event.get('description', '')
                ))
                saved += 1
            except Exception as e:
                print(f"⚠️  Fel vid sparande av '{event.get('title', 'Unknown')}': {e}")
                continue

        conn.commit()
        _run_stats['saved'] = saved

        # Cleanup: delete events from this source that were not updated during this run.
        # Uses the run's actual start time (set by reset_run_stats) as cutoff
        # so that slow runs (>20 min) are handled correctly.
        # Truncate to whole second – DB's TIMESTAMP has second precision while
        # Python datetime has microseconds. Without truncation, events inserted
        # in the same second as _run_start_time may be erroneously deleted
        # (e.g. fast scrapers like Monument031 that take <1s).
        raw_cutoff = _run_start_time if _run_start_time else datetime.now() - timedelta(minutes=20)
        cutoff = raw_cutoff.replace(microsecond=0)
        cleanup_query = """
            DELETE FROM events
            WHERE source = %s
            AND manual = FALSE
            AND updated_at < %s
        """
        cursor.execute(cleanup_query, (source, cutoff))
        deleted = cursor.rowcount
        _run_stats['deleted'] = deleted

        if deleted > 0:
            print(f"🧹 Raderade {deleted} gamla events från {source}")

        conn.commit()
        cursor.close()
        conn.close()

        return saved

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        if conn:
            conn.close()
        return 0

def cleanup_old_events(days=30):
    """
    Delete events older than X days.

    Args:
        days: Number of days to retain
    """
    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()
        query = "DELETE FROM events WHERE date < DATE_SUB(NOW(), INTERVAL %s DAY)"
        cursor.execute(query, (days,))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return deleted

    except mysql.connector.Error as err:
        print(f"❌ Cleanup error: {err}")
        if conn:
            conn.close()
        return 0


def cleanup_past_manual_events():
    """Delete manually created events whose time has passed (2h grace period)."""
    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM events WHERE manual = TRUE AND date < NOW() - INTERVAL 2 HOUR"
        )
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return deleted

    except mysql.connector.Error as err:
        print(f"❌ Cleanup manual error: {err}")
        if conn:
            conn.close()
        return 0

def get_event_stats():
    """Fetch event statistics from the database."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)

        stats = {}

        # Total count
        cursor.execute("SELECT COUNT(*) as total FROM events")
        stats['total'] = cursor.fetchone()['total']

        # Count by venue
        cursor.execute("""
            SELECT venue, COUNT(*) as count
            FROM events
            WHERE date >= CURDATE()
            GROUP BY venue
            ORDER BY count DESC
        """)
        stats['by_venue'] = cursor.fetchall()

        # Count by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM events
            WHERE date >= CURDATE()
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['by_category'] = cursor.fetchall()

        # Upcoming events
        cursor.execute("SELECT COUNT(*) as upcoming FROM events WHERE date >= NOW()")
        stats['upcoming'] = cursor.fetchone()['upcoming']

        cursor.close()
        conn.close()

        return stats

    except mysql.connector.Error as err:
        print(f"❌ Stats error: {err}")
        if conn:
            conn.close()
        return None
