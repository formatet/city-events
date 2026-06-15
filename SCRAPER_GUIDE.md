# Scraper Guide

This guide is written so that an AI agent (or human) with no prior context can
write, test, and deploy a new scraper from scratch.

---

## System overview

Three containers (adjust to your own infrastructure):

| Container | Role |
|---|---|
| DB | MariaDB – `your_db.events` |
| Backend | Python scrapers |
| Web | Flask API + frontend |

Scrapers run nightly via systemd (configurable). Set `DB_HOST`, `DB_USER`,
`DB_PASSWORD`, and `DB_NAME` as environment variables to match your setup.

---

## File structure

```
backend/
├── scrape_all.py              # Orchestrator – runs all scrapers/scrape_*_db.py
├── db_utils.py                # save_events(), determine_category() – rarely needs changing
├── config.py                  # City-specific config: VENUE_DEFAULTS, CATEGORY_KEYWORDS
├── scrapers/
│   ├── scrape_example_html_db.py        # Template: static HTML (Scrapling)
│   ├── scrape_example_json_db.py        # Template: JSON API
│   ├── scrape_example_detailpages_db.py # Template: listing + detail pages
│   └── scrape_*_db.py                   # One file per venue
```

**Naming convention:** `scrape_<venue_slug>_db.py`  
`scrape_all.py` automatically discovers all files matching `scrapers/scrape_*_db.py`.

---

## Libraries

**Scrapling for HTML scraping** (WordPress, Drupal, Squarespace, Wix, static sites).
All new scrapers that parse HTML should use Scrapling. Older BS4/Selenium scrapers
work but will be rewritten on the next pass.

**stdlib `urllib.request` for pure APIs** (JSON REST, iCal feeds). Scrapling adds
nothing when there is no HTML to parse — use direct HTTP calls instead.

Never use `requests` or `BeautifulSoup` in new scrapers.

```bash
pip install "scrapling[fetchers]"
```

### Choosing a fetcher

| Situation | Fetcher |
|---|---|
| Static HTML (WordPress, Drupal, standard CMS) | `Fetcher()` |
| Site that blocks vanilla requests | `Fetcher()` with `stealthy_headers=True` |
| JS-rendered page (SPA, React, Angular) | `StealthyFetcher()` or `DynamicFetcher()` |

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

fetcher = Fetcher()
page = fetcher.get(url, stealthy_headers=True, timeout=15)
```

### Selectors

```python
# CSS selector – text
page.css('h2.event-title::text').get()       # first match
page.css('h2.event-title::text').getall()    # all matches

# CSS selector – attribute
page.css('a.event-link::attr(href)').get()

# Find element to chain from
card = page.css('div.event-card')[0]
title = card.css('h2::text').get()

# All direct text nodes in an element (important with mixed content)
texts = page.css('div.mixed-content::text').getall()
```

### ⚠️ Important: str() conversion

`.get()` and `.getall()` return `TextHandler` objects, **not** plain strings.
The MySQL driver does not accept TextHandler. Always wrap with `str()`:

```python
title       = str(page.css('h1::text').get()).strip()
hrefs       = [str(h) for h in page.css('a::attr(href)').getall()]
desc_parts  = [str(t) for t in page.css('p::text').getall()]
```

---

## save_events() – the database interface

```python
from db_utils import save_events

events = [
    {
        'title':       'Event name',           # str, required
        'date':        '2026-06-15 20:00:00',  # str 'YYYY-MM-DD HH:MM:SS', required
        'venue':       'Venue name',            # str, required
        'link':        'https://...',           # str, URL to ticket/info page
        'description': 'Short text...',         # str, may be empty
        # 'category': 'Musik',                  # str, OPTIONAL – auto-detected if omitted
    }
]

saved = save_events(events, source='Venue name')
# source should match venue name for stale-cleanup to work correctly
```

`save_events()` automatically:
- Upserts (INSERT OR UPDATE on title + date + venue)
- Skips events with cancellation/sold-out keywords in title or description
- Deletes stale events from the same `source` that were not updated this run
- Determines category via `determine_category()` if `category` is omitted

---

## Category system

Category is determined in two steps in `db_utils.py`:

**Step 1 – Venue default** (hardcoded per venue name in `VENUE_DEFAULTS` in `config.py`).  
**Step 2 – Keyword override** (title + description are searched; first match wins).

Both dicts live in `backend/config.py` – the only file you need to replace when
forking for a new city.

### Adding a new venue

```python
# In config.py – VENUE_DEFAULTS
'My New Venue': 'Musik',
```

### Adding a new keyword rule

```python
# In config.py – CATEGORY_KEYWORDS
'Jazz': ['jazz', 'big band', 'bebop'],
```

---

## Workflow: new scraper from scratch

### 1. Explore the site

Start by understanding the HTML structure:
- Is the page static or JS-rendered? → choose Scrapling fetcher (see table above)
- Where is the event container? (CSS class, data attribute, tag structure)
- What does the date look like? (ISO, Swedish text, 12h/24h, year present or absent)
- Are detail pages needed to get the time? (see `scrape_example_detailpages_db.py`)
- Is there pagination? (`?page=1` or `li.pager__item--next`)

**Quick inspection:**
```python
from scrapling.fetchers import Fetcher
page = Fetcher().get('https://venue.example/events', stealthy_headers=True)
print(page.html_content[:3000])
```

### 2. Copy a template

```bash
cp backend/scrapers/scrape_example_html_db.py backend/scrapers/scrape_<venue>_db.py
```

Fill in `EVENTS_URL`, `VENUE`, `SOURCE` and adapt the parsing logic.

### 3. Test locally

```bash
cd backend
python scrapers/scrape_<venue>_db.py
```

Point `DB_HOST` at your database via environment variable, or edit `DB_CONFIG`
defaults in `db_utils.py` temporarily.

### 4. Deploy to server

```bash
scp backend/scrapers/scrape_<venue>_db.py user@your-backend-server:/opt/city-events/scrapers/
ssh user@your-backend-server "cd /opt/city-events && source venv/bin/activate && python scrapers/scrape_<venue>_db.py"
```

---

## Common date patterns

### ISO date (simplest)

```python
# "2026-07-10"
datetime.strptime(date_iso, '%Y-%m-%d')
```

### ISO date from URL

```python
# URL: /events/2026-04-15/blues-night
m = re.search(r'/(\d{4}-\d{2}-\d{2})/', href)
date_iso = m.group(1)
```

### Swedish text with year

```python
# "15 april 2026" or "15 april 2026, kl: 18:00"
MONTHS = {'januari':1,'februari':2,'mars':3,'april':4,'maj':5,'juni':6,
          'juli':7,'augusti':8,'september':9,'oktober':10,'november':11,'december':12}
m = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4}).*?(\d{1,2}):(\d{2})', text, re.I)
dt = datetime(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)),
              int(m.group(4)), int(m.group(5)))
```

### Date without year (inferred)

```python
# "18 Apr", "15 APRIL | STUDIO 2"
# Infer year: if the month has already passed this year, use next year
year = now.year if month >= now.month else now.year + 1
```

### 12-hour time (am/pm) → 24-hour

```python
# "6:00 pm" → 18:00
m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_raw.lower())
hour = int(m.group(1))
if m.group(3) == 'pm' and hour != 12:
    hour += 12
elif m.group(3) == 'am' and hour == 12:
    hour = 0
```

### Month section with data attribute

```python
# <section data-show-month="06"> ... <div class="item"> ...
for section in page.css('section.show-month'):
    month = int(str(section.css('::attr(data-show-month)').get()))
    for t in [str(x) for x in section.css('strong::text').getall()]:
        m = re.search(r'(20\d{2})', t)
        if m:
            year = int(m.group(1)); break
```

---

## Common pitfalls

**Mixed content in a div**  
`div.coco-card__text` contains `<p>SUPPORT: TBA</p>` followed by a text node
`"1 MAJ | STUDIO 2"`. `.get()` picks the first node (whitespace). Solution:
loop `.getall()` and filter:

```python
date_raw = None
for t in [str(x) for x in card.css('div.coco-card__text::text').getall()]:
    if re.search(r'\d+\s+[A-ZÅÄÖ]{3}', t.strip()):
        date_raw = t.strip()
        break
```

**Wix widgets**  
Title links in Wix are `<a role="button">` without `href`. Use `data-hook`
attributes as selectors – they are semantic and survive Wix redesigns:

```python
title = item.css('[data-hook="ev-list-item-title"]::text').get()
date  = item.css('[data-hook="date"]::text').get()
link  = item.css('[data-hook="ev-rsvp-button"]::attr(href)').get()
```

**TextHandler in MySQL**  
See section above. All values passed to `save_events()` must be `str`.

**Past events**  
Always filter out events that have already started:
```python
if dt < datetime.now():
    continue
```

**Relative URLs**
```python
if href.startswith('/'):
    href = BASE_URL + href
```

---

## Scrapling: escalating fetcher levels

```python
# Level 1 – standard (most static sites)
from scrapling.fetchers import Fetcher
page = Fetcher().get(url, stealthy_headers=True, timeout=15)

# Level 2 – stealth (curl_cffi, mimics Chrome at HTTP/2 level)
from scrapling.fetchers import StealthyFetcher
page = StealthyFetcher().get(url, timeout=20)

# Level 3 – headless browser (JS-rendered pages)
from scrapling.fetchers import DynamicFetcher
page = DynamicFetcher().get(url, timeout=30)
```

---

## Checklist – new scraper

- [ ] `EVENTS_URL`, `VENUE`, `SOURCE` filled in
- [ ] All `.get()`/`.getall()` values wrapped with `str()`
- [ ] Past events filtered out (`dt < datetime.now()`)
- [ ] Relative URLs made absolute
- [ ] `save_events(events, source=SOURCE)` called
- [ ] `main()` returns `0` on success, `1` on no events found
- [ ] Tested against the database
- [ ] Venue added to `VENUE_DEFAULTS` in `config.py`
