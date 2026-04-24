#!/usr/bin/env python3
"""
Flask API – serves city events from MariaDB.
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, resources={r"/api/events": {"origins": "*"}, r"/data/*": {"origins": "*"}})

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response

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
        return jsonify(events)
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
    return send_from_directory('/var/www/city-events', 'llms.txt', mimetype='text/plain; charset=utf-8')

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
    return send_from_directory('/var/www/city-events/static', 'events.json', mimetype='application/json')

@app.route('/static/events.csv')
def events_csv_static():
    return send_from_directory('/var/www/city-events/static', 'events.csv', mimetype='text/csv')

PRIDE_FILE = '/var/www/city-events/pride_state.txt'
LLMS_LOG   = '/var/www/city-events/llms_access.log'

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


@app.route('/health')
def health():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"})
    return jsonify({"status": "unhealthy", "database": "disconnected"}), 500

@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
