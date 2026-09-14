# -*- coding: utf-8 -*-
"""
Appiattisce la voce "Le Proposte" del menu header (hamburger su mobile):
oggi e' un menu a tendina che si apre solo con hover/click via JS
(Interactivity API di WordPress), che in un sito statico e' fragile e
sui touchscreen spesso non funziona. La si sostituisce con 3 link sempre
visibili, senza dipendere da JS:

  Le Proposte (-> pagina indice /proposte/)
  Legge elettorale proporzionale con preferenze
  Cancellierato italiano

Si applica solo al nav dentro <header> (quello del menu hamburger), non
a quello nel footer. Va rilanciato su tutte le pagine del mirror.

Uso: python tools/flatten_proposte_menu.py site
"""
import sys, io, os, posixpath
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = sys.argv[1]

changed = 0
skipped = 0

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if fn != "index.html" and fn != "404.html":
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "lxml")

        header = soup.find("header")
        if header is None:
            skipped += 1
            continue
        nav = header.find("nav")
        if nav is None:
            skipped += 1
            continue
        li = nav.find("li", class_="has-child")
        if li is None:
            # gia' appiattito in una run precedente, o struttura diversa
            continue

        sub_ul = li.find("ul", class_="wp-block-navigation-submenu")
        sub_items = sub_ul.find_all("li", recursive=False)
        # {testo: href} dei 2 link attuali (Legge elettorale, Cancellierato)
        pairs = []
        for sli in sub_items:
            a = sli.find("a")
            pairs.append((a.get_text(strip=True), a["href"]))

        # deriva l'href della pagina indice /proposte/ dal primo sotto-link
        # (stesso numero di ".." del resto del menu, calcolato dal path)
        first_href = pairs[0][1]
        proposte_href = posixpath.join(
            posixpath.dirname(posixpath.dirname(first_href)), "index.html"
        )

        # stile dei link piatti (font-size ecc.) preso da un fratello esistente
        container = li.parent
        template_li = None
        for sib in container.find_all("li", recursive=False):
            if sib is not li and "has-child" not in (sib.get("class") or []):
                template_li = sib
                break

        def make_li(text, href):
            new_li = soup.new_tag("li")
            new_li["class"] = list(template_li.get("class") or []) if template_li else \
                ["wp-block-navigation-item", "wp-block-navigation-link"]
            if template_li and template_li.get("style"):
                new_li["style"] = template_li["style"]
            a = soup.new_tag("a", href=href, attrs={"class": "wp-block-navigation-item__content"})
            span = soup.new_tag("span", attrs={"class": "wp-block-navigation-item__label"})
            span.string = text
            a.append(span)
            new_li.append(a)
            return new_li

        new_items = [make_li("Le Proposte", proposte_href)]
        for text, href in pairs:
            new_items.append(make_li(text, href))

        for item in new_items:
            li.insert_before(item)
        li.decompose()

        new_html = str(soup)
        if new_html != html:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new_html)
            changed += 1

print("Pagine modificate: %d | saltate (no header/nav): %d" % (changed, skipped))
