"""
City-specific configuration for the city-events calendar.

This is the only file you need to replace when cloning the project
for a new city. Everything else (scrapers, db_utils, Flask API, frontend)
is generic.

VENUE_DEFAULTS  – default category for a venue.
                  Keyword matching in db_utils can override this.

CATEGORY_KEYWORDS – title keywords that override the venue default.
                    Priority order matters: first match wins.
"""

# Categories and keywords – generic, works for any city.
# Priority order matters – first match wins.
CATEGORY_KEYWORDS = {
    'Standup':    ['standup', 'stand-up', 'komedi', 'comedy', 'ståupp'],
    'Övrigt':     ['quiz', 'karaoke', 'ölprovning'],
    'Opera':      ['opera'],
    'Dans':       ['dans', 'balett', 'koreografi', 'dansa'],
    'Musikal':    ['musikal', 'musical'],
    'Barn':       ['barn', 'familj', 'barnföreställning', 'familjeföreställning', 'bebis'],
    'Klubb':      [' dj ', 'club night', 'afterwork', 'techno', 'house'],
    'Film':       ['film', 'bio'],
    'Poesi':      ['poesi', 'poetry', 'poem', 'dikter', 'dikt', 'poet'],
    'Vernissage': ['vernissage'],
    'Samtal':     ['författar', 'forsk', 'föreläsning', 'seminarium'],
}

# Venue defaults – replace with your local venues.
# Format: 'Venue name': 'Category'
VENUE_DEFAULTS = {
    # Film
    'Bio Roy': 'Film',
    'Hagabion': 'Film',
    'Bio Capitol': 'Film',
    'Cinemateket': 'Film',
    'Aftonstjärnan': 'Film',

    # Utställning
    'Konsthallen': 'Utställning',
    'Konstmuseet': 'Utställning',
    'Röhsska museet': 'Utställning',

    # Dans
    'Atalante': 'Dans',

    # Teater
    'Stadsteatern': 'Teater',
    'GEST': 'Teater',
    'Backa Teater': 'Teater',
    'Lorensbergsteatern': 'Teater',
    'Folkteatern': 'Teater',
    'Kulturpunkten': 'Teater',
    'Angereds Teater': 'Teater',
    'Big Wind': 'Teater',
    'Konstepidemin Scen': 'Teater',
    'Konstkollektivet Snö': 'Teater',
    'Teater Sesam': 'Teater',
    'Teater Trixter': 'Teater',
    'Teater UNO': 'Teater',
    'Stora Teatern': 'Teater',
    '2LANG': 'Teater',

    # Opera
    'GöteborgsOperan': 'Opera',

    # Musik
    'Pustervik': 'Musik',
    'Pusterviksbaren': 'Musik',
    'Oceanen': 'Musik',
    'Nefertiti': 'Musik',
    'Konserthuset': 'Musik',
    'Draken Live': 'Musik',
    'Skeppet GBG': 'Musik',
    'Kajskjul 8': 'Musik',
    'Fyrens Ölkafé': 'Musik',
    'Bryggan': 'Musik',
    'Frihamnens Event': 'Musik',
    'GWO': 'Musik',
    'Unity Jazz': 'Musik',
    'Utopia Jazz': 'Musik',
    'Playhouse Jazz': 'Musik',
    "Trädgår'n": 'Musik',
    'Restaurang Folk': 'Musik',
    'Musikens Hus': 'Musik',
    'Hängmattan': 'Musik',
    'Valand': 'Musik',
    'Monument031': 'Musik',
    'Porter Pelle': 'Musik',
    'Fängelset': 'Musik',
    'Potatisen': 'Musik',
    'The Abyss': 'Musik',
    'Contrast Public House': 'Musik',
    'KoM Musik & Bar': 'Musik',
    'Koloni': 'Musik',
    'Visans Vänner i Göteborg': 'Musik',
    'Nationella minoriteters kulturhus': 'Musik',
    'FiaskoKompaniet': 'Musik',
    'Gothenburg Film Studios': 'Musik',
    'Llama Lloyd': 'Musik',

    # Klubb
    'Yaki-Da': 'Klubb',
    'Excet': 'Klubb',
    'Park Lane': 'Klubb',
    'Bardot': 'Klubb',
    'Sticky Fingers': 'Klubb',

    # Samtal
    'Vetenskapsfestivalen': 'Samtal',
    'Litteraturhuset': 'Samtal',
    'Stadsbiblioteket': 'Samtal',
    'Majornas bibliotek': 'Samtal',
    'Slottsskogsobservatoriet': 'Samtal',

    # Övrigt
    'Chalmerspyrot': 'Övrigt',
}
