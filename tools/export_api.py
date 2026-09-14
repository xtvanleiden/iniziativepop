# -*- coding: utf-8 -*-
"""Esporta contenuti pubblici via WP REST API in export/"""
import os, sys, json, time
import requests

BASE = "https://comitatoiniziativepopolari.it/wp-json"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 SiteMirror/1.0"})


def get_all(endpoint):
    items, page = [], 1
    while True:
        url = "%s/wp/v2/%s?per_page=100&page=%d&_embed=1" % (BASE, endpoint, page)
        r = S.get(url, timeout=60)
        if r.status_code != 200:
            break
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        items += batch
        total_pages = int(r.headers.get("X-WP-TotalPages", "1") or 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.2)
    return items


summary = {}
for ep in ("pages", "posts", "media", "categories", "tags", "users", "comments", "types", "taxonomies"):
    try:
        data = get_all(ep)
    except Exception as e:
        print("ERR %s: %r" % (ep, e))
        continue
    with open(os.path.join(OUT, ep + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    summary[ep] = len(data)
    print("%-12s %d" % (ep, len(data)))

# root discovery + site info
for name, url in (("wp-json-root", BASE + "/"),
                  ("site-settings", BASE + "/wp/v2/settings"),
                  ("wp-block-templates", BASE + "/wp/v2/templates"),
                  ("theme", BASE + "/wp/v2/themes")):
    try:
        r = S.get(url, timeout=60)
        if r.status_code == 200:
            with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
                json.dump(r.json(), f, indent=2, ensure_ascii=False)
            print("%-12s ok" % name)
        else:
            print("%-12s HTTP %d (richiede login)" % (name, r.status_code))
    except Exception as e:
        print("%-12s ERR %r" % (name, e))

with open(os.path.join(OUT, "_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("\nExport API completato")
