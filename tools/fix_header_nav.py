# -*- coding: utf-8 -*-
"""
Sostituisce il menu header (pulsante hamburger + tendina) con
un'implementazione propria, senza dipendere dalla Interactivity API
di WordPress.

Perche': il pulsante hamburger e il sottomenu usavano
data-wp-on-async--click="actions.openMenuOnClick" ecc., gestiti dal
modulo JS "@wordpress/interactivity". Quel modulo viene risolto tramite
un <script type="importmap"> che punta pero' a un URL ASSOLUTO
(https://iniziativepop.it/...) invece che locale: nel sito in
anteprima (iniziativepop.vercel.app) quel fetch fallisce, l'import si
rompe e con esso l'intera Interactivity API — quindi il pulsante non
apre nulla, su nessuna dimensione di schermo (la voce del blocco era
impostata "always-shown": niente riga orizzontale alternativa).

La sostituzione: un pulsante hamburger + pannello a schermo intero in
puro HTML/CSS/JS (nessuna dipendenza), stessi 5 link ovunque, con
riga orizzontale sopra i 783px e pannello sotto. CSS e JS aggiunti una
sola volta nei file già condivisi da tutte le pagine (style.css e
navigation-customization.js), quindi qui si tocca solo l'HTML.

Uso: python tools/fix_header_nav.py site
"""
import sys, io, os
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = sys.argv[1]

# etichetta -> testo da cercare nel menu attuale (per estrarne l'href corretto,
# gia' relativo alla profondita' della pagina)
WANTED = [
    "Legge elettorale proporzionale con preferenze",
    "Cancellierato italiano",
    "Iscriviti al comitato",       # variante minuscola (quasi tutte le pagine)
    "Iscriviti all'associazione",  # variante gia' aggiornata, se presente
    "Iscriviti al Comitato",       # variante maiuscola (solo iscrizione/)
    "Lo statuto",
    "Stampa ed eventi",
]

HAMBURGER_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">'
                  '<path d="M5 5v1.5h14V5H5zm0 7.8h14v-1.5H5v1.5zM5 19h14v-1.5H5V19z"></path></svg>')
CLOSE_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M13.06 12l6.47-6.47-1.06-1.06L12 10.94 5.53 4.47 4.47 5.53 10.94 12l-6.47 6.47 1.06 1.06L12 13.06l6.47 6.47 1.06-1.06z"></path></svg>')

changed = 0
skipped = []

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if fn not in ("index.html", "404.html"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "lxml")

        header = soup.find("header")
        if header is None:
            skipped.append((p, "no header"))
            continue
        nav = header.find("nav")
        if nav is None:
            skipped.append((p, "no nav in header"))
            continue

        # raccoglie i link attuali per etichetta esatta
        found = {}
        for a in nav.find_all("a", href=True):
            label_el = a.find(class_="wp-block-navigation-item__label")
            text = (label_el.get_text(strip=True) if label_el else a.get_text(strip=True))
            if text in WANTED and text not in found:
                found[text] = a["href"]

        iscrizione_href = found.get("Iscriviti al Comitato") or found.get("Iscriviti all'associazione") \
            or found.get("Iscriviti al comitato")
        iscrizione_label = "Iscriviti al Comitato" if "Iscriviti al Comitato" in found else "Iscriviti all'associazione"

        links = [
            ("Legge Elettorale Proporzionale con Preferenze", found.get("Legge elettorale proporzionale con preferenze")),
            ("Cancellierato Italiano", found.get("Cancellierato italiano")),
            (iscrizione_label, iscrizione_href),
            ("Lo statuto", found.get("Lo statuto")),
            ("Stampa ed eventi", found.get("Stampa ed eventi")),
        ]
        missing = [lbl for lbl, href in links if not href]
        if missing:
            skipped.append((p, "mancano link: %s" % missing))
            continue

        def li_items(extra_class=""):
            out = []
            for lbl, href in links:
                out.append('<li><a href="%s"%s>%s</a></li>' % (
                    href, (' class="%s"' % extra_class) if extra_class else "", lbl))
            return "".join(out)

        new_nav_html = (
            '<nav aria-label="Menu principale" class="cip-nav">'
            '<button type="button" class="cip-nav-toggle" aria-label="Apri menu" '
            'aria-expanded="false" aria-controls="cip-nav-panel">%s</button>'
            '<ul class="cip-nav-row">%s</ul>'
            '<div id="cip-nav-panel" class="cip-nav-panel" hidden>'
            '<button type="button" class="cip-nav-panel-close" aria-label="Chiudi menu">%s</button>'
            '<ul>%s</ul>'
            '</div>'
            '</nav>'
        ) % (HAMBURGER_SVG, li_items(), CLOSE_SVG, li_items())

        new_nav = BeautifulSoup(new_nav_html, "lxml").nav
        nav.replace_with(new_nav)

        with open(p, "w", encoding="utf-8") as f:
            f.write(str(soup))
        changed += 1

print("Pagine aggiornate: %d" % changed)
if skipped:
    print("Saltate (%d):" % len(skipped))
    for p, why in skipped:
        print("  ", p, "->", why)
