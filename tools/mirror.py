# -*- coding: utf-8 -*-
"""Mirror statico di comitatoiniziativepopolari.it -> cartella site/"""
import os, re, sys, time, hashlib, json, posixpath
from urllib.parse import urljoin, urlparse, urldefrag, unquote
import requests
from bs4 import BeautifulSoup

OLD_HOST = "comitatoiniziativepopolari.it"
BASE = "https://" + OLD_HOST + "/"
OUT = sys.argv[1]
EXT_DIR = "_ext"

# host esterni di cui scarichiamo gli asset in locale
EXT_ALLOW = {
    "i0.wp.com", "i1.wp.com", "i2.wp.com", "i3.wp.com",
    "c0.wp.com", "c1.wp.com", "c2.wp.com",
    "s.w.org", "fonts.googleapis.com", "fonts.gstatic.com",
    "secure.gravatar.com", "0.gravatar.com", "1.gravatar.com", "2.gravatar.com",
}
ASSET_EXT = re.compile(r"\.(css|js|png|jpe?g|gif|svg|webp|avif|ico|woff2?|ttf|eot|otf|pdf|mp4|webm|mp3|zip|docx?|xlsx?|json|txt|xml)$", re.I)

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SiteMirror/1.0"})

pages = {}
assets = {}
queue_pages = []
seen_pages = set()
seen_assets = set()
failed = []


def norm(u):
    u, _ = urldefrag(u)
    u = u.strip()
    # refuso presente nel contenuto originale: alcuni link finiscono con ')'
    # (es. ".../cassazione/)/"). Si toglie solo se non c'e' una '(' ad aprirla.
    while u.endswith(")") and "(" not in u:
        u = u[:-1]
    return u


def is_old(u):
    return urlparse(u).netloc.lower().replace("www.", "") == OLD_HOST


def local_page_path(u):
    p = unquote(urlparse(u).path)
    if p in ("", "/"):
        return "index.html"
    p = p.strip("/")
    if p.lower().endswith((".html", ".htm")):
        return p
    return p + "/index.html"


def safe_seg(s):
    return re.sub(r'[<>:"|?*\\]', "_", s)


def local_asset_path(u):
    pr = urlparse(u)
    path = unquote(pr.path).lstrip("/")
    if not path:
        path = "index"
    if is_old(u):
        rel = path
    else:
        rel = posixpath.join(EXT_DIR, pr.netloc, path)
        if pr.query:
            h = hashlib.md5(pr.query.encode()).hexdigest()[:8]
            root, ext = posixpath.splitext(rel)
            rel = root + "__" + h + ext
    if not posixpath.splitext(rel)[1]:
        rel += ".css" if "fonts.googleapis" in pr.netloc else ".bin"
    return "/".join(safe_seg(s) for s in rel.split("/"))


def fetch(u, binary=False):
    for attempt in range(3):
        try:
            r = S.get(u, timeout=45)
            if r.status_code == 200:
                return r
            if r.status_code in (404, 403, 410):
                return None
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def fetch_any(u):
    """come fetch() ma accetta anche una risposta 404 (serve per la pagina 404)"""
    for attempt in range(3):
        try:
            r = S.get(u, timeout=45)
            if r.status_code in (200, 404):
                return r
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def write(rel, data):
    full = os.path.join(OUT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if isinstance(data, bytes):
        with open(full, "wb") as f:
            f.write(data)
    else:
        with open(full, "w", encoding="utf-8") as f:
            f.write(data)


def relpath(from_rel, to_rel):
    d = posixpath.dirname(from_rel)
    r = posixpath.relpath(to_rel, d if d else ".")
    return r.replace("\\", "/")


def want_asset(u):
    pr = urlparse(u)
    if pr.scheme not in ("http", "https"):
        return False
    if is_old(u):
        return True
    return pr.netloc.lower() in EXT_ALLOW


def want_page(u):
    if not is_old(u):
        return False
    pr = urlparse(u)
    # gli URL con query (?replytocom=, ?share=, ?s=, ?add-to-cart=) sono varianti
    # della stessa pagina: in un mirror statico vanno ignorati, altrimenti il
    # crawl entra in un loop di migliaia di duplicati.
    if pr.query:
        return False
    p = pr.path.lower()
    if ASSET_EXT.search(p):
        return False
    skip = ("/wp-admin", "/wp-login", "/wp-json", "/feed", "/xmlrpc",
            "/wp-content", "/wp-includes", "/cart", "/checkout", "/my-account")
    if any(p.startswith(x) for x in skip):
        return False
    if p.endswith("/feed/") or "/comment-page-" in p:
        return False
    return True


def strip_query(u):
    pr = urlparse(norm(u))
    return pr.scheme + "://" + pr.netloc + pr.path


def add_page(u):
    u = strip_query(u)
    if not u.endswith("/") and not ASSET_EXT.search(urlparse(u).path):
        u = u + "/"
    if u in seen_pages or not want_page(u):
        return
    seen_pages.add(u)
    queue_pages.append(u)


CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+(['\"])([^'\"]+)\1", re.I)


def process_css(text, css_url, css_rel, depth=0):
    def repl(m):
        quote, raw = m.group(1), m.group(2)
        if raw.startswith(("data:", "#", "about:")):
            return m.group(0)
        got = download_asset(norm(urljoin(css_url, raw)), depth + 1)
        if not got:
            return m.group(0)
        return "url(" + quote + relpath(css_rel, got) + quote + ")"

    def repl_imp(m):
        q, raw = m.group(1), m.group(2)
        got = download_asset(norm(urljoin(css_url, raw)), depth + 1)
        if not got:
            return m.group(0)
        return "@import " + q + relpath(css_rel, got) + q

    text = CSS_IMPORT.sub(repl_imp, text)
    return CSS_URL.sub(repl, text)


def download_asset(u, depth=0):
    u = norm(u)
    if u in assets:
        return assets[u]
    if not want_asset(u) or depth > 6:
        return None
    rel = local_asset_path(u)
    assets[u] = rel
    # gia' scaricato in una run precedente -> non riscaricare
    full = os.path.join(OUT, rel.replace("/", os.sep))
    if os.path.exists(full) and os.path.getsize(full) > 0:
        return rel
    r = fetch(u)
    if r is None:
        failed.append(u)
        assets.pop(u, None)
        return None
    ctype = r.headers.get("content-type", "").split(";")[0].strip().lower()
    if ctype == "text/css" or rel.endswith(".css"):
        write(rel, process_css(r.text, u, rel, depth))
    else:
        write(rel, r.content)
    print("  asset  " + rel, flush=True)
    return rel


SRCSET_ATTRS = ("srcset", "data-srcset", "imagesrcset")
LINK_ASSET_RELS = {"stylesheet", "icon", "shortcut icon", "apple-touch-icon",
                   "apple-touch-icon-precomposed", "preload", "manifest",
                   "mask-icon", "prefetch", "modulepreload"}
URL_ATTRS = (("img", "src"), ("img", "data-src"), ("script", "src"), ("link", "href"),
             ("source", "src"), ("source", "srcset"), ("video", "src"), ("video", "poster"),
             ("audio", "src"), ("embed", "src"), ("object", "data"), ("input", "src"),
             ("track", "src"))


def process_page(u, force_rel=None, expect_404=False):
    r = fetch(u) if not expect_404 else fetch_any(u)
    if r is None:
        failed.append(u)
        return
    rel = force_rel or local_page_path(u)
    pages[u] = rel
    soup = BeautifulSoup(r.text, "lxml")

    for a in soup.find_all("a", href=True):
        add_page(urljoin(u, a["href"]))

    for tag, attr in URL_ATTRS:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if not v or v.startswith(("data:", "#", "javascript:", "mailto:", "tel:")):
                continue
            if attr in SRCSET_ATTRS:
                continue
            # <link> non-asset (feed, oembed, canonical, shortlink, api.w.org...):
            # non sono file da scaricare, restano URL assoluti -> nuovo dominio
            if tag == "link":
                rels = {r.lower() for r in (el.get("rel") or [])}
                if not rels & LINK_ASSET_RELS:
                    continue
            got = download_asset(norm(urljoin(u, v)))
            if got:
                el[attr] = relpath(rel, got)

    for el in soup.find_all(True):
        for attr in SRCSET_ATTRS:
            v = el.get(attr)
            if not v:
                continue
            parts = []
            for item in v.split(","):
                item = item.strip()
                if not item:
                    continue
                bits = item.split()
                got = download_asset(norm(urljoin(u, bits[0])))
                parts.append(" ".join([relpath(rel, got) if got else bits[0]] + bits[1:]))
            el[attr] = ", ".join(parts)

    for el in soup.find_all(style=True):
        el["style"] = process_css(el["style"], u, rel)
    for st in soup.find_all("style"):
        if st.string:
            st.string.replace_with(process_css(st.string, u, rel))

    for a in soup.find_all("a", href=True):
        absu = norm(urljoin(u, a["href"]))
        sq = strip_query(absu)
        if not sq.endswith("/") and not ASSET_EXT.search(urlparse(sq).path):
            sq += "/"
        if want_page(sq):
            a["href"] = relpath(rel, local_page_path(sq))
        elif is_old(absu):
            got = download_asset(absu)
            if got:
                a["href"] = relpath(rel, got)

    write(rel, str(soup))
    print("PAGE   " + rel, flush=True)


def main():
    seeds = [BASE]
    sm = fetch(BASE + "sitemap-1.xml")
    if sm:
        seeds += re.findall(r"<loc>([^<]+)</loc>", sm.text)
    for s in seeds:
        add_page(s)
    while queue_pages:
        u = queue_pages.pop(0)
        try:
            process_page(u)
        except Exception as e:
            print("  ERR " + u + ": " + repr(e), flush=True)
            failed.append(u)
        time.sleep(0.2)

    ism = fetch(BASE + "image-sitemap-1.xml")
    if ism:
        for m in re.findall(r"<image:loc>([^<]+)</image:loc>|<loc>([^<]+)</loc>", ism.text):
            iu = m[0] or m[1]
            if ASSET_EXT.search(urlparse(iu).path):
                download_asset(norm(iu))

    for extra in ("favicon.ico", "robots.txt"):
        download_asset(BASE + extra)

    # pagina 404 del tema, salvata in root come 404.html
    try:
        process_page(BASE + "pagina-non-esistente-404-generator/",
                     force_rel="404.html", expect_404=True)
    except Exception as e:
        print("  ERR 404: " + repr(e), flush=True)

    report = {"pages": len(pages), "assets": len(assets), "failed": sorted(set(failed))}
    with open(os.path.join(OUT, "..", "_mirror_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nFATTO: %d pagine, %d asset, %d falliti" % (len(pages), len(assets), len(set(failed))))


main()
