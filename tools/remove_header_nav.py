# -*- coding: utf-8 -*-
"""
Rimuove del tutto la navigazione dall'header (hamburger + riga di link
desktop), lasciando solo il logo. La navigazione resta disponibile dal
footer, gia' presente su ogni pagina.

Uso: python tools/remove_header_nav.py site
"""
import sys, io, os
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = sys.argv[1]

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
        nav = header.find("nav", class_="cip-nav")
        if nav is None:
            skipped.append((p, "no cip-nav (gia' rimossa?)"))
            continue

        # rimuove l'intero contenitore destro (spacer + nav), non solo il nav
        wrapper = nav.find_parent("div", class_="is-content-justification-right")
        target = wrapper if wrapper is not None else nav
        target.decompose()

        with open(p, "w", encoding="utf-8") as f:
            f.write(str(soup))
        changed += 1

print("Pagine aggiornate: %d" % changed)
if skipped:
    print("Saltate (%d):" % len(skipped))
    for p, why in skipped:
        print("  ", p, "->", why)
