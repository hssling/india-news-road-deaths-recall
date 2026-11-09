"""Screen Marathi-outlet candidates (Belagavi check): same logic as 04_screen.py, Marathi keywords.

Article text is held in memory only. Persisted per article (data/screen_logs_mr/screen_log_<pass>_<outlet>.csv):
url, outlet, language, pub_date, fetch_status, death_kw, crash_kw, n_chars. Logs live in a sub-folder so that
the data/screen_log*.csv globs of 05_build_outputs.py (DK and Belagavi runs) never see them.
Short sentence-level excerpts for MANUAL reading go to the file named by argv[5] (a temporary scratch file
OUTSIDE the project, deleted after coding) - never into data/.

Usage: KC_DISTRICT=belagavi python -I src/04b_screen_mr.py <outlet substring> <start> <end> <p1|p2> <excerpt file>
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

assert DC.KEY == "belagavi"
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "data" / "screen_logs_mr"
LOGDIR.mkdir(exist_ok=True)
CFILE = {"p1": "candidates_all_belagavi_mr.csv", "p2": "candidates_pass2_screen_belagavi_mr.csv",
         "p2b": "candidates_pass2b_screen_belagavi_mr.csv"}

DEATH = re.compile(r"\bdie[sd]?\b|\bdead\b|\bkilled\b|\bdeath|succumb|"
                   r"ठार|मृत्यू|मृत्यु|मृत|जागीच|गतप्राण|प्राण गमाव|प्राणास मुक|बळी|मरण|दगाव|दगावल|"
                   r"निधन|ठप्प झाल", re.I)
CRASH = re.compile(r"accident|collid|collision|crash|mishap|rammed|hit by|overturn|run over|ran over|skid|"
                   r"अपघात|धडक|धडकल|धडकून|ठोकर|उलट|पलटी|चिरड|घसरून|घसरल|कोसळ|नियंत्रण सुट|"
                   r"दुचाकी|ट्रक|कंटेनर|टेम्पो|ट्रॅक्टर|डंपर|रिक्षा|जीप|क्रुझर", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+", text) if s.strip()]


def main():
    key, a, b, p, exfile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
    assert "meta_press_surveillance" not in str(Path(exfile).resolve()), "excerpts must stay outside the project"
    log = LOGDIR / f"screen_log_{p}_{key.lower().replace(' ', '_')}.csv"
    c = pd.read_csv(ROOT / "data" / CFILE[p])
    c = c[c["outlet"].str.contains(key, case=False)]
    done = set(pd.read_csv(log)["url"]) if log.exists() else set()
    new = not log.exists()
    with open(log, "a", newline="", encoding="utf-8") as fh, open(exfile, "a", encoding="utf-8") as ex:
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
                ex.write(f"STOPPED {e}\n")
                break
            except Exception as e:  # network / TLS error: logged, never bypassed
                w.writerow([r.url, r.outlet, r.language, "", f"ERR {type(e).__name__}", "", "", 0])
                fh.flush()
                ex.write(f"[{a+i}] ERR {type(e).__name__} {r.url}
")
                ex.flush()
                continue
            if title is None:
                st = body if body and (body.startswith("HTTP ") or body == "ROBOTS_DISALLOWED") else "NO_TITLE"
                w.writerow([r.url, r.outlet, r.language, "", st, "", "", 0])
                fh.flush()
                ex.write(f"[{a+i}] {st} {r.url}\n")
                continue
            date = date or str(getattr(r, "sitemap_date", "") or "")[:10]
            body = body or ""
            full = f"{title}. {body}"
            dk, ck = bool(DEATH.search(full)), bool(CRASH.search(full))
            w.writerow([r.url, r.outlet, r.language, date, "ok", dk, ck, len(body)])
            fh.flush()
            if not (dk and ck):
                ex.write(f"[{a+i}] {date} NONFATAL/NOCRASH d={int(dk)} c={int(ck)} | {title[:110]}\n")
                continue
            hits = [s for s in sentences(body) if DEATH.search(s) or CRASH.search(s)]
            lim = 6 if r.why == "roundup" else 3
            exs = " || ".join(h[:260] for h in hits[:lim])
            ex.write(f"[{a+i}] {date}\n   T: {title[:150]}\n   X: {exs}\n")
            ex.flush()
    print("done", key, p, a, b, polite.request_counts())


if __name__ == "__main__":
    main()
