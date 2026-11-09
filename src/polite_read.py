"""Fetch an article politely and return (title, date, text) IN MEMORY ONLY.

Nothing returned here is written to disk by this module; callers print a short
excerpt for manual reading and record only extracted fields.
"""
import html as htmlmod
import json
import re

import polite


def _clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmlmod.unescape(s)).strip()


def _udayavani(h):
    """Udayavani (Next.js): body text is loaded client-side from a CDN host whose robots.txt
    returns 403, so we do NOT fetch it. Use only server-rendered fields of the article page:
    headline, second title (sub-headline), keywords/tags, publishDate. body = 'HEADLINE-ONLY | ...'."""
    i = h.find('newsDetails\\":{')
    seg = h[i:i + 5000].replace('\\"', '"') if i >= 0 else ""
    def f(k):
        m = re.search(r'"' + k + r'":"(.*?)"', seg)
        return _clean(m.group(1)) if m else ""
    title = f("title")
    if not title:
        m = re.search(r"<h1>(.*?)</h1>", h, flags=re.S)
        title = _clean(m.group(1)) if m else None
    date = f("publishDate")[:10] or None
    kw = re.search(r'"keywords":\[(.*?)\]', seg)
    kws = _clean(kw.group(1).replace('"', " ")) if kw else ""
    return title, date, f"HEADLINE-ONLY | {f('secondTitle')} | kw: {kws}"


def read(url):
    r = polite.get(url)
    if r is None:
        return None, None, "ROBOTS_DISALLOWED"
    if not r.ok:
        return None, None, f"HTTP {r.status_code}"
    h = r.text
    if "udayavani.com" in r.url:
        return _udayavani(h)
    title, date, body = None, None, None
    for blob in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, flags=re.S):
        try:
            data = json.loads(blob.strip())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and it.get("@graph"):
                items.extend(it["@graph"])
        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("articleBody") and not body:
                body = _clean(it["articleBody"])
            if it.get("headline") and not title:
                title = _clean(str(it["headline"]))
            if it.get("datePublished") and not date:
                date = str(it["datePublished"])[:10]
    if not title:
        m = re.search(r'<meta property="og:title" content="([^"]*)"', h)
        title = _clean(m.group(1)) if m else None
    if not title:  # og:title with other attribute order (Public TV, Asianet live pages), then <title>
        m = re.search(r'<meta[^>]*og:title[^>]*>', h)
        c = re.search(r'content="([^"]*)"', m.group(0)) if m else None
        title = _clean(c.group(1)) if c else None
    if not title:
        m = re.search(r"<title>(.*?)</title>", h, flags=re.S)
        title = _clean(m.group(1)) if m else None
    if not date:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', h) or \
            re.search(r'article:published_time" content="([^"]+)"', h)
        date = m.group(1)[:10] if m else None
    if not date:
        m = re.search(r'content="([0-9]{4}-[0-9]{2}-[0-9]{2})[^"]*"[^>]*article:published_time', h) or             re.search(r'<time[^>]*datetime="([0-9]{4}-[0-9]{2}-[0-9]{2})', h)
        date = m.group(1) if m else None
    if not body or len(body) < 200:
        ps = [_clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S)]
        ps = [p for p in ps if len(p) > 40]
        body = " ".join(ps)
    return title, date, body
