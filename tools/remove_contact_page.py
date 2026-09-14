# -*- coding: utf-8 -*-
"""
Rimuove la voce "Contattaci" dal menu (header e footer, su tutte le pagine)
e cancella la pagina /mettiti-in-contatto-con-noi/. Chi vuole contattare il
Comitato usa gli indirizzi email gia' visibili nel footer.

Uso: python tools/remove_contact_page.py site
"""
import sys, io, os, shutil
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = sys.argv[1]
CONTACT_HREF = "mettiti-in-contatto-con-noi"

changed = 0
removed_li = 0
removed_other = 0

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if fn not in ("index.html", "404.html"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            html = f.read()
        if CONTACT_HREF not in html:
            continue
        soup = BeautifulSoup(html, "lxml")

        # 1. voci di menu (li nel nav, sia header che footer)
        for li in soup.find_all("li"):
            a = li.find("a", recursive=False)
            if a and a.get("href") and CONTACT_HREF in a["href"]:
                li.decompose()
                removed_li += 1

        # 2. eventuali link "sciolti" non dentro un <li> di nav
        #    (es. i pulsanti aggiunti nella pagina 404)
        for a in soup.find_all("a", href=True):
            if CONTACT_HREF in a["href"]:
                a.decompose()
                removed_other += 1

        new_html = str(soup)
        if new_html != html:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new_html)
            changed += 1

print("Pagine modificate: %d | voci di menu rimosse: %d | altri link rimossi: %d"
      % (changed, removed_li, removed_other))

# 3. cancella la pagina
contact_dir = os.path.join(ROOT, "mettiti-in-contatto-con-noi")
if os.path.isdir(contact_dir):
    shutil.rmtree(contact_dir)
    print("Cancellata cartella:", contact_dir)
else:
    print("Cartella gia' assente:", contact_dir)

# 4. rimuovi dalla sitemap
sitemap = os.path.join(ROOT, "sitemap.xml")
if os.path.exists(sitemap):
    with open(sitemap, encoding="utf-8") as f:
        sm = f.read()
    lines = sm.split("\n")
    out, skip = [], False
    removed_url = False
    for line in lines:
        if "<url>" in line:
            skip = CONTACT_HREF in "\n".join(lines[lines.index(line):lines.index(line) + 5])
        if CONTACT_HREF in line:
            removed_url = True
        out.append(line)
    # approccio piu' robusto: ricostruzione via regex sul blocco <url>...</url>
    import re
    sm2 = re.sub(
        r"\s*<url>\s*<loc>[^<]*mettiti-in-contatto-con-noi[^<]*</loc>.*?</url>",
        "", sm, flags=re.S,
    )
    if sm2 != sm:
        with open(sitemap, "w", encoding="utf-8") as f:
            f.write(sm2)
        print("Rimossa voce dalla sitemap.xml")
    else:
        print("Nessuna voce da rimuovere nella sitemap.xml")
