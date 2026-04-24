# Setup Guide – forking city-events for your city

This guide covers everything you need to adapt and deploy city-events for a new city,
in the order you should do it.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | 3.11 recommended |
| MariaDB 10.6+ (or MySQL 8+) | on a separate host or localhost |
| Linux with systemd | for nightly scraping |
| A reverse proxy | Caddy or nginx in front of gunicorn |
| SSH access to your server(s) | for deploy scripts |

Install Python dependencies:
```bash
pip install -r backend/requirements.txt   # scraper host
pip install -r web/requirements.txt       # web host
```

---

## Architecture

Three roles – can run on one machine or separate hosts. The reference setup uses
**Debian LXC containers on Proxmox**, one container per role:

```
Internet
    │
    ▼
Cloudflare Tunnel (cloudflared LXC)
    │  encrypted tunnel, no open inbound ports on your network
    ▼
Caddy (reverse proxy LXC)
    │  TLS termination, basic auth on /admin
    ▼
Flask / gunicorn (web LXC)          ◄──── MariaDB (db LXC)
    │                                          ▲
    │                               ┌──────────┘
    └───── scrape_all.py (backend LXC) writes nightly
```

The backend writes to the database nightly. The web server reads from it on every request.
Both connect to the database using the same `DB_*` environment variables.

**Important:** the Flask app runs on port 5000 via gunicorn and must sit behind a reverse
proxy (Caddy or nginx) to be reachable on port 80/443. The app itself has no TLS and no
authentication. `/admin` and all `/api/admin/*` routes are unprotected at the Flask level –
the reverse proxy is the only gate.

If you use Cloudflare Tunnel (recommended), no ports need to be open on your server at all.

Example minimal Caddyfile:
```
your-domain.example {
    reverse_proxy localhost:5000

    basicauth /admin* {
        # generate hash with: caddy hash-password
        admin $2a$14$your-bcrypt-hash-here
    }
}
```

---

## Step 1 – Database

Create the database and table:
```bash
mysql -u root -p < database/schema.sql
```

Create a dedicated user (edit the commented `CREATE USER` block in `schema.sql` first,
then run just that part):
```sql
CREATE USER 'cityevents'@'localhost' IDENTIFIED BY 'your-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON cityevents_db.* TO 'cityevents'@'localhost';
FLUSH PRIVILEGES;
```

Verify:
```bash
mysql -u cityevents -p cityevents_db -e "DESCRIBE events;"
```

---

## Step 2 – City-specific config

### `backend/config.py`

The only file you truly need to rewrite. Everything else is generic.

Replace `VENUE_DEFAULTS` with your local venues and their default categories:
```python
VENUE_DEFAULTS = {
    'My Concert Hall': 'Musik',
    'City Theatre':    'Teater',
    'Local Cinema':    'Film',
}
```

Replace `CATEGORY_KEYWORDS` if your city's events use different terminology.
Priority order matters – first match wins.

The category names themselves (Film, Teater, Musik…) appear verbatim in the UI –
rename them in `config.py` and they'll update everywhere automatically.

### Language and locale

The frontend is written in Swedish. If you're deploying for a non-Swedish city,
search `web/static/js/` for these strings and translate them:

- `format.js`: `"Idag"`, `"Ikväll"`, `"Imorgon"`, `"På"`, `"sv-SE"` (locale for date formatting)
- `render.js`: `"När"`, `"Vad"`, `"Var"`, `"Konstform"` / `"Konst"` (table column headers)
- `app.js`: the error message shown when events fail to load
- `filters.js`: `"Alla datum"` is already removed, but check for any remaining Swedish strings
- `web/static/om.html`: rewrite entirely

### `web/static/js/theme.js` – coordinates for day/night theme

The site switches between day/dusk/night themes based on actual sunrise/sunset.
Set your city's coordinates:

```js
const lat = 57.7089; // ← your city's latitude
const lon = 11.9746; // ← your city's longitude
```

| City | lat | lon |
|---|---|---|
| Gothenburg, SE | 57.7089 | 11.9746 |
| Stockholm, SE | 59.3293 | 18.0686 |
| London, UK | 51.5074 | -0.1278 |
| Berlin, DE | 52.5200 | 13.4050 |
| New York, US | 40.7128 | -74.0060 |

### `web/static/index.html` and `web/static/om.html`

Replace all instances of "Kristall" and "Göteborg" with your site name and city.
`om.html` is the about page – rewrite it entirely for your city.
`admin.html` has a Swedish title tag – update it too.

### Branding – icon and logo

The crystal icon (SVG path in `web/static/js/render.js`) is used as the site's
interactive element – it appears next to each event as a link, glows on featured events,
and doubles as the filter indicator in the column headers.

You're welcome to replace it with any SVG shape that fits your city's identity.
The relevant constants are `KRISTALL_PATH` and `KRISTALL_OUTER` at the top of `render.js`.

That said – you're very welcome to keep the crystal as a small homage to where this
project started. It looks good and it's free to use.

Replace the static icon files with your own branding:
```
web/static/favicon.ico
web/static/favicon.svg
web/static/apple-touch-icon.png
web/static/icon-192.png
web/static/icon-512.png
web/static/icon.svg
```

### `web/static/robots.txt`, `sitemap.xml`, `manifest.json`

Replace `your-domain.example` with your actual domain in all three files.

---

## Step 3 – Environment variables

All sensitive config is read from environment variables. The cleanest way to set them
is in the systemd service file:

```ini
# In city-events-scrape.service:
[Service]
Environment="DB_HOST=10.0.0.5"
Environment="DB_USER=cityevents"
Environment="DB_PASSWORD=your-password"
Environment="DB_NAME=cityevents_db"
Environment="NTFY_TOPIC=my-alerts"
Environment="HEALTHCHECKS_URL=https://hc-ping.com/your-uuid"
```

```ini
# In city-events-api.service:
[Service]
Environment="DB_HOST=10.0.0.5"
Environment="DB_USER=cityevents"
Environment="DB_PASSWORD=your-password"
Environment="DB_NAME=cityevents_db"
```

Full variable reference:

| Variable | Description | Required |
|---|---|---|
| `DB_HOST` | Database hostname | Yes |
| `DB_USER` | Database username | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_NAME` | Database name | Yes |
| `NTFY_TOPIC` | ntfy.sh topic for scraper notifications | No |
| `HEALTHCHECKS_URL` | healthchecks.io ping URL (dead man's switch) | No |
| `SITE_URL` | Public URL of your site | No |
| `SITE_NAME` | Site name in generated data files | No |
| `SITE_CONTACT` | Contact email in generated data files | No |
| `CITY_NAME` | City name in generated data files | No |
| `LLM_OUTPUT_DIR` | Output path for events.csv / events.json / llms.txt | No |
| `REMOTE_STATIC` | SCP destination for static data files | No |
| `REMOTE_ROOT` | SCP destination for llms.txt | No |

---

## Step 4 – Write your first scraper

See `SCRAPER_GUIDE.md` for a full walkthrough. The short version:

```bash
cp backend/scrapers/scrape_example_html_db.py backend/scrapers/scrape_myvenue_db.py
# edit VENUE, SOURCE, EVENTS_URL, and the parsing logic
python backend/scrapers/scrape_myvenue_db.py
```

**Critical rules:**

- `source` in `save_events(events, source=SOURCE)` must equal the venue name in `VENUE_DEFAULTS`.
  The stale-cleanup that removes old events from the database is keyed on this value –
  a mismatch means old events are never deleted.

- Never save an event without a confirmed time. If the time cannot be parsed, skip the event
  entirely (`return None`). Events with a fallback time of 00:00 look broken in the UI.

- Always wrap Scrapling return values with `str()` before passing to the database.
  `.get()` and `.getall()` return `TextHandler` objects, not plain strings.
  The MySQL driver will reject them silently or raise an error.

- The UNIQUE KEY is `(title, date, venue)`. Two events with the same title, date, and venue
  will upsert to a single row. If a scraper changes a venue's name, old rows with the
  previous name will pile up until the stale-cleanup removes them.

---

## Step 5 – Local development

Test scrapers and the Flask app without deploying:

```bash
# Run a scraper locally (needs DB_* env vars pointing to your database)
cd backend
DB_HOST=localhost DB_USER=cityevents DB_PASSWORD=secret python scrapers/scrape_myvenue_db.py

# Run the Flask app locally
cd web
DB_HOST=localhost DB_USER=cityevents DB_PASSWORD=secret python app.py
# → http://localhost:5000
```

---

## Step 6 – Deploy

```bash
# Backend (scrapers + systemd timer)
cd backend
BACKEND_HOST=user@your-server BACKEND_DIR=/opt/city-events ./deploy-backend.sh

# Web server (Flask + gunicorn + systemd service)
cd web
WEB_HOST=user@your-server WEB_DIR=/var/www/city-events ./deploy-web.sh
```

Check it's running:
```bash
ssh user@your-server "systemctl status city-events-api"
ssh user@your-server "systemctl list-timers city-events-scrape.timer"
```

---

## Step 7 – Run scrapers for the first time

```bash
ssh user@your-backend-server \
  "cd /opt/city-events && source venv/bin/activate && python scrape_all.py"
```

Watch the output. Each scraper logs how many events it found and saved.
Check the database:
```bash
mysql -u cityevents -p cityevents_db -e \
  "SELECT venue, COUNT(*) as n FROM events GROUP BY venue ORDER BY n DESC LIMIT 20;"
```

---

## Features to know about

### Admin interface (`/admin`)

A simple admin page for adding manual events that scrapers will never overwrite.
Flask has no authentication on `/admin` or `/api/admin/*` – **you must protect these
routes in your reverse proxy** (see Caddyfile example in the Architecture section).

Manual events are automatically deleted 2 hours after their start time.

### Machine-readable data (`/static/events.json`, `/static/events.csv`)

Generated nightly by `generate_llm_data.py`. Set `REMOTE_STATIC` and `REMOTE_ROOT`
environment variables so the backend copies the files to the web server after each run.

### Analytics

`web/static/js/kt.js` is a thin wrapper around Umami's `window.umami.track()`.
The script tag in `index.html` is commented out – replace it with your own Umami
instance before deploying:

```html
<script defer src="https://your-umami-host/script.js" data-website-id="your-website-id"></script>
```

**Setting up Umami** (self-hosted, recommended):

1. Deploy [Umami](https://umami.is) on a subdomain (e.g. `stats.your-domain.example`).
   The official Docker image is the fastest way to get started.
2. Add your site in the Umami dashboard → get a `website-id` UUID.
3. Add the script tag to `index.html` and `om.html`.
4. Tracked events: `data_load_error` (when events fail to load). Add more calls to
   `trackEvent()` in `app.js` as needed.

If you don't want analytics at all, just leave the script tag commented out and
ignore `kt.js` – it does nothing without Umami present.

### Crystal colours and featured events

Each night `scrape_all.py` randomly picks one event per calendar day (up to 24 days
ahead) and marks it `featured=1`. Featured events get a coloured crystal icon in the UI.

Manual events can have a custom `crystal_color` (hex, e.g. `#bef2ff`) set via `/admin`.
They can also have a `highlight` style: `leftborder` (gold left border) or `background`
(warm tint) to visually distinguish them from scraped events.

### Pride mode

A toggle at `POST /api/admin/pride` switches the UI into pastel pride colours.
The state is stored in a plain text file on the server (`pride_state.txt`).
The current mode is exposed at `GET /api/pride` and read by the frontend on load.

### Title normalisation

`db_utils.py` automatically converts ALL-CAPS titles (common on concert sites) to
Title Case or Sentence case. Add abbreviations that must stay in all-caps to
`_PRESERVE_CAPS` in `db_utils.py` (e.g. local sports club acronyms).

---

## Updating after initial deploy

After changing a scraper or fixing a bug, redeploy only the changed file:

```bash
# Update a single scraper
scp backend/scrapers/scrape_myvenue_db.py user@backend-server:/opt/city-events/scrapers/

# Update db_utils.py or config.py
scp backend/db_utils.py backend/config.py user@backend-server:/opt/city-events/

# Update the Flask app (requires restart)
scp web/app.py user@web-server:/var/www/city-events/app.py
ssh user@web-server "systemctl restart city-events-api"

# Update static files (no restart needed)
rsync -avz web/static/ user@web-server:/var/www/city-events/static/
```

Check the scraper logs:
```bash
ssh user@backend-server "tail -f /opt/city-events/logs/scrape_stdout.log"
```

Check the health endpoint:
```
GET /health  →  {"status": "healthy", "database": "connected"}
```

---

## Troubleshooting

**Scraper saves 0 events**
- Check that the website structure hasn't changed (CSS selectors go stale)
- Try `StealthyFetcher()` if the site blocks plain requests
- Confirm `source=SOURCE` matches the key in `VENUE_DEFAULTS`

**Events appear with time 00:00**
- The scraper is not finding the time. Add a guard: if time cannot be parsed, `return None`.

**Old events not being deleted**
- The `source` parameter in `save_events()` must exactly match what was used when
  the events were inserted. A name change leaves orphaned rows until they age out.

**Flask app can't connect to database**
- Verify `DB_*` env vars are set in the systemd service file and that `systemctl daemon-reload`
  was run after editing it.

**Database UNIQUE constraint errors**
- Two scrapers are inserting the same (title, date, venue). Check that venue names are
  consistent across scrapers and that no two scrapers cover the same venue.
