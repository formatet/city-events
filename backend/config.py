"""
City-specific configuration for the city-events calendar.

This is the only file you need to replace when cloning the project
for a new city. Everything else (scrapers, db_utils, Flask API, frontend)
is generic.

TITLE_BLACKLIST   – substrings that disqualify an event regardless of source.
                    Checked by db_utils.save_events() before any DB write.
                    Use for services, clubs, and non-event content that
                    appears across multiple scrapers.

VENUES_WITH_OWN_SCRAPER – venues covered by dedicated scrapers.
                    Omnibus scrapers (e.g. stadskalender_barn) import this
                    to avoid double-scraping. Single source of truth.

VENUE_DEFAULTS  – default category for a venue.
                  db_utils also does pattern-based church detection:
                  any venue containing 'kyrka', 'kapell', 'domkyrka' or
                  'katedral' gets 'Klassisk' automatically.

CATEGORY_KEYWORDS – title/description keywords that override venue default.
                    Priority order matters: first match wins.
                    'Övrigt' is intentionally absent – it is only a fallback,
                    never keyword-triggered.
"""

# ---------------------------------------------------------------------------
# Globalt innehållsfilter – tillämpas av db_utils.save_events() på alla events
# ---------------------------------------------------------------------------
# Titlar som innehåller något av dessa strängar sparas aldrig i databasen,
# oavsett källa. Håll listan konservativ – hellre för lite än för mycket.
TITLE_BLACKLIST = {
    # Event som flyttat till en annan spelplats. Den gamla scenen låter posten
    # ligga kvar som hänvisning ("Stick To Your Guns | Flyttad till The Abyss"),
    # och eftersom vi scrapar båda husen blir det en dubblett där den ena pekar
    # på fel plats. Kräver "till" – enbart "flyttat" eller "nytt datum" betyder
    # att eventet blivit omdaterat och fortfarande är giltigt.
    'flyttad till',
    'flyttat till',
    'flyttas till',
    # Tjänster – aldrig kalender-events
    'bokbord',
    'juridisk asylrådgivning',
    # Studiehandledning och digital hjälp
    'läxhjälp',
    'digital handledning',
    'teknikhjälp',
    'digitalt stöd',
    'digital hjälp',
    'digitala torsdagar',
    'digitala fredagar',
    'digitala onsdagar',
    # Språkaktiviteter (tjänster, inte events)
    'träna svenska',
    'lär dig svenska',
    'språkcafé',
    'språkkafé',
    'stickcafé',
    'på lätt svenska',
    'på lätt finska',
    # Dryck
    'ölprovning',
    'vinprovning',
    # Kulturspecifika ämnesfilter
    'somali',
    # 'föreläsning' låg här t.o.m. 2026-08-22 med motiveringen "inte
    # upplevelsekultur". Borttaget: filtret var en substring och tog även
    # författarkvällar och kulturhistoriska föredrag ("Sonja Åkesson 100 år med
    # hyllningsföreläsning"). Kategorin finns redan – CATEGORY_KEYWORDS['Samtal']
    # har 'föreläsning' som nyckelord, så posterna hamnar under Samtal.
    # Awareness-dagar och workshops som tjänster
    'mensdagen',
    'skrivworkshop',
    # Språkaktiviteter riktade till inlärare
    'språkträff',
    # Kurser – man lär sig något, man upplever inte något
    'danskurs',
    'grundkurs',
    'fortsättningskurs',
    # Praktiska tjänster och medborgerliga möten
    'klädbyte',
    # Inte bara 'familjehem' – det fångade Bokmässans deckarsamtal om
    # 'familjehemligheter'. Målet är organisationen och dess infomöten.
    'familjehem göteborg',
    'bli familjehem',
    'fullmäktige',
    # Hälsoinformation
    'vaccin',
    'hälsorisk',
    # Återkommande hobby-aktiviteter (bibliotek)
    'målarfredag',
    'broderi',
    'stickpicknick',
    # Stay Out West-klubbkvällarna som paraplyposter. Musikens Hus och
    # Konserthuset listar hela kvällen som ETT event; scrape_wayoutwest_db.py
    # importerar samma kvällar akt för akt med riktig speltid. Utan filtret
    # dubbleras kvällen när (WoW) slås på.
    'stay out west i göteborgs konserthus',
    'stay out west #',
}

# ---------------------------------------------------------------------------
# Venues med dedikerade scrapers
# ---------------------------------------------------------------------------
# Omnibus-scrapers (t.ex. stadskalender_barn) importerar denna mängd och
# hoppar över venues som täcks härifrån. Lägg alltid till här när en ny
# dedikerad scraper skapas för ett bibliotek eller kulturhus.
# ---------------------------------------------------------------------------
# Titelersättningar – tillämpas av db_utils.save_events() efter normalisering
# ---------------------------------------------------------------------------
# Långa arrangörsnamn som källor klistrar framför den riktiga titeln. Regex mot
# titeln, skiftlägesokänsligt. Håll listan kort – det här är kosmetik, inte
# filtrering (använd TITLE_BLACKLIST för att utesluta events helt).
TITLE_REPLACEMENTS = (
    # Göteborgs Dans- och Teaterfestival, med och utan bindestreck.
    # OBS: festivalen är en ARRANGÖR, inte en plats. Den får aldrig hamna i
    # venue-kolumnen – venue ska alltid vara en fysisk spelplats. Kommer den in
    # som venue betyder det att scrapern läst arrangören i stället för lokalen,
    # och då är den riktiga platsen förlorad. Se scrape_kulturpunkten_db.py,
    # som hämtar spelplatsen från detaljsidan just av det skälet.
    (r'Göteborgs\s+Dans[\s-]+och\s+Teaterfestival(en)?', 'GDTF'),
)

# Venue-ersättningar – samma princip, mot venue-kolumnen. Källor lägger ofta
# till stadsdel, gatuadress eller vägbeskrivning efter platsnamnet. Regex mot
# hela venue-strängen, skiftlägesokänsligt.
VENUE_REPLACEMENTS = (
    # 'Bananpiren, Frihamnen (vid Flytevi, den marina kolonilotten)' och
    # 'Bananpiren, Frihamnen' är samma kaj.
    (r'^Bananpiren\b.*', 'Bananpiren'),
)

VENUES_WITH_OWN_SCRAPER = {
    # Bibliotek (scrape_bibliotek_db.py)
    'Stadsbiblioteket',
    'Stadsbiblioteket på Götaplatsen',
    'Majornas bibliotek',
    'Majornas Bibliotek',
    # Kortedala och Gamlestaden togs bort ur scrape_bibliotek_db.py 2026-07-25.
    # De står kvar HÄR med flit: mängden används av omnibus-scrapers för att
    # hoppa över venues, så posterna hindrar dem från att komma in bakvägen.
    # Ta inte bort dem för att "städa" – då börjar de dyka upp igen.
    'Kortedala bibliotek',
    'Kortedala Bibliotek',
    'Gamlestadens bibliotek',
    'Gamlestadens Bibliotek',
    # Sedan 2026-08-22 tar scrape_bibliotek_db.py hela biblioteksvyn i stadens
    # kalendarium, alltså samtliga filialer – inte bara Stadsbiblioteket och
    # Majorna. Kalendariet är inkonsekvent med versalt/gement "bibliotek",
    # därför båda varianterna.
    'Angereds bibliotek', 'Angereds Bibliotek',
    'Askims bibliotek', 'Askims Bibliotek',
    'Backa bibliotek', 'Backa Bibliotek',
    'Bergsjöns bibliotek', 'Bergsjöns Bibliotek',
    'Biskopsgårdens bibliotek', 'Biskopsgårdens Bibliotek',
    'Eriksbergs bibliotek', 'Eriksbergs Bibliotek',
    'Friskväderstorgets bibliotek', 'Friskväderstorgets Bibliotek',
    'Frölunda bibliotek', 'Frölunda Bibliotek',
    'Guldhedens bibliotek', 'Guldhedens Bibliotek',
    'Hammarkullens bibliotek', 'Hammarkullens Bibliotek',
    'Hjällbo bibliotek', 'Hjällbo Bibliotek',
    'Högsbo bibliotek', 'Högsbo Bibliotek',
    'Kyrkbyns bibliotek', 'Kyrkbyns Bibliotek',
    'Lagerhusets bibliotek', 'Lagerhusets Bibliotek',
    'Lundby bibliotek', 'Lundby Bibliotek',
    'Opaltorgets bibliotek', 'Opaltorgets Bibliotek',
    'Södra Skärgårdens bibliotek', 'Södra Skärgårdens Bibliotek',
    'Torslanda bibliotek', 'Torslanda Bibliotek',
    'Tuve bibliotek', 'Tuve Bibliotek',
    # Kulturhus
    'Kulturhuset Kåken',         # scrape_bibliotek_db.py (ligger i biblioteksvyn)
    'Slottsskogen',              # scrape_bibliotek_db.py (enhetssida)
    'Trädgårdsföreningen',       # scrape_bibliotek_db.py (enhetssida)
    'Kulturhuset Blå Stället',   # scrape_blastallet_db.py
    'Alfons Åbergs Kulturhus',   # scrape_alfons_db.py
    # Övriga (filtreras redan av is_relevant_venue i stadskalender_barn,
    # men listade här för fullständighet och framtida omnibus-scrapers)
    'Bio Roy',
    'Bio Capitol',
    'Hagabion',
    'Botaniska trädgården',
    'Stora Teatern',
    'Aftonstjärnan',
}

# Barn-sub-kategorier (visas bara på barn.kristall.info).
# Placeras FÖRE vuxen-kategorier för att ta prioritet vid match.
# Nyckelord ska vara specifika nog att inte råka matcha vuxenevents.
BARN_CATEGORIES = frozenset([
    'Barnteater', 'Barnmusik', 'Barndans',
    'Skapande', 'Läs & Lyssna', 'Rörelse', 'Familj', 'Natur',
])

CATEGORY_KEYWORDS = {
    'Fotboll':      ['fotboll', 'allsvenskan', 'superettan'],

    # Barn-sub-kategorier – specifika nyckelord, inte generiska (teater, musik etc.)
    'Barnteater':   ['barnteater', 'familjeteater', 'barnföreställning',
                     'familjeföreställning', 'familjevisning', 'dockteater',
                     'skuggteater', 'skuggteatern', 'cirkusföreställning',
                     'barn och unga', 'julefrid', 'turandot', 'pinocchio',
                     'för de allra minsta'],
    'Barnmusik':    ['bebisrytmik', 'babymusik', 'babykonsert', 'barnkonsert',
                     'familjekonsert', 'sångstund', 'barnkör',
                     'musik för barn', 'sång och rytm',
                     'prova på gitarr', 'testa att dj', 'sjung med'],
    'Barndans':     ['barndans', 'dans för barn', 'dansworkshop', 'familjeddans',
                     'hiphop och streetdance', 'streetdance', 'utomhusdisko'],
    'Rörelse':      ['äventyrslajv', 'lajv på museet', 'barnidrott',
                     'barnakrobatik', 'parkour', 'karate', 'capoeira'],
    'Skapande':     ['pyssel', 'pridepyssel', 'barnpyssel', 'kreativ', 'måla',
                     'gör en ', 'bygg en ', 'klipp och klistra',
                     'tälj', 'brodera', 'mosaik', 'kollage', 'blocktryck', 'lera',
                     'nyckelring', 'drömfångare', 'krympplast', 'warli',
                     'återbruka', 'tova ', 'slöjdkväll', 'ateljé för barn',
                     'kreativa lördagar', 'lördagsstudion', 'öppen ateljé'],
    'Läs & Lyssna': ['sagostund', 'onsdagssaga', 'torsdagssaga',
                     'bokklubb för', 'fågelfabler', 'fabler', 'sommarboken',
                     'sommarbokenträff', 'sommarbokklubben', 'bokskattjakt',
                     'bebis & bok', 'läs med', 'läslyssna', 'högläsning för barn'],
    'Familj':       ['föräldraledig', 'öppen förskola', 'öppna förskolan',
                     'familjefredag', 'bebis', 'babyvisning', 'babbla med baby',
                     'träff för föräldralediga', 'tutar och blinkar'],
    'Natur':        ['bioblitz', 'djuren i staden', 'draktjuvarna',
                     'natur för barn'],

    'Opera':    ['opera', 'operett'],
    'Klassisk': ['körkonsert', 'kyrkokonsert', 'kammarkonsert', 'kammarmusik',
                 'orgelkonsert', 'filharmoni', 'symfoniorkester', 'blåsorkester',
                 'kammarkör', 'gospelkör', 'manskör', 'damkör',
                 'kantata', 'requiem', 'mässa'],
    'Teater':   ['teaterföreställning', 'pjäs', 'dramatisering',
                 'musikal', 'musical'],
    'Dans':     ['dansföreställning', 'dansuppvisning', 'folkdans',
                 'balett', 'koreografi', 'danskurs'],
    'Konst':    ['utställning', 'exhibition', 'konstverk', 'vernissage'],
    'Nöje':     ['standup', 'stand-up', 'komedi', 'comedy', 'ståupp',
                 'quiz', 'improv', 'improvteater', 'humor'],
    'Samtal':   ['föreläsning', 'föredrag', 'seminarium', 'lecture', 'poesi',
                 'poetry', 'dikter', 'poet', 'författar', 'forsk', 'samtal om'],
    'Musik':    ['konsert', 'sjung', 'spelning', 'livemusik', 'live musik'],
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
    '2Lång':              'Teater',
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
    'Brännö kyrka':                 'Klassisk',

    # Musik
    'Pustervik':          'Musik',
    'Pusterviksbaren':    'Musik',
    'Oceanen':            'Musik',
    'Brofästet':          'Musik',
    'Nefertiti':          'Musik',
    'Konserthuset':       'Musik',
    'Draken Live':        'Musik',
    'Liseberg':           'Musik',
    'Skeppet GBG':        'Musik',
    'Kajskjul 8':         'Musik',
    'Fyrens Ölkafé':      'Musik',
    'Bryggan':            'Musik',
    'Frihamnens Event':   'Musik',
    'Scandinavium':       'Musik',
    'Ullevi':             'Musik',
    'Grindstugan':        'Musik',
    'Gathenhielmska':     'Musik',
    'Andra stället':      'Musik',
    'Brewhouse':          'Musik',
    'Unity Jazz':         'Musik',
    'Dirty Deeds':        'Musik',
    'Ögat':               'Musik',
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

    # Göteborgskalaset – tillfälliga festivalytor (scrape_goteborgskalaset_db.py)
    'Götaplatsen':               'Musik',
    'Kungstorget':               'Musik',
    'Bältespännarparken':        'Dans',
    'Kungsparken':               'Teater',
    'Ostindiefararen Götheborg': 'Övrigt',
    'Göteborgs Stadsmuseum':     'Konst',
    'Sockerbruket 8':            'Konst',
    'Medicinhistoriska museet':  'Konst',

    # Scener som Kulturpunkten listar under arrangörsnamn (detaljsidans plats)
    'Esperantoscenen':            'Teater',
    'Cinnober':                   'Teater',
    'ADAS teater':                'Teater',
    'Dergårdsteatern':            'Teater',
    'Regionteater Väst i Borås':  'Teater',
    'Kustens Hus':                'Teater',
    '3:e våningen Sockerbruket':  'Dans',

    # Klubb
    'Yaki-Da':       'Klubb',
    'Excet':         'Klubb',
    'Park Lane':     'Klubb',
    'Bardot':        'Klubb',
    # 'Sticky Fingers': stängt sedan länge – borttagen

    # Biblioteksfilialer (alla via stadskalender-scrapers)
    'Gamlestadens bibliotek':           'Samtal',
    'Frölunda bibliotek':               'Samtal',
    'Lundby bibliotek':                 'Samtal',
    'Bergsjöns bibliotek':              'Samtal',
    'Backa bibliotek':                  'Samtal',
    'Hjällbo bibliotek':                'Samtal',
    'Biskopsgårdens bibliotek':         'Samtal',
    'Lagerhusets Bibliotek':            'Samtal',
    'Tuve bibliotek':                   'Samtal',
    'Opaltorgets Bibliotek':            'Samtal',
    'Angereds bibliotek':               'Samtal',
    'Hammarkullens bibliotek':          'Samtal',
    'Guldhedens bibliotek':             'Samtal',
    'Torslanda bibliotek':              'Samtal',
    'Askims bibliotek':                 'Samtal',
    'Friskväderstorgets bibliotek':     'Samtal',
    'Kyrkbyns bibliotek':               'Samtal',
    'Södra Skärgårdens Bibliotek':      'Samtal',
    'Högsbo bibliotek':                 'Samtal',
    'Eriksbergs Bibliotek':             'Samtal',

    # Kulturhus (stadskalender)
    'Kulturhuset Bergsjön':             'Teater',
    'Kulturhuset Kåken':                'Teater',
    'Kulturrummet Gårdsten':            'Övrigt',
    'Frölunda Kulturhus':               'Teater',

    # Teater – venues utan egen scraper
    'Hagateatern':            'Teater',
    'Masthuggsteatern':       'Teater',

    # Samtal
    'Lohrs bokhandel':        'Samtal',
    'Vetenskapsfestivalen':   'Samtal',
    'Litteraturhuset':        'Samtal',
    'Stadsbiblioteket':       'Samtal',
    'Majornas bibliotek':     'Samtal',
    'Slottsskogsobservatoriet': 'Samtal',
    'GU Vasaparken':          'Samtal',
    'Hörsalen':               'Samtal',

    # Barn-venues – default är den vanligaste typen på varje venue.
    # Specifika events fångas av keyword-reglerna ovan.
    # Teater – venues som saknade default
    'Teater Smuts':                       'Teater',
    'Göteborgs Dramatiska Teater':        'Teater',

    # Nöje – comedy/variety-venues
    'Wic Mack AB':                        'Nöje',

    # Samtal – naturguidade venues
    'Botaniska trädgården':               'Samtal',

    # Way Out West – egen kategori, döljs som standard i frontend (se render.js).
    # 'Slottsskogen' står redan som 'Natur' nedan för parkevents; WoW-scrapern
    # sätter kategorin explicit så venue-defaulten spelar ingen roll där.
    'Stay Out West':                      'Way Out West',
    'Dungen Stage':                       'Way Out West',

    # Rena barn-venues: venue-default = barn-kategori (allt där är barn)
    'Slottsskogen':            'Natur',
    'Blå Stället':             'Skapande',
    'Teater Sesam':            'Barnteater',
    'Alfons Åbergs Kulturhus': 'Skapande',

    # Blandade venues: vuxen-default, barn fångas av keywords
    'Kortedala bibliotek':     'Samtal',
    'Världskulturmuseet':      'Övrigt',

    # Övrigt – äkta catch-all
    'Chalmerspyrot':          'Övrigt',
    'Naturhistoriska museet': 'Övrigt',
    'Trädgårdsföreningen':    'Samtal',
}
