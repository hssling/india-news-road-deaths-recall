"""Fetch candidate articles politely and print short excerpts for MANUAL reading.

Article text is held in memory only. Persisted per article (data/screen_log.csv):
url, outlet, language, pub_date, fetch_status, death_kw (bool), crash_kw (bool), n_chars.
The analyst reads the printed excerpt and codes crashes by hand in data/killcheck_coding.csv.

Usage: python -I src/04_screen.py <outlet substring> <start> <end> [why] [candidate file]
District-parameterised via KC_DISTRICT: for a non-DK district the default candidate file is
candidates_all_<district>.csv and every log is screen_log_<district>_<outlet>.csv
(pass 2: screen_log_<candidate file stem>_<outlet>.csv, stem already carries the suffix).
"""
import csv
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polite  # noqa: E402
import polite_read  # noqa: E402
import district_cfg as DC  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "screen_log.csv"

DEATH = re.compile(r"\bdie[sd]?\b|\bdead\b|\bkilled\b|\bdeath|succumb|lost (his|her|their) li|breathed his last|"
                   r"ಮೃತ|ಸಾವ|ಸಾವು|ಸಾವಿಗೀಡ|ಕೊನೆಯುಸಿರೆಳೆ|ಬಲಿ|ದುರ್ಮರಣ|ಮರಣ|ಪ್ರಾಣ ಕಳೆದುಕೊಂಡ|ಅಸುನೀಗಿ|ಅಸುನೀಗ", re.I)
CRASH = re.compile(r"accident|collid|collision|crash|mishap|rammed|hit by|knocked|overturn|run over|ran over|"
                   r"skid|lost control|ಅಪಘಾತ|ಢಿಕ್ಕಿ|ಡಿಕ್ಕಿ|ಢಿಕ್ಕಿ|ಉರುಳಿ|ಪಲ್ಟಿ|ಹರಿದು|ಬಿದ್ದು|ಸ್ಕಿಡ್", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+", text) if s.strip()]


def main():
    global LOG
    key, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    okey = key.lower().replace(' ', '_')
    if DC.KEY != "dk":
        LOG = ROOT / "data" / f"screen_log{DC.SUFFIX}_{okey}.csv"
    elif key.lower() != "udayavani":  # separate log per outlet so parallel runs never interleave
        LOG = ROOT / "data" / f"screen_log_{okey}.csv"
    why = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
    default_c = DC.fname("candidates_all")
    cfile = sys.argv[5] if len(sys.argv) > 5 else default_c
    if cfile != default_c:
        LOG = ROOT / "data" / f"screen_log_{Path(cfile).stem}_{key.lower().replace(' ', '_')}.csv"
    c = pd.read_csv(ROOT / "data" / cfile)
    c = c[c["outlet"].str.contains(key, case=False)]
    if why:
        c = c[c["why"] == why]
    done = set(pd.read_csv(LOG)["url"]) if LOG.exists() else set()
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["url", "outlet", "language", "pub_date", "fetch_status", "death_kw", "crash_kw", "n_chars"])
        for i, r in enumerate(c.iloc[a:b].itertuples()):
            if r.url in done:
                continue
            try:
                title, date, body = polite_read.read(r.url)
            except polite.SiteStopped as e:
                print("STOPPED", e)
                break
            except Exception as e:
                w.writerow([r.url, r.outlet, r.language, "", f"ERR {type(e).__name__}", "", "", 0])
                continue
            if title is None:
                # status only: never persist page text (a page with no headline returns body text here)
                st = body if body and (body.startswith("HTTP ") or body == "ROBOTS_DISALLOWED") else "NO_TITLE"
                w.writerow([r.url, r.outlet, r.language, "", st, "", "", 0])
                print(f"[{a+i}] {st} {r.url}")
                continue
            date = date or str(getattr(r, "sitemap_date", "") or "")[:10]  # undated pages: sitemap date
            body = body or ""
            full = f"{title}. {body}"
            dk, ck = bool(DEATH.search(full)), bool(CRASH.search(full))
            w.writerow([r.url, r.outlet, r.language, date, "ok", dk, ck, len(body)])
            fh.flush()
            slug = r.url.split("/")[-1][:70]
            if body.startswith("HEADLINE-ONLY"):
                print(f"[{a+i}] {date} {r.language[:2]} d={int(dk)} c={int(ck)} | {title[:140]} | {body[16:220]}")
                continue
            if not (dk and ck):
                print(f"[{a+i}] {date} NONFATAL/NOCRASH d={int(dk)} c={int(ck)} | {title[:110]}")
                continue
            hits = [s for s in sentences(body) if DEATH.search(s) or CRASH.search(s)]
            lim = 6 if r.why == "roundup" else 3
            ex = " || ".join(h[:260] for h in hits[:lim])
            print(f"[{a+i}] {date} {r.language[:2]} {slug}\n   T: {title[:150]}\n   X: {ex}")


if __name__ == "__main__":
    main()
