"""Marathi-outlet candidates for the Belagavi check (URL-level screen, no fetching).

Run with KC_DISTRICT=belagavi. Reads raw/sitemaps/{pu,sk,tb,t9,bl}_2022.csv (07_mr_harvest.py) and writes
  data/candidates_all_belagavi_mr.csv          pass 1: Belagavi place (or district section) + crash term
  data/candidates_pass2_belagavi_mr.csv        pass 2 pool: placeless crash slugs in regional sections
  data/candidates_pass2_screen_belagavi_mr.csv pass 2 screened list (pools > 200 -> 50% sample, random_state=1)
  data/sitemap_screen_counts_belagavi_mr.csv
Same rules as 03_candidates.py / 03b_residual.py / 03c_pass2_sample.py; no existing file is read for writing.
"""
import re
import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg as DC  # noqa: E402
import filters_mr as M  # noqa: E402

assert DC.KEY == "belagavi"
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "raw" / "sitemaps"
D = ROOT / "data"
SUF = "_belagavi_mr"

OUTLETS = [("pu", "Pudhari"), ("sk", "Sakal"), ("tb", "Tarun Bharat"), ("t9", "TV9 Marathi"), ("bl", "Belgaum Live")]
# district sections (place evidence, as Prajavani /district/belagavi/): Pudhari /belgaon/; Belgaum Live is a
# Belgaum-only site, so every URL counts as district-section
SECTION = {"pu": r"pudhari\.news/belgaon/", "bl": r"belgaumlive\.com/"}
# regional sections kept for placeless pass-2 slugs (national / Mumbai / Pune / Vidarbha etc. dropped)
REGION = {"pu": r"/maharashtra/kolhapur/|/latest/|/uncategorized/", "sk": r"/paschim-maharashtra/",
          "tb": r"tarunbharat\.com/",
          "t9": r"tv9marathi\.com/(crime|maharashtra)/[^/]+$|/maharashtra/(other-district|kolhapur|sangli)/",
          "bl": r"$^"}

NOISE_ROMAN = re.compile(r"covid|positive|corona|temple-car|car-festival|rath|bus-stand|bus-stop|bus-depot|"
                         r"bike-theft|bike-rally|car-rally|theft|stolen|gadkari|tender|inaugurat|foundation-stone|"
                         r"parking|toll|flyover|overbridge|underpass|four-lane|elephant|leopard|drown|suicide|"
                         r"murder|assault|ganja|drug|hijab|election|ipl|cricket|film|movie|web-story|horoscope")
# other places (pass 2 exclusion): the Belagavi 03b list (Karnataka, Maharashtra-border, states) plus
# Maharashtra districts/towns in roman and Devanagari script
OTHER_ROMAN = re.compile(
    r"udupi|kundapur|mangalur|mangalor|bengaluru|bangalore|mysuru|mysore|hubli|hubballi|dharwad|kalaburagi|"
    r"gulbarga|vijayapur|bijapur|ballari|bellary|raichur|koppal|gadag|haveri|davangere|shivamogga|shimoga|"
    r"hassan|kodagu|mandya|tumakuru|tumkur|chitradurga|kolar|bidar|yadgir|bagalkot|karwar|sirsi|dandeli|haliyal|"
    r"joida|jamkhandi|mudhol|badami|kolhapur|sangli|sangali|miraj|solapur|satara|karad|pune|pimpri|chinchwad|"
    r"ichalkaranji|kagal|gadhinglaj|chandgad|ajara|ajra|hatkanangale|shirol|jaysingpur|radhanagari|panhala|"
    r"shahuwadi|bhudargad|gaganbawda|sindhudurg|ratnagiri|kudal|sawantwadi|dodamarg|vengurla|goa|panaji|margao|"
    r"mapusa|mumbai|thane|nashik|nagpur|aurangabad|sambhajinagar|nanded|latur|beed|jalna|parbhani|hingoli|osmanabad|"
    r"dharashiv|ahmednagar|nagar|jalgaon|dhule|nandurbar|akola|amravati|yavatmal|wardha|chandrapur|gadchiroli|"
    r"bhandara|gondia|washim|buldhana|raigad|palghar|baramati|lonavala|delhi|gujarat|rajasthan|uttar|bihar|"
    r"bengal|punjab|haryana|kashmir|hyderabad|telangana|andhra|tamil|chennai|kerala|madhya|indore|bhopal|"
    r"pakistan|nepal|china|ukraine|russia|america|usa|dubai|london")
OTHER_DEV = re.compile(
    "कोल्हापूर|सांगली|मिरज|सातारा|कराड|पुणे|पिंपरी|मुंबई|ठाणे|रत्नागिरी|सिंधुदुर्ग|कुडाळ|सावंतवाडी|दोडामार्ग|गोवा|"
    "पणजी|मडगाव|म्हापसा|चंदगड|गडहिंग्लज|आजरा|कागल|इचलकरंजी|हातकणंगले|शिरोळ|जयसिंगपूर|राधानगरी|पन्हाळा|"
    "शाहूवाडी|भुदरगड|सोलापूर|नाशिक|नागपूर|औरंगाबाद|नांदेड|लातूर|बीड|जालना|अहमदनगर|जळगाव|धुळे|अकोला|"
    "अमरावती|रायगड|बारामती|धारवाड|हुबळी|विजापूर|बागलकोट|जमखंडी|कारवार|बंगळूर|बेंगळुरू|दिल्ली|गुजरात")
DEATH_SLUG = re.compile(r"accident|mishap|collision|collide|crash|killed|dies|died|dead|death|run-over|overturn|"
                        r"apghat|apaghat|(^|-)thar(-|$)|mrutyu|mrityu|jagich|(^|-)hits?(-|$)|"
                        "अपघात|ठार|मृत्यू|मृत्यु|जागीच|धडक|चिरडून|गतप्राण|दुर्घटना")
ROAD_SLUG = re.compile(r"road|accident|mishap|collision|crash|lorry|truck|bike|scooter|(^|-)bus(-|$)|(^|-)cars?(-|$)|"
                       r"tempo|jeep|rickshaw|tractor|container|dumper|cruiser|pedestrian|overturn|vehicle|highway|"
                       r"apghat|apaghat|"
                       "अपघात|धडक|दुचाकी|ट्रक|कंटेनर|टेम्पो|ट्रॅक्टर|डंपर|रिक्षा|बस|कार|जीप|महामार्ग|उलट|चिरडून")
NOT = re.compile(r"theft|seiz|rally|launch|price|gst|share|sensex|market|actor|actress|film|movie|cricket|ipl|"
                 r"policy|scheme|stand|parking|fine|toll|award|election|minister|mla|congress|bjp|insurance|"
                 "चोरी|निवडणूक|चित्रपट|विमा")


def fix_mojibake(u):
    """requests decoded the sitemap XML as Latin-1; undo it exactly (Latin-1 is bijective), then percent-encode."""
    if re.search(r"[À-ÿ]", u):
        try:
            u = u.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return u
    return quote(u, safe=":/?=&%#~+-_.,!*'()@") if re.search(r"[^\x00-\x7f]", u) else u


frames, pass2, counts = [], [], []
for tag, outlet in OUTLETS:
    f = SM / f"{tag}_2022.csv"
    if not f.exists():
        print("missing", f)
        continue
    d = pd.read_csv(f, dtype=str).fillna("")
    d["url"] = d["url"].map(fix_mojibake)
    d = d.drop_duplicates("url")
    if tag in ("pu", "sk"):
        d["sitemap_date"] = d["sitemap_date"].str[:10]
    elif tag in ("tb", "t9"):  # undated URLs: lastmod (proxy for publication date); TV9 sitemaps are 2022-monthly
        d["sitemap_date"] = d["lastmod"].str[:10]
        if tag == "tb":
            d = d[d["sitemap_date"].str.startswith("2022")].copy()
    elif tag == "bl":  # dated URLs /YYYY/MM/
        ym = d["url"].str.extract(r"belgaumlive\.com/(\d{4})/(\d{2})/")
        d = d[ym[0] == "2022"].copy()
        d["sitemap_date"] = "2022-" + ym.loc[d.index, 1]
    d["outlet"], d["language"] = outlet, "Marathi"
    sec = d["url"].str.contains(SECTION[tag], regex=True) if tag in SECTION else pd.Series(False, index=d.index)
    res = [M.is_candidate(u, s) for u, s in zip(d["url"], sec)]
    d["why"] = [r[1] for r in res]
    slug = d["url"].map(M.slug_of)
    d["noise"] = slug.map(lambda s: bool(NOISE_ROMAN.search(s) or M.MR_NOISE.search(s)))
    cand = d[(d["why"] != "") & ~d["noise"]]
    frames.append(cand[["url", "sitemap_date", "outlet", "language", "why"]])
    # pass 2: crash slugs with no Belagavi place, no other place, not in a district section, in a regional section
    path = d["url"].map(M.dec)
    place = path.map(M.has_place)
    m = (slug.str.contains(ROAD_SLUG) & slug.str.contains(DEATH_SLUG) & ~slug.str.contains(NOT)
         & ~path.str.contains(OTHER_ROMAN) & ~path.str.contains(OTHER_DEV) & ~place & ~sec & ~d["noise"]
         & d["url"].str.contains(REGION[tag], regex=True))
    x = d[m].copy()
    x["why"] = "pass2_placeless"
    pass2.append(x[["url", "sitemap_date", "outlet", "language", "why"]])
    counts.append(dict(outlet=outlet, urls_2022=len(d), place_urls=int(place.sum()), section_urls=int(sec.sum()),
                       candidates=len(cand), pass2_pool=len(x)))

c1 = pd.concat(frames, ignore_index=True)
c1.to_csv(D / f"candidates_all{SUF}.csv", index=False)
p2 = pd.concat(pass2, ignore_index=True)
p2 = p2[~p2["url"].isin(c1["url"])]
p2.to_csv(D / f"candidates_pass2{SUF}.csv", index=False)
parts = []
for o in p2["outlet"].drop_duplicates():
    x = p2[p2.outlet == o].reset_index(drop=True)
    if len(x) > 200:  # large pools: 50% random sample, same call as 03c_pass2_sample.py
        x = x.sample(frac=0.5, random_state=1).sort_index()
    parts.append(x)
p2s = pd.concat(parts, ignore_index=True)
p2s.to_csv(D / f"candidates_pass2_screen{SUF}.csv", index=False)
# pass 2b (Tarun Bharat only, extra check outside the standard method): WordPress truncates Devanagari slugs to ~24
# characters, so a crash term can be cut off. Pool = Devanagari slugs that name a Belagavi place, have no crash term,
# are >= 20 characters long (i.e. probably truncated) and are not noise; 50% sample if > 200 (random_state=1).
tb = pd.read_csv(SM / "tb_2022.csv", dtype=str).fillna("")
tb["url"] = tb["url"].map(fix_mojibake)
tb = tb.drop_duplicates("url")
tb["sitemap_date"] = tb["lastmod"].str[:10]
tb = tb[tb["sitemap_date"].str.startswith("2022")]
s = tb["url"].map(M.slug_of)
m2b = (s.str.contains("[ऀ-ॿ]") & (s.str.len() >= 20) & tb["url"].map(M.dec).map(M.has_place)
       & ~s.map(M.has_crash) & ~s.map(lambda x: bool(NOISE_ROMAN.search(x) or M.MR_NOISE.search(x))))
p2b = tb[m2b].assign(outlet="Tarun Bharat", language="Marathi", why="pass2b_truncated")[
    ["url", "sitemap_date", "outlet", "language", "why"]].reset_index(drop=True)
p2b.to_csv(D / f"candidates_pass2b{SUF}.csv", index=False)
p2bs = p2b.sample(frac=0.5, random_state=1).sort_index() if len(p2b) > 200 else p2b
p2bs.to_csv(D / f"candidates_pass2b_screen{SUF}.csv", index=False)
print("pass 2b (Tarun Bharat truncated Devanagari place slugs): pool", len(p2b), "screened", len(p2bs))

cnt = pd.DataFrame(counts)
cnt["pass2_screened"] = cnt["outlet"].map(p2s.groupby("outlet").size()).fillna(0).astype(int)
cnt.to_csv(D / f"sitemap_screen_counts{SUF}.csv", index=False)
print(cnt.to_string())
print(c1.groupby(["outlet", "why"]).size())
