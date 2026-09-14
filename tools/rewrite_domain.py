# -*- coding: utf-8 -*-
"""Sostituisce ogni riferimento residuo al vecchio dominio con quello nuovo."""
import os, sys, re

ROOT = sys.argv[1]
OLD = "comitatoiniziativepopolari.it"
NEW = "iniziativepop.it"

TEXT_EXT = (".html", ".htm", ".css", ".js", ".json", ".xml", ".txt", ".svg", ".webmanifest")

# 1. rinomina le cartelle che contengono il vecchio dominio nel nome
#    (es. _ext/i0.wp.com/comitatoiniziativepopolari.it -> .../iniziativepop.it)
#    dal piu' profondo al piu' superficiale, per non invalidare i path
for dirpath, dirnames, _ in os.walk(ROOT, topdown=False):
    for d in dirnames:
        if OLD in d:
            src = os.path.join(dirpath, d)
            dst = os.path.join(dirpath, d.replace(OLD, NEW))
            if os.path.exists(dst):
                print("ATTENZIONE: %s esiste gia', salto" % dst)
                continue
            os.rename(src, dst)
            print("cartella rinominata: %s -> %s" % (d, d.replace(OLD, NEW)))

count_files = 0
count_hits = 0

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if not fn.lower().endswith(TEXT_EXT):
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, "r", encoding="utf-8") as f:
                s = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        orig = s
        n = s.count(OLD)
        if n == 0:
            continue
        # www.old -> new  (prima, per non lasciare www.iniziativepop.it)
        s = s.replace("www." + OLD, NEW)
        s = s.replace(OLD, NEW)
        if s != orig:
            with open(p, "w", encoding="utf-8") as f:
                f.write(s)
            count_files += 1
            count_hits += n

print("Dominio riscritto in %d file (%d occorrenze) -> %s" % (count_files, count_hits, NEW))
