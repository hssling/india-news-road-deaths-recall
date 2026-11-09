"""Pass-2 candidates: road-crash slugs with NO recognised DK place token and no other named place.

Measures what the place-token filter misses (spelling variants, placeless slugs). Writes
data/candidates_pass2.csv (all) for screening; Udayavani screened in full, others sampled.
District-parameterised via KC_DISTRICT (district_cfg.py). For Belagavi the 'other place' list is the DK
list with Belagavi names removed and DK / coastal / Maharashtra-border names added; output
data/candidates_pass2_belagavi.csv.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filters as F  # noqa: E402
import district_cfg as DC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OTHER = re.compile(
    r"udupi|kundapur|karkala|brahmavar|malpe|kaup|katapadi|uchila|shirva|byndoor|hebri|padubidri|manipal|belman|"
    r"kota|saligram|hiriyadka|kollur|kasaragod|kasargod|kerala|bengaluru|bangalore|mysuru|mysore|hubli|hubballi|"
    r"dharwad|belagavi|belgaum|kalaburagi|gulbarga|vijayapur|bijapur|ballari|bellary|ballary|raichur|koppal|kustagi|"
    r"gadag|haveri|davangere|davanagere|shivamogga|shimoga|chikkamagalur|chikmagalur|mudigere|hassan|hasana|"
    r"sakleshpur|kodagu|madikeri|virajpet|mandya|tumakuru|tumkur|chitradurga|kolar|chikkaballapur|ramanagar|"
    r"chamaraj|hanur|bidar|bhalki|yadgir|bagalkot|karwar|uttara|sirsi|bhatkal|honnavar|kumta|ankola|yallapur|sagar|"
    r"thirthahalli|koratagere|chincholi|kurugodu|savadatti|ramadurga|nidasosi|siddapur|delhi|mumbai|maharashtra|maha-|"
    r"tamil|chennai|hyderabad|telangana|andhra|goa|gujarat|rajasthan|uttar|ups|bihar|bengal|kolkata|punjab|haryana|"
    r"kashmir|pakistan|nepal|china|ukraine|russia|usa|america|afghan|canada|nagpur|chandrapur|chittoor|muzaffarnagar")
ROAD = re.compile(r"road|accident|mishap|collision|collide|crash|lorry|bike|scooter|scooty|(^|-)bus(-|$)|tipper|"
                  r"(^|-)cars?(-|$)|truck|tempo|pickup|jeep|rickshaw|(^|-)auto(-|$)|pedestrian|overturn|topple|"
                  r"(^|-)hits?(-|$)|rider|pillion|vehicle")
NOT = re.compile(r"theft|thie|seiz|rally|launch|price|gst|deadline|share|sensex|nifty|market|actor|actress|film|"
                 r"movie|cricket|ipl|policy|scheme|stand|parking|fine|toll|award|election|minister|mla|congress|bjp")

if DC.KEY == "belagavi":
    OTHER = re.compile(OTHER.pattern.replace("belagavi|belgaum|", "").replace("savadatti|ramadurga|", "")
                       + r"|mangalur|mangalor|dakshina|puttur|bantwal|belthang|sullia|ullal|surathkal|moodbidri|"
                         r"kolhapur|sangli|miraj|solapur|satara|pune|ichalkaranji|kagal|gadhinglaj|chandgad|"
                         r"sindhudurg|ratnagiri|jamkhandi|mudhol|bilagi|badami|hungund|ilkal|muddebihal|"
                         r"basavana-bagewadi|(?<![a-z])indi(?![a-z])|sindagi|navalgund|kalghatgi|alnavar|dandeli|haliyal|joida")
    assert "belagavi" not in OTHER.pattern and "savadatti" not in OTHER.pattern
OUTLETS = [("uv", "Udayavani"), ("pv", "Prajavani"), ("dh", "Deccan Herald")]
if DC.KEY != "dk":
    OUTLETS += [("vv", "Vijayavani"), ("kp", "Kannada Prabha"), ("nie", "New Indian Express"), ("an", "Asianet Suvarna"),
                ("ptv", "Public TV")]
# state / district sections kept for placeless slugs (national sections dropped)
STATE_SEC = {"pv": r"/news/karnataka-news/|/india/karnataka/", "dh": r"/news/karnataka-news/|/india/karnataka/",
             "vv": r"/district/|/news/|/state/", "kp": r"/karnataka/", "nie": r"/states/karnataka/",
             "an": r"/state/|/karnataka-districts/|/crime/", "ptv": r"publictv\.in/"}  # Public TV has no sections
rows = []
for tag, outlet in OUTLETS:
    d = pd.read_csv(ROOT / "raw" / "sitemaps" / f"{tag}_2022.csv").drop_duplicates("url")
    slug = d["url"].map(F.slug_of)
    place = d["url"].map(lambda u: F.has_place(u.lower().split("?")[0]))
    sec = d["url"].str.contains(DC.CFG["pv_section"])
    path = d["url"].str.lower().str.split("?").str[0]
    m = slug.str.contains(ROAD) & ~path.str.contains(OTHER) & ~slug.str.contains(NOT) & ~place & ~sec
    m &= slug.str.contains(r"accident|mishap|collision|collide|crash|killed|dies|died|dead|death|no-more|lost-life|"
                           r"run-over|overturn|savu|(^|-)hits?(-|$)")
    x = d[m].copy()
    x["outlet"] = outlet
    if tag == "ptv":
        x = x[x["lastmod"].str.startswith("2022")]
    if tag == "uv":
        x["language"] = x["url"].str.extract(r"lang=(\w+)")[0].map({"kn": "Kannada", "en": "English"})
        x["sitemap_date"] = x["lastmod"].str[:10]
    else:
        if tag == "ptv":
            x["sitemap_date"] = x["lastmod"].str[:10]
        x["language"] = "English" if tag in ("dh", "nie") else "Kannada"
        # national/state sections of PV/DH: keep only karnataka/state sections
        x = x[x["url"].str.contains(STATE_SEC[tag], regex=True)]
    x["why"] = "pass2_placeless"
    rows.append(x[["url", "sitemap_date", "outlet", "language", "why"]])
out = pd.concat(rows, ignore_index=True)
out.to_csv(ROOT / "data" / DC.fname("candidates_pass2"), index=False)
print(out.groupby(["outlet", "language"]).size())
