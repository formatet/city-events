# Slutsåld-filtrering – återstående scrapers

Batch 1 (2026-05-01): 15 scrapers fixade
Batch 2 (2026-05-01): 10 scrapers fixade
Kvar: 24 scrapers

## Ej åtgärdade

### Mellannivå
- `scrape_stadsbiblioteket_db.py` – Stadsbiblioteket (gratis events, säljer sällan ut)
- `scrape_slottsskogsobservatoriet_db.py` – Slottsskogsobservatoriet
- `scrape_kontmuseum_db.py` – Konstmuseet
- `scrape_konsthall_db.py` – Konsthallen
- `scrape_rohsska_db.py` – Röhsska museet
- `scrape_majorna_bibliotek_db.py` – Majornas bibliotek
- `scrape_grindstugan_db.py` – Grindstugan
- `scrape_fyren_db.py` – Fyrens Ölkafé
- `scrape_filmstudios_db.py` – Gothenburg Film Studios
- `scrape_gathenhielmska_db.py` – Gathenhielmska
- `scrape_fangelset_db.py` – Fängelset

### Låg prioritet (säljer sällan ut)
- `scrape_2lang_db.py` – 2LANG
- `scrape_bioroy_db.py` – Bio Roy
- `scrape_capitol_db.py` – Bio Capitol
- `scrape_contrastgbg_db.py` – Contrast Public House
- `scrape_llamalloyd_db.py` – Llama Lloyd
- `scrape_lohrs_db.py` – Lohrs bokhandel
- `scrape_parklane_db.py` – Park Lane (klub, sällan slutsålt)
- `scrape_porterpelle_db.py` – Porter Pelle
- `scrape_unityjazz_db.py` – Unity Jazz
- `scrape_utopiajazz_db.py` – Utopia Jazz
- `scrape_svenskakyrkan_gbg_db.py` – Svenska kyrkan
- `scrape_pustervik_db.py` – ✓ fixad (batch 1)
- `scrape_backa_db.py` – ✓ redan fixad

### GöteborgsOperan – kvar
- `scrape_operan_db.py` – best-effort kontextcheck tillagd (batch 1);
  fullständig fix kräver detaljsidor per föreställning (~50 req/körning).
  Approach: extrahera `/forestallningar/<slug>/`-URL:er → hämta → kolla "Utsålt".

## Approach för kvarvarande
De flesta saknar biljetthantering på sin listningssida. Mönstret:
  1. `text = soup.get_text()` / `page.css('*::text').getall()` på event-blocket
  2. `if any(w in text.lower() for w in ('slutsålt', 'utsålt', ...)): continue`
