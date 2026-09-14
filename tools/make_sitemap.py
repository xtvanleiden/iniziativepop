# -*- coding: utf-8 -*-
"""
Genera sitemap.xml e robots.txt per il nuovo dominio, a partire dalle
pagine HTML effettivamente presenti nel mirror.

Uso: python tools/make_sitemap.py site [https://iniziativepop.it]
"""
import sys, io, os
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = sys.argv[1]
SITE = (sys.argv[2] if len(sys.argv) > 2 else "https://iniziativepop.it").rstrip("/")

urls = []
for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if fn != "index.html":
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        path = "/" if rel == "index.html" else "/" + rel[: -len("index.html")]
        lastmod = datetime.fromtimestamp(os.path.getmtime(full), timezone.utc)
        urls.append((path, lastmod))

urls.sort(key=lambda x: (x[0] != "/", x[0]))

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, lastmod in urls:
    prio = "1.0" if path == "/" else ("0.8" if path.count("/") <= 2 else "0.6")
    lines.append("  <url>")
    lines.append("    <loc>%s%s</loc>" % (SITE, path))
    lines.append("    <lastmod>%s</lastmod>" % lastmod.strftime("%Y-%m-%d"))
    lines.append("    <priority>%s</priority>" % prio)
    lines.append("  </url>")
lines.append("</urlset>")

with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

robots = """Sitemap: %s/sitemap.xml

User-agent: *
Allow: /
""" % SITE
with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(robots)

print("sitemap.xml generata con %d URL" % len(urls))
print("robots.txt riscritta (rimossi i Disallow WooCommerce/wp-admin, non piu' pertinenti)")
