# -*- coding: utf-8 -*-
"""
Sostituisce il modulo di ricerca della pagina 404 (inerte in un sito statico)
con dei link alle sezioni principali.

Uso: python tools/fix_404.py site
"""
import sys, io, os
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = sys.argv[1]
PAGE = os.path.join(ROOT, "404.html")

LINKS = [
    ("Home page", "index.html"),
    ("Le proposte", "proposte/"),
    ("Iscriviti al Comitato", "iscrizione/"),
    ("Lo statuto", "statuto/"),
    ("Stampa ed eventi", "stampa-eventi/"),
    ("Contattaci", "mettiti-in-contatto-con-noi/"),
]

with open(PAGE, encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

removed = 0
for form in soup.find_all("form"):
    cls = " ".join(form.get("class") or [])
    if "search" in cls or form.find("input", {"type": "search"}):
        wrap = form.find_parent(class_=lambda c: c and "wp-block-search" in " ".join(c))
        (wrap or form).decompose()
        removed += 1

# togli anche la frase che invitava a cercare
for p in soup.find_all("p"):
    if "usando il modulo qui sotto" in p.get_text():
        p.string = "Da qui puoi raggiungere le sezioni principali del sito."
        break

nav = soup.new_tag("nav", attrs={
    "aria-label": "Sezioni principali",
    "style": ("display:flex;flex-wrap:wrap;gap:12px;justify-content:center;"
              "margin:28px auto;max-width:720px;padding:0 16px"),
})
for label, href in LINKS:
    a = soup.new_tag("a", href=href, attrs={
        "style": ("display:inline-block;padding:10px 20px;border:2px solid #146894;"
                  "border-radius:50px;color:#146894;text-decoration:none;font-weight:600"),
    })
    a.string = label
    nav.append(a)

anchor = None
for p in soup.find_all("p"):
    if "sezioni principali del sito" in p.get_text():
        anchor = p
        break
if anchor is None:
    anchor = soup.find("h1") or (soup.find("main") or soup.body)
anchor.insert_after(nav)

with open(PAGE, "w", encoding="utf-8") as f:
    f.write(str(soup))

print("404.html aggiornata: %d moduli di ricerca rimossi, %d link aggiunti"
      % (removed, len(LINKS)))
