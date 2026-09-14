# -*- coding: utf-8 -*-
"""Scarica TUTTA la media library (originali + tutte le dimensioni) in site/wp-content/uploads/"""
import os, sys, json, time
from urllib.parse import urlparse, unquote
import requests

OUT = sys.argv[1]          # cartella site/
EXPORT = sys.argv[2]       # cartella export/
OLD_HOST = "comitatoiniziativepopolari.it"

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 SiteMirror/1.0"})

media = json.load(open(os.path.join(EXPORT, "media.json"), encoding="utf-8"))

urls = set()
for m in media:
    su = m.get("source_url")
    if su:
        urls.add(su)
    sizes = (m.get("media_details") or {}).get("sizes") or {}
    for s in sizes.values():
        if s.get("source_url"):
            urls.add(s["source_url"])

ok = skipped = fail = 0
failed = []
for u in sorted(urls):
    pr = urlparse(u)
    if pr.netloc.lower().replace("www.", "") != OLD_HOST:
        # es. i0.wp.com -> riporta al path originale
        continue
    rel = unquote(pr.path).lstrip("/")
    full = os.path.join(OUT, rel.replace("/", os.sep))
    if os.path.exists(full) and os.path.getsize(full) > 0:
        skipped += 1
        continue
    try:
        r = S.get(u, timeout=90)
        if r.status_code != 200:
            fail += 1
            failed.append(u + " HTTP " + str(r.status_code))
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(r.content)
        ok += 1
        print("  + %s (%d KB)" % (rel, len(r.content) // 1024), flush=True)
    except Exception as e:
        fail += 1
        failed.append(u + " " + repr(e))
    time.sleep(0.1)

print("\nMedia: %d scaricati, %d gia presenti, %d falliti" % (ok, skipped, fail))
for f in failed:
    print("  FAIL", f)
