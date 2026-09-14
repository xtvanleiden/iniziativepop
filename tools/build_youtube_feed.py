# -*- coding: utf-8 -*-
"""
Sostituisce nella home page il blocco a due colonne (Cancellierato Italiano /
Legge Elettorale Proporzionale, titolo + descrizione) con una fascia che
mostra gli ultimi video del canale YouTube del Comitato, che scorrono
automaticamente in orizzontale (nessuna API key richiesta: si usa il feed
RSS pubblico di YouTube).

Uso: python tools/build_youtube_feed.py site [https://www.youtube.com/@iniziativepop]
"""
import sys, io, os, re, time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = sys.argv[1]
CHANNEL_URL = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com/@iniziativepop"
FALLBACK_CHANNEL_ID = "UCsxjaL_fHq2v56TSZxVV-hg"  # usato solo se la risoluzione fallisce
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MAX_VIDEOS = 12


def http_get(url):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def resolve_channel_id(channel_url):
    try:
        html = http_get(channel_url)
        m = re.search(r'canonical"\s+href="https://www\.youtube\.com/channel/(UC[\w-]+)"', html)
        if m:
            return m.group(1)
    except Exception as e:
        print("  attenzione: risoluzione channel id fallita (%r), uso fallback" % e)
    return FALLBACK_CHANNEL_ID


def fetch_videos(channel_id):
    xml_text = http_get("https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id)
    ns = {"a": "http://www.w3.org/2005/Atom",
          "yt": "http://www.youtube.com/xml/schemas/2015",
          "media": "http://search.yahoo.com/mrss/"}
    root = ET.fromstring(xml_text)
    videos = []
    for entry in root.findall("a:entry", ns)[:MAX_VIDEOS]:
        vid = entry.find("yt:videoId", ns).text
        title = entry.find("a:title", ns).text
        published = entry.find("a:published", ns).text[:10]
        group = entry.find("media:group", ns)
        thumb = group.find("media:thumbnail", ns).get("url")
        videos.append({"id": vid, "title": title, "date": published, "thumb": thumb})
    return videos


def month_it(iso_date):
    mesi = ["gen", "feb", "mar", "apr", "mag", "giu",
            "lug", "ago", "set", "ott", "nov", "dic"]
    y, m, d = iso_date.split("-")
    return "%d %s %s" % (int(d), mesi[int(m) - 1], y)


def build_section(soup, videos, channel_url):
    section = soup.new_tag("section", attrs={
        "class": "cip-yt-feed", "aria-label": "Ultimi video dal canale YouTube",
        "style": "padding:56px 24px;background:#f4f8fa",
    })

    heading = soup.new_tag("h2", attrs={
        "style": ("text-align:center;color:#146894;font-size:clamp(23px,1.4rem + 1vw,38px);"
                   "margin:0 0 8px"),
    })
    heading.string = "Ultimi video dal canale"
    section.append(heading)

    sub = soup.new_tag("p", attrs={
        "style": "text-align:center;color:#3a5a68;margin:0 0 32px;font-size:1rem",
    })
    sub.string = "Gli aggiornamenti del Comitato Iniziative Popolari, in diretta dal nostro canale YouTube."
    section.append(sub)

    wrap = soup.new_tag("div", attrs={"class": "cip-yt-track-wrap"})
    track = soup.new_tag("div", attrs={"class": "cip-yt-track"})

    def add_cards():
        for v in videos:
            card = soup.new_tag("a", href="https://www.youtube.com/watch?v=" + v["id"],
                                 target="_blank", rel="noopener noreferrer",
                                 attrs={"class": "cip-yt-card"})
            img = soup.new_tag("img", src=v["thumb"], alt=v["title"], loading="lazy")
            card.append(img)
            body = soup.new_tag("span", attrs={"class": "cip-yt-card-body"})
            t = soup.new_tag("span", attrs={"class": "cip-yt-card-title"})
            t.string = v["title"]
            d = soup.new_tag("span", attrs={"class": "cip-yt-card-date"})
            d.string = month_it(v["date"])
            body.append(t)
            body.append(d)
            card.append(body)
            track.append(card)

    add_cards()  # prima copia
    add_cards()  # seconda copia identica, per il loop continuo senza scatti

    wrap.append(track)
    section.append(wrap)

    cta = soup.new_tag("a", href=channel_url, target="_blank", rel="noopener noreferrer",
                        attrs={"class": "cip-yt-cta"})
    cta.string = "Vai al canale YouTube →"
    cta_wrap = soup.new_tag("p", attrs={"style": "text-align:center;margin:28px 0 0"})
    cta_wrap.append(cta)
    section.append(cta_wrap)

    style = soup.new_tag("style")
    style.string = """
.cip-yt-feed { overflow: hidden; }
.cip-yt-track-wrap { overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; }
.cip-yt-track {
  display: flex; gap: 20px; width: max-content;
  animation: cip-yt-scroll 60s linear infinite;
}
.cip-yt-track-wrap:hover .cip-yt-track,
.cip-yt-track-wrap:focus-within .cip-yt-track { animation-play-state: paused; }
@keyframes cip-yt-scroll {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
.cip-yt-card {
  flex: 0 0 260px; display: block; text-decoration: none; color: inherit;
  border-radius: 14px; overflow: hidden; background: #fff;
  box-shadow: 0 1px 4px rgba(20,104,148,.15); transition: box-shadow .2s, transform .2s;
}
.cip-yt-card:hover, .cip-yt-card:focus-visible {
  box-shadow: 0 6px 18px rgba(20,104,148,.28); transform: translateY(-2px);
}
.cip-yt-card img { display: block; width: 100%; height: 146px; object-fit: cover; background: #dce8ed; }
.cip-yt-card-body { display: block; padding: 12px 14px 16px; }
.cip-yt-card-title {
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; font-weight: 600; font-size: .92rem; line-height: 1.35;
  color: #12374a; min-height: 2.6em;
}
.cip-yt-card-date { display: block; margin-top: 6px; font-size: .78rem; color: #6c8a96; }
.cip-yt-cta {
  display: inline-block; padding: 10px 22px; border: 2px solid #146894; border-radius: 50px;
  color: #146894; text-decoration: none; font-weight: 600;
}
.cip-yt-cta:hover { background: #146894; color: #fff; }
@media (prefers-reduced-motion: reduce) {
  .cip-yt-track { animation: none; }
}
@media (max-width: 480px) {
  .cip-yt-card { flex-basis: 210px; }
  .cip-yt-card img { height: 118px; }
}
"""
    section.append(style)
    return section


def main():
    print("Risoluzione channel id per %s ..." % CHANNEL_URL)
    channel_id = resolve_channel_id(CHANNEL_URL)
    print("  channel id:", channel_id)
    print("Recupero video dal feed RSS...")
    videos = fetch_videos(channel_id)
    print("  video trovati:", len(videos))
    if not videos:
        print("ERRORE: nessun video trovato, home non modificata")
        return 1

    page = os.path.join(ROOT, "index.html")
    with open(page, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    h2s = [h for h in soup.find_all("h2") if "Cancellierato" in h.get_text()]
    if not h2s:
        print("ERRORE: sezione 'Cancellierato Italiano / Legge Elettorale' non trovata "
              "(la home e' gia' stata modificata?)")
        return 1
    cols = h2s[0].find_parent("div", class_="wp-block-columns")
    if cols is None:
        print("ERRORE: contenitore wp-block-columns non trovato")
        return 1

    new_section = build_section(soup, videos, CHANNEL_URL)
    cols.replace_with(new_section)

    with open(page, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print("Home aggiornata: sezione proposte sostituita con il feed di %d video." % len(videos))
    return 0


sys.exit(main())
