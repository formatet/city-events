#!/usr/bin/env python3
"""
Flask API – serves city events from MariaDB.
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import os
import time
import urllib.request
import urllib.parse
import smtplib
from email.mime.text import MIMEText
import logging

app = Flask(__name__, static_folder='static', static_url_path='')

_APP_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'submissions.log')
_sub_logger = logging.getLogger('submissions')
_sub_logger.setLevel(logging.INFO)
if not _sub_logger.handlers:
    _fh = logging.FileHandler(_APP_LOG_FILE, encoding='utf-8')
    _fh.setFormatter(logging.Formatter('%(asctime)s\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    _sub_logger.addHandler(_fh)
CORS(app, resources={r"/api/events": {"origins": "*"}, r"/data/*": {"origins": "*"}})

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response

_events_cache = {"data": None, "ts": 0.0}
CACHE_TTL = 300  # 5 minuter – events ändras bara en gång per natt

NTFY_TOPIC = os.getenv('NTFY_TOPIC', '')
_report_error_ts = 0.0
REPORT_COOLDOWN = 300

DB_CONFIG = {
    'host':     os.getenv('DB_HOST',     'localhost'),
    'user':     os.getenv('DB_USER',     'cityevents'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME',     'cityevents_db'),
    'charset':  'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def fmt_events(events):
    for event in events:
        if isinstance(event['date'], datetime):
            event['date'] = event['date'].isoformat()
    return events

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/data/events.json')
@app.route('/api/events')
def get_events():
    now = time.time()
    if _events_cache["data"] is not None and now - _events_cache["ts"] < CACHE_TTL:
        resp = jsonify(_events_cache["data"])
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, date, venue, category, link, featured, highlight, crystal_color
            FROM events
            WHERE date >= NOW()
            ORDER BY date ASC
        """)
        events = fmt_events(cursor.fetchall())
        cursor.close()
        conn.close()
        _events_cache["data"] = events
        _events_cache["ts"] = now
        resp = jsonify(events)
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp
    except mysql.connector.Error as err:
        print(f"Database query error: {err}")
        return jsonify({"error": "Database query failed"}), 500

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route('/om')
def om():
    return send_from_directory('static', 'om.html')

@app.route('/llms.txt')
def llms_txt():
    try:
        ua = request.headers.get('User-Agent', 'unknown')
        with open(LLMS_LOG, 'a') as f:
            f.write(f"{datetime.utcnow().isoformat()}|{ua}\n")
    except Exception:
        pass
    return send_from_directory(_APP_DIR, 'llms.txt', mimetype='text/plain; charset=utf-8')

@app.route('/api/llms-stats')
def llms_stats():
    try:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        total = 0
        last_24h = 0
        agents = {}
        with open(LLMS_LOG) as f:
            for line in f:
                parts = line.strip().split('|', 1)
                if len(parts) != 2:
                    continue
                total += 1
                ua = parts[1]
                try:
                    if datetime.fromisoformat(parts[0]) >= cutoff:
                        last_24h += 1
                except ValueError:
                    pass
                agents[ua] = agents.get(ua, 0) + 1
        return jsonify({'total': total, 'last_24h': last_24h, 'agents': agents})
    except FileNotFoundError:
        return jsonify({'total': 0, 'last_24h': 0, 'agents': {}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/events.json')
def events_json_static():
    return send_from_directory('static', 'events.json', mimetype='application/json')

@app.route('/static/events.md')
def events_md_static():
    return send_from_directory('static', 'events.md', mimetype='text/markdown; charset=utf-8')

_APP_DIR   = os.path.dirname(os.path.abspath(__file__))
PRIDE_FILE = os.path.join(_APP_DIR, 'pride_state.txt')
WOW_FILE   = os.path.join(_APP_DIR, 'wow_state.txt')
LLMS_LOG   = os.path.join(_APP_DIR, 'llms_access.log')

@app.route('/api/pride', methods=['GET'])
def get_pride():
    try:
        with open(PRIDE_FILE) as f:
            mode = f.read().strip()
    except FileNotFoundError:
        mode = 'off'
    if mode not in ('off', 'pastel'):
        mode = 'off'
    return jsonify({'mode': mode})

@app.route('/api/admin/pride', methods=['POST'])
def set_pride():
    data = request.get_json() or {}
    mode = data.get('mode', 'off')
    if mode not in ('off', 'pastel'):
        return jsonify({'error': 'Invalid mode'}), 400
    with open(PRIDE_FILE, 'w') as f:
        f.write(mode)
    return jsonify({'mode': mode})

@app.route('/api/wow', methods=['GET'])
def get_wow():
    try:
        with open(WOW_FILE) as f:
            mode = f.read().strip()
    except FileNotFoundError:
        mode = 'off'
    if mode not in ('off', 'on'):
        mode = 'off'
    return jsonify({'mode': mode})

@app.route('/api/admin/wow', methods=['POST'])
def set_wow():
    data = request.get_json() or {}
    mode = data.get('mode', 'off')
    if mode not in ('off', 'on'):
        return jsonify({'error': 'Invalid mode'}), 400
    with open(WOW_FILE, 'w') as f:
        f.write(mode)
    return jsonify({'mode': mode})


@app.route('/api/report-error', methods=['POST'])
def report_error():
    global _report_error_ts
    if not NTFY_TOPIC:
        return jsonify({'ok': False}), 503
    if time.time() - _report_error_ts < REPORT_COOLDOWN:
        return jsonify({'ok': False, 'reason': 'cooldown'}), 429
    _report_error_ts = time.time()
    try:
        req = urllib.request.Request(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            data='En besökare rapporterade att sidan inte laddades.'.encode('utf-8'),
            headers={
                'Title': urllib.parse.quote('kristall.info – laddningsfel rapporterat'),
                'Priority': 'default',
                'Tags': 'warning',
            },
        )
        urllib.request.urlopen(req, timeout=10)
        return jsonify({'ok': True})
    except Exception as e:
        print(f'ntfy report-error misslyckades: {e}')
        return jsonify({'ok': False}), 500

@app.route('/health')
def health():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"})
    return jsonify({"status": "unhealthy", "database": "disconnected"}), 500

FROM_EMAIL = 'hej@kristall.info'

def send_mail(to, subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = to
    try:
        with smtplib.SMTP('localhost', 25, timeout=10) as smtp:
            smtp.sendmail(FROM_EMAIL, [to], msg.as_string())
        _sub_logger.info(f"EMAIL_SENT\tto={to}\tsubject={subject}")
    except Exception as e:
        _sub_logger.error(f"EMAIL_FAILED\tto={to}\tsubject={subject}\terror={e}")

@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')

@app.route('/anmal')
def anmal_page():
    return send_from_directory('static', 'anmal.html')

@app.route('/api/submit-event', methods=['POST'])
def submit_event():
    try:
        data = request.get_json() or {}
        required = ['title', 'event_date', 'venue', 'category', 'link']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Saknat fält: {field}'}), 400

        try:
            from datetime import date as _date
            event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
            if event_date < _date.today():
                return jsonify({'error': 'Datumet är passerat – ange ett kommande datum.'}), 400
        except ValueError:
            return jsonify({'error': 'Ogiltigt datumformat'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Databasfel'}), 500

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pending_submissions
                (title, event_date, event_time, venue, category, link, description, contact_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'].strip(),
            data['event_date'],
            data.get('event_time') or None,
            data['venue'].strip(),
            data['category'],
            data['link'].strip(),
            data.get('description', '').strip() or None,
            data.get('contact_email', '').strip() or None,
        ))
        conn.commit()
        cursor.close()
        conn.close()

        _sub_logger.info(
            f"SUBMISSION_IN\ttitle={data['title']}\tdate={data['event_date']}\t"
            f"venue={data['venue']}\tcategory={data['category']}\t"
            f"link={data.get('link','')}\temail={data.get('contact_email','')}"
        )

        if NTFY_TOPIC:
            try:
                time_str = f" {data['event_time']}" if data.get('event_time') else ''
                body = f"{data['event_date']}{time_str} · {data['venue']} · {data['category']}\nGranska på /admin"
                req = urllib.request.Request(
                    f'https://ntfy.sh/{NTFY_TOPIC}',
                    data=body.encode('utf-8'),
                    headers={
                        'Title': urllib.parse.quote(f"Ny anmälan: {data['title']}"),
                        'Priority': 'default',
                        'Tags': 'calendar',
                    },
                )
                urllib.request.urlopen(req, timeout=10)
            except Exception:
                pass

        email = data.get('contact_email', '').strip()
        if email:
            time_str = f" kl. {data['event_time']}" if data.get('event_time') else ''
            send_mail(
                email,
                'Din anmälan till kristall.info',
                f"Hej,\n\nTack för att du anmälde \"{data['title']}\" ({data['event_date']}{time_str}, {data['venue']}).\n\nVi granskar anmälan och lägger till eventet i kalendern om det uppfyller kriterierna. Det brukar ta något dygn.\n\nkristall.info"
            )

        return jsonify({'ok': True}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Databasfel'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, event_date, event_time, venue, category,
                   link, description, contact_email, submitted_at
            FROM pending_submissions ORDER BY submitted_at ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        for row in rows:
            if hasattr(row.get('event_date'), 'isoformat'):
                row['event_date'] = row['event_date'].isoformat()
            if row.get('event_time') is not None:
                td = row['event_time']
                total_seconds = int(td.total_seconds()) if hasattr(td, 'total_seconds') else 0
                h, m = divmod(total_seconds // 60, 60)
                row['event_time'] = f"{h:02d}:{m:02d}"
            if hasattr(row.get('submitted_at'), 'isoformat'):
                row['submitted_at'] = row['submitted_at'].isoformat()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/pending/<int:sub_id>/approve', methods=['POST'])
def approve_pending(sub_id):
    try:
        opts = request.get_json() or {}
        highlight = opts.get('highlight') or None
        if highlight not in (None, 'leftborder', 'background'):
            highlight = None
        crystal_color = opts.get('crystal_color') or None
        if crystal_color and (len(crystal_color) != 7 or not crystal_color.startswith('#')):
            crystal_color = None

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Databasfel'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pending_submissions WHERE id = %s", (sub_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close(); conn.close()
            return jsonify({'error': 'Inte hittad'}), 404

        event_date = row['event_date']
        event_time = row['event_time']
        if hasattr(event_time, 'total_seconds'):
            total_seconds = int(event_time.total_seconds())
            h, m = divmod(total_seconds // 60, 60)
            event_time = f"{h:02d}:{m:02d}:00"
        elif event_time:
            event_time = str(event_time)
        else:
            event_time = '00:00:00'

        date_str = f"{event_date} {event_time}"

        # Blockera godkännande om det resulterande datumet är passerat
        try:
            event_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            event_dt = datetime.strptime(str(event_date), '%Y-%m-%d')
        if event_dt < datetime.now():
            cursor.close(); conn.close()
            return jsonify({'error': f'Datumet {date_str} är passerat – eventet kan inte godkännas.'}), 400

        cursor2 = conn.cursor()
        cursor2.execute("""
            INSERT INTO events
                (title, date, venue, category, link, source, description, manual, highlight, crystal_color)
            VALUES (%s, %s, %s, %s, %s, 'Anmälan', %s, TRUE, %s, %s)
            ON DUPLICATE KEY UPDATE manual = TRUE, highlight = VALUES(highlight),
                crystal_color = VALUES(crystal_color), updated_at = CURRENT_TIMESTAMP
        """, (
            row['title'], date_str, row['venue'], row['category'],
            row['link'] or '', row['description'] or '', highlight, crystal_color,
        ))
        cursor2.execute("DELETE FROM pending_submissions WHERE id = %s", (sub_id,))
        conn.commit()
        cursor2.close()
        cursor.close()
        conn.close()

        _sub_logger.info(
            f"APPROVED\tid={sub_id}\ttitle={row['title']}\tdate={event_date}\t"
            f"venue={row['venue']}\thighlight={highlight}\tcrystal={crystal_color}"
        )

        email = (row.get('contact_email') or '').strip()
        if email:
            time_disp = event_time[:5] if event_time != '00:00:00' else ''
            time_str = f" kl. {time_disp}" if time_disp else ''
            send_mail(
                email,
                'Ditt event är nu med i kristall.info-kalendern!',
                f"Hej,\n\nDitt event \"{row['title']}\" ({event_date}{time_str}, {row['venue']}) har granskats och lagts till i kristall.info-kalendern.\n\nSe det på: https://kristall.info\n\nkristall.info"
            )

        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/pending/<int:sub_id>', methods=['DELETE'])
def reject_pending(sub_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Databasfel'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title, contact_email FROM pending_submissions WHERE id = %s", (sub_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close(); conn.close()
            return jsonify({'error': 'Inte hittad'}), 404
        cursor2 = conn.cursor()
        cursor2.execute("DELETE FROM pending_submissions WHERE id = %s", (sub_id,))
        conn.commit()
        cursor2.close()
        cursor.close()
        conn.close()

        _sub_logger.info(f"REJECTED\tid={sub_id}\ttitle={row['title']}")

        email = (row.get('contact_email') or '').strip()
        if email:
            send_mail(
                email,
                'Din anmälan till kristall.info',
                f"Hej,\n\nTack för att du anmälde \"{row['title']}\" till kristall.info.\n\nTyvärr uppfyller eventet inte våra kriterier för kalendern just nu – vi tar bara med publika kulturevenemang i Göteborg stad med en publik evenemangs- eller biljettlänk.\n\nHoppas du hittar något kul på kristall.info!\n\nkristall.info"
            )

        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/log')
def submissions_log():
    try:
        lines = []
        if os.path.exists(_APP_LOG_FILE):
            with open(_APP_LOG_FILE, encoding='utf-8') as f:
                lines = f.readlines()
        last = [l.rstrip() for l in lines[-200:]]
        last.reverse()
        return jsonify({'lines': last})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/add_event', methods=['POST'])
def add_manual_event():
    try:
        data = request.get_json()
        required = ['title', 'date', 'venue', 'category']
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        highlight = data.get('highlight') or None
        if highlight not in (None, 'leftborder', 'background'):
            highlight = None
        crystal_color = data.get('crystal_color') or None
        if crystal_color and (len(crystal_color) != 7 or not crystal_color.startswith('#')):
            crystal_color = None

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (title, date, venue, category, link, source, description, manual, highlight, crystal_color)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
            ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                link = VALUES(link),
                description = VALUES(description),
                source = VALUES(source),
                highlight = VALUES(highlight),
                crystal_color = VALUES(crystal_color),
                manual = TRUE,
                updated_at = CURRENT_TIMESTAMP
        """, (
            data['title'], data['date'], data['venue'], data['category'],
            data.get('link', ''), data.get('source', 'Manual'),
            data.get('description', ''), highlight, crystal_color
        ))
        conn.commit()
        event_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Event sparat!", "id": event_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/events', methods=['GET'])
def get_manual_events():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, date, venue, category, link, source, description, highlight, crystal_color
            FROM events WHERE manual = TRUE ORDER BY date ASC
        """)
        events = fmt_events(cursor.fetchall())
        cursor.close()
        conn.close()
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/events/<int:event_id>', methods=['GET'])
def get_manual_event(event_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, date, venue, category, link, source, description, highlight, crystal_color
            FROM events WHERE id = %s AND manual = TRUE
        """, (event_id,))
        event = cursor.fetchone()
        cursor.close()
        conn.close()
        if not event:
            return jsonify({"error": "Event not found"}), 404
        if isinstance(event['date'], datetime):
            event['date'] = event['date'].isoformat()
        return jsonify(event)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/events/<int:event_id>', methods=['PUT'])
def update_manual_event(event_id):
    try:
        data = request.get_json()
        highlight = data.get('highlight') or None
        if highlight not in (None, 'leftborder', 'background'):
            highlight = None
        crystal_color = data.get('crystal_color') or None
        if crystal_color and (len(crystal_color) != 7 or not crystal_color.startswith('#')):
            crystal_color = None

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE events
            SET title = %s, date = %s, venue = %s, category = %s,
                link = %s, source = %s, description = %s,
                highlight = %s, crystal_color = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND manual = TRUE
        """, (
            data['title'], data['date'], data['venue'], data['category'],
            data.get('link', ''), data.get('source', 'Manual'),
            data.get('description', ''), highlight, crystal_color, event_id
        ))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Event not found or not manual"}), 404
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Event uppdaterat!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/events/<int:event_id>', methods=['DELETE'])
def delete_manual_event(event_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = %s AND manual = TRUE", (event_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Event not found or not manual"}), 404
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Event raderat!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

SCRAPE_STATS_PATH = os.path.join(os.path.dirname(__file__), 'scrape_stats.json')

@app.route('/api/admin/health')
def scraper_health():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                source,
                SUM(CASE WHEN date >= NOW() THEN 1 ELSE 0 END) AS upcoming,
                MAX(updated_at) AS last_updated
            FROM events
            WHERE manual = FALSE
            GROUP BY source
            ORDER BY source
        """)
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM events WHERE date >= NOW()")
        total = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        # Load last scrape run stats (written by scrape_all.py, copied nightly)
        run_stats = {}
        run_at = None
        try:
            import json as _json
            stats_path = os.path.normpath(SCRAPE_STATS_PATH)
            if os.path.exists(stats_path):
                with open(stats_path, encoding='utf-8') as f:
                    data = _json.load(f)
                run_stats = data.get('sources', {})
                run_at = data.get('run_at')
        except Exception:
            pass

        now = datetime.now()
        sources = []
        for row in rows:
            last_updated = row['last_updated']
            hours_ago = (now - last_updated).total_seconds() / 3600 if last_updated else 999
            upcoming = int(row['upcoming'] or 0)

            if upcoming == 0:
                status = 'empty'
            elif hours_ago > 36:
                status = 'stale'
            else:
                status = 'ok'

            src_stats = run_stats.get(row['source'], {})
            entry = {
                'source': row['source'],
                'upcoming': upcoming,
                'last_updated': last_updated.isoformat() if last_updated else None,
                'hours_ago': round(hours_ago, 1),
                'status': status,
            }
            if src_stats:
                entry['found']    = src_stats.get('found', 0)
                entry['saved']    = src_stats.get('saved', 0)
                entry['excluded'] = src_stats.get('excluded', 0)
                entry['excl_detail'] = {
                    'cancelled': src_stats.get('excl_cancelled', 0),
                    'soldout':   src_stats.get('excl_soldout', 0),
                    'booked':    src_stats.get('excl_booked', 0),
                }
            sources.append(entry)

        return jsonify({
            'checked_at': now.isoformat(),
            'run_at': run_at,
            'total_upcoming': int(total),
            'sources': sources,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
