# -*- coding: utf-8 -*-
"""Verifica che ogni riferimento locale nelle pagine HTML punti a un file esistente."""
import os, sys, posixpath
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

ROOT = sys.argv[1]
missing = {}
checked = 0
ext_hosts = {}

ATTRS = ("src", "href", "data-src", "poster", "data")

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(dirpath, fn)
        page_rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        with open(p, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")
        refs = []
        for el in soup.find_all(True):
            for a in ATTRS:
                v = el.get(a)
                if v:
                    refs.append(v)
            for a in ("srcset", "imagesrcset", "data-srcset"):
                v = el.get(a)
                if v:
                    refs += [i.strip().split()[0] for i in v.split(",") if i.strip()]
        for v in refs:
            if not isinstance(v, str):
                continue
            v = v.strip()
            if not v or v.startswith(("data:", "#", "javascript:", "mailto:", "tel:", "//")):
                continue
            pr = urlparse(v)
            if pr.scheme in ("http", "https"):
                ext_hosts[pr.netloc] = ext_hosts.get(pr.netloc, 0) + 1
                continue
            checked += 1
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page_rel), unquote(pr.path)))
            full = os.path.join(ROOT, target.replace("/", os.sep))
            if not os.path.exists(full):
                missing.setdefault(target, []).append(page_rel)

print("Riferimenti locali controllati: %d" % checked)
print("MANCANTI: %d" % len(missing))
for t, pgs in sorted(missing.items())[:40]:
    print("  %-70s (in %d pagine)" % (t, len(pgs)))
print("\nHost esterni ancora referenziati:")
for h, n in sorted(ext_hosts.items(), key=lambda x: -x[1]):
    print("  %-40s %d" % (h, n))
