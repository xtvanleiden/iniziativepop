# -*- coding: utf-8 -*-
"""
Sostituisce tutte le varianti del logo del sito con una nuova immagine
sorgente, ridimensionandola esattamente alle stesse dimensioni pixel dei
file esistenti e salvando negli stessi percorsi/nomi — cosi' non serve
toccare nessun riferimento nell'HTML (src, srcset, og:image, apple-touch-
icon, ecc. restano tutti validi).

Uso: python tools/replace_logo.py site loghi/logo_stelline.png
"""
import sys, io, os, glob
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = sys.argv[1]
SOURCE = sys.argv[2]

TARGETS = sorted(
    glob.glob(os.path.join(ROOT, "wp-content", "uploads", "2025", "06", "*logo*")) +
    glob.glob(os.path.join(ROOT, "_ext", "i0.wp.com", "**", "logo__*.jpeg"), recursive=True)
)

if not TARGETS:
    print("ERRORE: nessun file logo trovato in", ROOT)
    sys.exit(1)

master = Image.open(SOURCE).convert("RGB")
print("Sorgente: %s (%dx%d)" % (SOURCE, master.width, master.height))

done = 0
for path in TARGETS:
    with Image.open(path) as existing:
        w, h = existing.size
        fmt = existing.format  # JPEG per tutti i file attuali

    resized = master.resize((w, h), Image.LANCZOS)
    resized.save(path, format=fmt or "JPEG", quality=90, optimize=True)
    print("  %-90s -> %dx%d" % (path, w, h))
    done += 1

print("\nSostituiti %d file logo." % done)
