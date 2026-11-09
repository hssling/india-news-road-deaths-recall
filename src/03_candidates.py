"""Build candidate lists from harvested 2022 sitemaps (URL-level screen, no fetching).

Writes data/candidates_all.csv: url, sitemap_date, outlet, language, why
and data/sitemap_screen_counts.csv (URLs screened per outlet).
District-parameterised via KC_DISTRICT (district_cfg.py); non-DK districts write *_<district>.csv and
also screen the outlets added for the Belagavi check (Vijayavani, Kannada Prabha, NIE, Asianet Suvarna).
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filters as F  # noqa: E402
import district_cfg as DC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "raw" / "sitemaps"
NOISE = re.compile(r"covid|positive|corona|temple-car|car-street|car-festival|rathotsava|bus-stand|bus-stop|"
                   r"bus-bay|bus-shelter|bike-theft|bike-rally|car-rally|theft|stolen|gadkari|tender|dpr|"
                   r"inaugurat|foundation-stone|fine|parking|toll|flyover|overbridge|underpass|four-lane|"
                   r"elephant|leopard|wild-boar|drown|suicide|murder|assault|ganja|drug|hijab|"
                   r"election|ipl|cricket|film|movie")

frames, counts = [], []
OUTLETS = [("dh", "Deccan Herald"), ("pv", "Prajavani"), ("uv", "Udayavani"), ("toi", "Times of India")]
if DC.KEY != "dk":
    OUTLETS += [("vv", "Vijayavani"), ("kp", "Kannada Prabha"), ("nie", "New Indian Express"),
                ("an", "Asianet Suvarna"), ("ptv", "Public TV")]
LANG = {"pv": "Kannada", "vv": "Kannada", "kp": "Kannada", "an": "Kannada", "ptv": "Kannada"}
for tag, outlet in OUTLETS:
    f = SM / f"{tag}_2022.csv"
    if not f.exists():
        continue
    d = pd.read_csv(f).drop_duplicates("url")
    if tag == "uv":
        d["language"] = d["url"].str.extract(r"lang=(\w+)")[0].map({"kn": "Kannada", "en": "English"})
        d["sitemap_date"] = d["lastmod"].str[:10]
    elif tag == "ptv":  # undated URLs: keep posts whose sitemap lastmod is in 2022
        d["sitemap_date"] = d["lastmod"].str[:10]
        d = d[d["sitemap_date"].str.startswith("2022")].copy()
        d["language"] = "Kannada"
    elif tag in LANG:
        d["language"] = LANG[tag]
    else:
        d["language"] = "English"
    d["outlet"] = outlet
    # Prajavani / DH district sections count as DK place evidence
    dk_section = d["url"].str.contains(DC.CFG["section_re"], regex=True)  # district section of the outlet
    res = [F.is_candidate(u, s) for u, s in zip(d["url"], dk_section)]
    d["why"] = [r[1] for r in res]
    d["noise"] = d["url"].map(lambda u: bool(NOISE.search(F.slug_of(u))))
    cand = d[(d["why"] != "") & ~d["noise"]]
    counts.append(dict(outlet=outlet, urls_in_sitemaps=len(d), dk_place_urls=int(sum(F.has_place(u.lower().split('?')[0]) for u in d['url']) + 0),
                       dk_section_urls=int(dk_section.sum()), candidates=len(cand)))
    frames.append(cand[["url", "sitemap_date", "outlet", "language", "why"]])

out = pd.concat(frames, ignore_index=True)
out.to_csv(ROOT / "data" / DC.fname("candidates_all"), index=False)
cnt = pd.DataFrame(counts)
if DC.KEY != "dk":  # column names are district-neutral for new districts
    cnt = cnt.rename(columns={"dk_place_urls": "place_urls", "dk_section_urls": "section_urls"})
cnt.to_csv(ROOT / "data" / DC.fname("sitemap_screen_counts"), index=False)
print(pd.DataFrame(counts).to_string())
print(out.groupby(["outlet", "language", "why"]).size())
