"""Harvest 2022 sitemap URL lists (URLs + sitemap date only; no article text).

DH and Prajavani (Quintype platform): one daily sitemap per day.
Udayavani: monthly sitemaps kan/MM-YYYY.xml (Kannada) and eng/MM-YYYY.xml if listed in english.xml.
Added for the Belagavi check (same Quintype daily layout): Vijayavani (vv), Kannada Prabha (kp),
The New Indian Express (nie); Asianet Suvarna News Kannada (an) daily sitemaps /sitemap/YYYY/MM/DD/sitemap.xml.gz.
Sitemaps are state-wide (not per district), so one harvest serves every district.
Each site runs in its own thread; polite.py enforces >=2 s per host and robots.txt.
Usage: python -I src/02_harvest_sitemaps.py [dh|pv|uv|vv|kp|nie|an|ptv ...]
"""
import csv
import datetime as dt
import gzip
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polite  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "sitemaps"
OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2022
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(\S+?)\s*(?:\]\]>)?\s*</loc>")
LASTMOD = re.compile(r"<lastmod>\s*(?:<!\[CDATA\[)?\s*(\S+?)\s*(?:\]\]>)?\s*</lastmod>")


def days():
    d = dt.date(YEAR, 1, 1)
    while d.year == YEAR:
        yield d
        d += dt.timedelta(days=1)


def parse_urlset(xml):
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, flags=re.S):
        m = LOC.search(block)
        lm = LASTMOD.search(block)
        if m:
            out.append((m.group(1), lm.group(1) if lm else ""))
    return out


def harvest(tag, jobs):
    f = OUT / f"{tag}_{YEAR}.csv"
    log = OUT / f"{tag}_{YEAR}_log.csv"
    n = 0
    with open(f, "w", newline="", encoding="utf-8") as fh, open(log, "w", newline="", encoding="utf-8") as lh:
        w = csv.writer(fh)
        lw = csv.writer(lh)
        w.writerow(["sitemap", "sitemap_date", "url", "lastmod"])
        lw.writerow(["sitemap", "status", "n_urls"])
        for label, url in jobs:
            try:
                r = polite.get(url)
            except polite.SiteStopped as e:
                lw.writerow([url, f"STOPPED {e}", 0])
                print(tag, "STOPPED", e, flush=True)
                break
            except Exception as e:  # network error: log and continue
                lw.writerow([url, f"ERR {type(e).__name__}", 0])
                continue
            if r is None:
                lw.writerow([url, "ROBOTS_DISALLOWED", 0])
                continue
            txt = r.text
            if r.ok and r.content[:2] == bytes([0x1F, 0x8B]):  # raw gzip body (no Content-Encoding)
                txt = gzip.decompress(r.content).decode("utf-8", "replace")
            items = parse_urlset(txt) if r.ok else []
            lw.writerow([url, r.status_code, len(items)])
            for u, lm in items:
                w.writerow([url, label, u, lm])
            n += len(items)
            fh.flush()
            lh.flush()
    print(tag, "done", n, "urls", polite.request_counts(), flush=True)


JOBS = {
    "dh": [(d.isoformat(), f"https://www.deccanherald.com/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in days()],
    "pv": [(d.isoformat(), f"https://www.prajavani.net/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in days()],
    "uv": [(f"{YEAR}-{m:02d}", f"https://udayavani.com/kan/{m:02d}-{YEAR}.xml") for m in range(1, 13)]
          + [(f"{YEAR}-{m:02d}-eng", f"https://udayavani.com/eng/{m:02d}-{YEAR}.xml") for m in range(1, 13)],
    "vv": [(d.isoformat(), f"https://www.vijayavani.net/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in days()],
    "kp": [(d.isoformat(), f"https://www.kannadaprabha.com/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in days()],
    "nie": [(d.isoformat(), f"https://www.newindianexpress.com/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in days()],
    "an": [(d.isoformat(), f"https://kannada.asianetnews.com/sitemap/{YEAR}/{d.month:02d}/{d.day:02d}/sitemap.xml.gz")
           for d in days()],
    # Public TV (WordPress, undated URLs): post-sitemaps are reverse-chronological, ~2,100 posts each;
    # numbers 38-58 bracket 2022 (probed 2026-11-09). 2022 is selected later on <lastmod> (proxy for pub date).
    "ptv": [(f"post-sitemap{n}", f"https://publictv.in/post-sitemap{n}.xml") for n in range(38, 59)],
    # Times of India city-section monthly sitemaps (3 parts per month in 2022)
    "toi": [(f"{YEAR}-{mn}-{k}", f"https://timesofindia.indiatimes.com/staticsitemap/toi/category/city/{YEAR}-{mn}-{k}.xml")
            for mn in ["January", "February", "March", "April", "May", "June", "July", "August",
                       "September", "October", "November", "December"] for k in (1, 2, 3, 4)],
}

if __name__ == "__main__":
    tags = sys.argv[1:] or list(JOBS)
    th = [threading.Thread(target=harvest, args=(t, JOBS[t])) for t in tags]
    for t in th:
        t.start()
    for t in th:
        t.join()
