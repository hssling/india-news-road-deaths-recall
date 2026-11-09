"""Marathi-outlet probe for the Belagavi check: robots.txt policy + 2022 sitemap/archive existence.

For each candidate host: fetch robots.txt once (research UA, polite rate limit), test whether the
research UA, ClaudeBot, anthropic-ai, GPTBot and '*' may fetch the sitemap / article paths, list the
Sitemap: lines, then (only if every tested agent is allowed) request a few candidate sitemap URLs.
Writes raw/mr_probe/probe_<host>.csv rows (URL, status, size, n <loc>) - no page text is stored.
Usage: python -I src/06_mr_probe.py host1 [host2 ...]
"""
import csv
import re
import sys
import urllib.robotparser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polite  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "mr_probe"
OUT.mkdir(parents=True, exist_ok=True)
AGENTS = [polite.UA, "ClaudeBot", "anthropic-ai", "GPTBot", "*"]
GUESSES = ["/sitemap.xml", "/sitemap_index.xml", "/news-sitemap.xml", "/sitemap/sitemap-daily-2022-06-15.xml",
           "/sitemap-index.xml", "/post-sitemap.xml"]


def raw_get(url):
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    polite._wait(host)
    polite._counts[host] = polite._counts.get(host, 0) + 1
    return polite.SESSION.get(url, timeout=40)


def probe(host, extra):
    base = f"https://{host}"
    rows = []
    try:
        r = raw_get(base + "/robots.txt")
    except Exception as e:  # TLS / network errors are recorded, never bypassed
        print(host, "robots ERR", type(e).__name__, str(e)[:120])
        return [dict(host=host, url=base + "/robots.txt", status=f"ERR {type(e).__name__}", note="")]
    print(host, "robots", r.status_code, len(r.text))
    rp = urllib.robotparser.RobotFileParser()
    if r.status_code in (401, 403):
        rp.disallow_all = True
    elif r.status_code >= 400:
        rp.allow_all = True
    else:
        rp.parse(r.text.splitlines())
    sm = re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", r.text) if r.ok else []
    paths = [base + p for p in GUESSES] + sm + [base + e for e in extra]
    test = [base + "/sitemap.xml", base + "/news/2022/06/15/x"] + sm[:3]
    verdict = {a: all(rp.can_fetch(a, u) for u in test) for a in AGENTS}
    print("  agents allowed:", verdict)
    print("  sitemaps listed:", sm[:15])
    ai = [ln.strip() for ln in r.text.splitlines() if re.search(r"claude|anthropic|gptbot|ai-train|ccbot", ln, re.I)] if r.ok else []
    print("  AI lines:", ai[:12])
    rows.append(dict(host=host, url=base + "/robots.txt", status=r.status_code,
                     note=f"allowed={verdict}; ai_lines={ai[:12]}; sitemaps={sm[:15]}"))
    if not all(verdict.values()):
        print("  -> skipped by policy")
        return rows
    seen = set()
    for u in paths:
        if u in seen:
            continue
        seen.add(u)
        try:
            x = polite.get(u)
        except polite.SiteStopped as e:
            rows.append(dict(host=host, url=u, status=f"STOPPED {e}", note=""))
            print("  STOPPED", e)
            break
        except Exception as e:
            rows.append(dict(host=host, url=u, status=f"ERR {type(e).__name__}", note=""))
            print("  ERR", u, type(e).__name__)
            continue
        if x is None:
            rows.append(dict(host=host, url=u, status="ROBOTS_DISALLOWED", note=""))
            continue
        txt = x.text if x.ok else ""
        locs = re.findall(r"<loc>\s*(?:<!\[CDATA\[)?\s*(\S+?)\s*(?:\]\]>)?\s*</loc>", txt)
        y22 = [l for l in locs if "2022" in l]
        print(f"  {x.status_code} {u} -> {x.url if x.url != u else ''} n_loc={len(locs)} n_2022={len(y22)}")
        print("     first:", locs[:3], "2022 ex:", y22[:4])
        rows.append(dict(host=host, url=u, status=x.status_code,
                         note=f"final={x.url}; n_loc={len(locs)}; n_loc_2022={len(y22)}; ex={locs[:3]}; ex2022={y22[:5]}"))
    return rows


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    for a in args:
        host, *extra = a.split(",")
        rows = probe(host, extra)
        with open(OUT / f"probe_{host}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["host", "url", "status", "note"])
            w.writeheader()
            w.writerows(rows)
