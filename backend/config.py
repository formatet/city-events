"""
City-specific configuration for the city-events calendar.

This is the only file you need to replace when cloning the project
for a new city. Everything else (scrapers, db_utils, Flask API, frontend)
is generic.

VENUE_DEFAULTS  – default category for a venue.
                  db_utils also does pattern-based church detection:
                  any venue containing 'kyrka', 'kapell', 'domkyrka' or
                  'katedral' gets 'Klassisk' automatically.

CATEGORY_KEYWORDS – title/description keywords that override venue default.
                    Priority order matters: first match wins.
                    'Övrigt' is intentionally absent – it is only a fallback,
                    never keyword-triggered.
"""

# 10 categories. Priority order: specific beats generic.
# Barn first (a barnkonsert is Barn regardless of venue).
# Nöje before Musik (quiz at a music venue = Nöje, not Musik).
# Klassisk before Musik (körkonsert is Klassisk even at mixed venues).
# Musik last among live-performance keywords (generic fallback).
# Övrigt is NOT here – only applied as venue fallback in db_utils.
CATEGORY_KEYWORDS = {
    'Fotboll':  ['fotboll', 'allsvenskan', 'superettan'],
    'Barn':     ['barnföreställning', 'familjeföreställning', 'barnkonsert',
                 'barn och unga', 'för barn', 'familjevisning', 'bebis', 'bebisrytmik',
                 'babyvisning', 'babymusik', 'babykonsert'],
    'Opera':    ['opera', 'operett'],
    'Klassisk': ['körkonsert', 'kyrkokonsert', 'kammarkonsert', 'kammarmusik',
                 'orgelkonsert', 'filharmoni', 'symfoniorkester', 'blåsorkester',
                 'kammarkör', 'gospelkör', 'manskör', 'damkör', 'barnkör',
                 'kantata', 'requiem', 'mässa'],
    'Teater':   ['teaterföreställning', 'pjäs', 'dramatisering',
                 'musikal', 'musical'],
    'Dans':     ['dansföreställning', 'dansuppvisning', 'folkdans',
                 'balett', 'koreografi', 'danskurs'],
    'Konst':    ['utställning', 'exhibition', 'konstverk', 'vernissage'],
    'Nöje':     ['standup', 'stand-up', 'komedi', 'comedy', 'ståupp',
                 'quiz', 'karaoke', 'improv', 'improvteater', 'humor'],
    'Samtal':   ['föreläsning', 'seminarium', 'lecture', 'poesi', 'poetry',
                 'dikter', 'poet', 'författar', 'forsk', 'samtal om'],
    'Musik':    ['konsert', 'sjung', 'spelning', 'livemusik', 'live musik'],
}

# Venues that have a dedicated scraper and should not be scraped by aggregators
VENUES_WITH_OWN_SCRAPER = {
    'Stora Teatern',
    'Aftonstjärnan',
}

# Venue defaults.
# Churches not listed here are caught by the pattern matcher in db_utils
# (any venue name containing 'kyrka', 'kapell', 'domkyrka', 'katedral').
VENUE_DEFAULTS = {
    # Film
    'Bio Roy':        'Film',
    'Hagabion':       'Film',
    'Bio Capitol':    'Film',
    'Cinemateket':    'Film',
    'Aftonstjärnan':  'Film',

    # Konst (was Bildkonst)
    'Konsthallen':         'Konst',
    'Konstmuseet':         'Konst',
    'Konstepidemin':       'Konst',
    'Röhsska museet':      'Konst',
    'HDK-Valand':          'Konst',
    'Göteborgs konstmuseum': 'Konst',
    'Llama Lloyd':         'Konst',

    # Dans
    'Atalante': 'Dans',

    # Teater
    'Stadsteatern':       'Teater',
    'GEST':               'Teater',
    'Backa Teater':       'Teater',
    'Lorensbergsteatern': 'Teater',
    'Folkteatern':        'Teater',
    'Kulturpunkten':      'Teater',
    'Angereds Teater':    'Teater',
    'Big Wind':           'Teater',
    'Konstepidemin Scen': 'Teater',
    'Konstkollektivet Snö': 'Teater',
    'Teater Sesam':       'Teater',
    'Teater Trixter':     'Teater',
    'Teater UNO':         'Teater',
    'Stora Teatern':      'Teater',
    '2LANG':              'Teater',
    'Redbergsteatern':    'Teater',
    'Sommarteatern':      'Teater',
    'Trappscenen':        'Teater',

    # Fotboll
    'Gamla Ullevi':  'Fotboll',
    'Bravida Arena': 'Fotboll',
    'IFK Göteborg':  'Fotboll',
    'BK Häcken':     'Fotboll',
    'Örgryte IS':    'Fotboll',
    'GAIS':          'Fotboll',

    # Opera
    'GöteborgsOperan': 'Opera',

    # Klassisk – specifika venues (kyrkor fångas även av pattern i db_utils)
    'Göteborg Wind Orchestra':      'Klassisk',
    'GWO':                          'Klassisk',
    'Musikhögskolan Eklandagatan':  'Klassisk',
    'Haga Konserthall':             'Klassisk',
    'Göteborgs domkyrka':           'Klassisk',
    'Hagakyrkan':                   'Klassisk',
    'Tyska Christinae kyrka':       'Klassisk',
    'Vasakyrkan':                   'Klassisk',
    'Johannebergskyrkan':           'Klassisk',
    'Oscar Fredriks kyrka':         'Klassisk',
    'Masthuggskyrkan':              'Klassisk',
    'Annedalskyrkan':               'Klassisk',
    'Biskopsgårdens kyrka':         'Klassisk',
    'Carl Johans kyrka':            'Klassisk',
    'Lundby nya kyrka':             'Klassisk',
    'Betlehemskyrkan':              'Klassisk',
    'Sjömanskyrkan':                'Klassisk',

    # Musik
    'Pustervik':          'Musik',
    'Pusterviksbaren':    'Musik',
    'Oceanen':            'Musik',
    'Nefertiti':          'Musik',
    'Konserthuset':       'Musik',
    'Draken Live':        'Musik',
    'Liseberg':           'Musik',
    'Skeppet GBG':        'Musik',
    'Kajskjul 8':         'Musik',
    'Fyrens Ölkafé':      'Musik',
    'Bryggan':            'Musik',
    'Frihamnens Event':   'Musik',
    'Grindstugan':        'Musik',
    'Gathenhielmska':     'Musik',
    'Andra stället':      'Musik',
    'Brewhouse':          'Musik',
    'Unity Jazz':         'Musik',
    'Utopia Jazz':        'Musik',
    'Playhouse Jazz':     'Musik',
    "Trädgår'n":          'Musik',
    'Restaurang Folk':    'Musik',
    'Musikens Hus':       'Musik',
    'Hängmattan':         'Musik',
    'Valand':             'Musik',
    'Monument031':        'Musik',
    'Porter Pelle':       'Musik',
    'Fängelset':          'Musik',
    'Potatisen':          'Musik',
    'The Abyss':          'Musik',
    'Contrast Public House': 'Musik',
    'KoM Musik & Bar':    'Musik',
    'Koloni':             'Musik',
    'Visans Vänner i Göteborg': 'Musik',
    'Nationella minoriteters kulturhus': 'Teater',
    'FiaskoKompaniet':    'Musik',
    'Gothenburg Film Studios': 'Musik',
    "Jacy'z Hotel":       'Musik',
    'Guldhedens Restaurang': 'Musik',
    'Sekten':             'Musik',

    # Klubb
    'Yaki-Da':       'Klubb',
    'Excet':         'Klubb',
    'Park Lane':     'Klubb',
    'Bardot':        'Klubb',
    'Sticky Fingers': 'Klubb',

    # Samtal
    'Lohrs bokhandel':        'Samtal',
    'Vetenskapsfestivalen':   'Samtal',
    'Litteraturhuset':        'Samtal',
    'Stadsbiblioteket':       'Samtal',
    'Majornas bibliotek':     'Samtal',
    'Slottsskogsobservatoriet': 'Samtal',
    'GU Vasaparken':          'Samtal',
    'Hörsalen':               'Samtal',

    # Övrigt – äkta catch-all
    'Chalmerspyrot':              'Övrigt',
    'Göteborgs botaniska trädgård': 'Övrigt',
}
