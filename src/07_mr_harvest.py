"""Harvest 2022 sitemap URL lists for the Marathi outlets of the Belagavi check (URLs + lastmod only).

Re-uses harvest() / parse_urlset() from 02_harvest_sitemaps.py unchanged; new tags only, so no existing
raw/sitemaps/*_2022.csv file is touched:
  pu  Pudhari (pudhari.news, Quintype daily sitemaps sitemap/sitemap-daily-YYYY-MM-DD.xml)
  sk  Sakal (www.esakal.com, Quintype daily sitemaps)
  tb  Tarun Bharat (www.tarunbharat.com, WordPress post-sitemapN.xml, ascending by date, 100 posts each;
      N = 940-1380 brackets 2022 - probed 2026-11-09: #950 = 2021-12-29..2022-01-04, #1350 = 2022-12-17..19,
      #1400 = 2023-02-05; 2022 is later selected on <lastmod>, as for Public TV)
  t9  TV9 Marathi (monthly post sitemaps), bl  Belgaum Live (all WordPress post-sitemaps)
Usage: python -I src/07_mr_harvest.py [pu|sk|tb|t9|bl ...]
"""
import importlib.util
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("harv02", HERE / "02_harvest_sitemaps.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
ROOT_MR = HERE.parent / "raw" / "mr_probe"  # sitemap-index URL lists saved by the probe

JOBS = {
    "pu": [(d.isoformat(), f"https://pudhari.news/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in H.days()],
    "sk": [(d.isoformat(), f"https://www.esakal.com/sitemap/sitemap-daily-{d.isoformat()}.xml") for d in H.days()],
    "tb": [(f"post-sitemap{n}", f"https://www.tarunbharat.com/post-sitemap{n}.xml") for n in range(940, 1381)],
    # TV9 Marathi: monthly post sitemaps sitemap/post-2022-<month>-<k>.xml (48, listed in sitemap_index.xml)
    "t9": [(u.rsplit("/", 1)[-1][5:-4], u) for u in
           (ROOT_MR / "tv9marathi_index_2022_posts.txt").read_text().split()],
    # Belgaum Live (WordPress, dated /YYYY/MM/ URLs, post-sitemaps ordered by lastmod so 2022 posts are scattered):
    # all 147 post-sitemaps; 2022 selected later on the URL date
    "bl": [(u.rsplit("/", 1)[-1][:-4], u) for u in (ROOT_MR / "belgaumlive_index_posts.txt").read_text().split()],
}
EXISTING = {"dh", "pv", "uv", "vv", "kp", "nie", "an", "ptv", "toi"}
assert not EXISTING & set(JOBS)

if __name__ == "__main__":
    tags = sys.argv[1:] or list(JOBS)
    th = [threading.Thread(target=H.harvest, args=(t, JOBS[t])) for t in tags]
    for t in th:
        t.start()
    for t in th:
        t.join()
