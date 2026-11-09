"""Assemble kill-check outputs from the hand-coded article file.

Input  data/killcheck_coding.csv  (one row per article that reports a road crash; coded by hand)
       columns: url, outlet, language, pub_date, crash_id, crash_date, place, taluk, in_district,
                fatal, deaths, victim_types, vehicles, basis, notes
       data/screen_log.csv        (every fetched candidate)
       data/candidates_all.csv    (URL-level candidates)
       data/official_benchmark.csv
Output data/killcheck_articles.csv, data/killcheck_crashes.csv, data/killcheck_summary.csv
District-parameterised via KC_DISTRICT (district_cfg.py): non-DK districts read and write *_<district>.csv
(e.g. killcheck_coding_belagavi.csv -> killcheck_crashes_belagavi.csv). Default = DK, unchanged.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg as DC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
FN = DC.fname
SHORT = "DK" if DC.KEY == "dk" else DC.CFG["name"]

code = pd.read_csv(D / FN("killcheck_coding"), dtype=str).fillna("")
code["deaths"] = pd.to_numeric(code["deaths"], errors="coerce").fillna(0).astype(int)

# resolve 'Outlet:i' / 'P2:Outlet:i' references (index into the outlet subset screened by 04_screen.py)
if DC.KEY == "dk":
    cands = {"P1": pd.read_csv(D / "candidates_frozen_v1.csv"), "P2": pd.read_csv(D / "candidates_pass2_screen.csv")}
    cands["P1"] = pd.concat([cands["P1"][cands["P1"].outlet == "Udayavani"],
                             pd.read_csv(D / "candidates_all.csv").query("outlet != 'Udayavani'")])
else:
    cands = {"P1": pd.read_csv(D / FN("candidates_all")), "P2": pd.read_csv(D / FN("candidates_pass2_screen"))}


def resolve(ref):
    parts = ref.split(":")
    p = "P2" if parts[0] == "P2" else "P1"
    outlet, i = parts[-2], int(parts[-1])
    sub = cands[p][cands[p]["outlet"].str.contains(outlet, case=False)]
    r = sub.iloc[i]
    return pd.Series(dict(url=r.url, outlet=r.outlet, language=r.language, pass_=("pass2" if p == "P2" else "pass1")))


code = pd.concat([code, code["ref"].apply(resolve)], axis=1)
logs = sorted(f for f in D.glob("screen_log*.csv") if DC.own_file(f.name))
screen = pd.concat([pd.read_csv(f, dtype=str) for f in logs]).fillna("")
pub = screen.drop_duplicates("url").set_index("url")["pub_date"]
code["pub_date"] = code["url"].map(pub).fillna("")
code["basis"] = code["basis"].replace({"headline": "headline+subhead+keywords"})
core = code["scope"] == "core"

# ---- articles file: every fetched candidate, with relevance + crash id
arts = screen[["url", "pub_date", "outlet", "language", "fetch_status"]].drop_duplicates("url").copy()
cmap = code.groupby("url")["crash_id"].apply(lambda s: ";".join(sorted(set(x for x in s if x))))
arts["crash_id"] = arts["url"].map(cmap).fillna("")
rel = code.assign(r=(code["in_district"] == "Y") & (code["fatal"] == "Y") & core).groupby("url")["r"].any()
arts["relevant"] = arts["url"].map(rel).map({True: "yes", False: "no"}).fillna("no")
kind = code.groupby("url").apply(
    lambda g: f"{SHORT} fatal crash" if ((g.in_district == "Y") & (g.fatal == "Y")).any()
    else (f"{SHORT} non-fatal crash" if (g.in_district == "Y").any() else f"crash outside {SHORT}"),
    include_groups=False)
arts["relevance_note"] = arts["url"].map(kind).fillna(f"not a road crash / not {SHORT}")
arts.to_csv(D / FN("killcheck_articles"), index=False)

# ---- crashes file: one row per de-duplicated DK fatal crash
fat = code[(code["in_district"] == "Y") & (code["fatal"] == "Y") & core & code["crash_id"].str.startswith("C")]
# sanity: a crash id must not mix core and non-core codes, and dedup rule (+-1 day of earliest report date
# is NOT required for follow-ups) is checked by listing spread of crash_date per id
spread = fat.assign(cd=pd.to_datetime(fat["crash_date"])).groupby("crash_id")["cd"].agg(lambda s: (s.max() - s.min()).days)
print("crash ids with crash_date spread > 1 day:", spread[spread > 1].to_dict())


def agg(g):
    langs = sorted(set(g["language"]))
    return pd.Series(dict(
        crash_date=g["crash_date"].replace("", pd.NA).dropna().min() if (g["crash_date"] != "").any() else "",
        place=max(g["place"], key=len), taluk=max(g["taluk"], key=len),
        deaths=int(g["deaths"].max()),  # max across reports (later reports capture subsequent deaths)
        victim_types=max(g["victim_types"], key=len), vehicles=max(g["vehicles"], key=len),
        n_articles=len(g), outlets=";".join(sorted(set(g["outlet"]))),
        in_english=any(l == "English" for l in langs), in_kannada=any(l == "Kannada" for l in langs),
        basis=";".join(sorted(set(g["basis"]))), source_urls=" ".join(g["url"]),
        notes=" | ".join(x for x in g["notes"] if x)))


crashes = fat.groupby("crash_id").apply(agg, include_groups=False).reset_index()
crashes = crashes.sort_values("crash_date")
crashes.to_csv(D / FN("killcheck_crashes"), index=False)

# ---- recall summary
off = pd.read_csv(D / FN("official_benchmark"))
U = DC.CFG["combined"]
tot = int(off.query("level=='annual' and year==2022 and unit==@U")["deaths"].iloc[0])
fatal_cr = int(off.query("level=='monthly' and unit==@U")["fatal_crashes"].sum())
rows = []
for lab, sub in [("English only (any English outlet)", crashes[crashes.in_english]),
                 ("Kannada only (any Kannada outlet)", crashes[crashes.in_kannada]),
                 ("Union", crashes)]:
    rows.append(dict(scope=lab, crashes=len(sub), deaths=int(sub.deaths.sum()),
                     official_deaths=tot, recall_deaths=round(sub.deaths.sum() / tot, 3),
                     official_fatal_crashes=fatal_cr, recall_crashes=round(len(sub) / fatal_cr, 3)))
for o in sorted(set(code["outlet"])):
    sub = crashes[crashes.outlets.str.contains(o, regex=False)]
    rows.append(dict(scope=f"outlet: {o}", crashes=len(sub), deaths=int(sub.deaths.sum()),
                     official_deaths=tot, recall_deaths=round(sub.deaths.sum() / tot, 3),
                     official_fatal_crashes=fatal_cr, recall_crashes=round(len(sub) / fatal_cr, 3)))
summ = pd.DataFrame(rows)
summ.to_csv(D / FN("killcheck_summary"), index=False)
print(summ.to_string())

# by month
crashes["month"] = pd.to_datetime(crashes["crash_date"], errors="coerce").dt.month_name()
mo = off.query("level=='monthly' and unit==@U")[["period", "deaths", "fatal_crashes"]].rename(
    columns={"period": "month", "deaths": "official_deaths", "fatal_crashes": "official_fatal_crashes"})
nm = crashes.groupby("month").agg(news_crashes=("crash_id", "size"), news_deaths=("deaths", "sum")).reset_index()
mo = mo.merge(nm, on="month", how="left").fillna(0)
mo["recall_deaths"] = (mo.news_deaths / mo.official_deaths).round(3)
mo.to_csv(D / FN("killcheck_recall_by_month"), index=False)
print(mo.to_string())
if DC.KEY != "dk":  # half-year recall (DK report gives it in the text only)
    mo["half"] = ["H1 (Jan-Jun)" if i < 6 else "H2 (Jul-Dec)" for i in range(len(mo))]
    hy = mo.groupby("half")[["official_deaths", "official_fatal_crashes", "news_crashes", "news_deaths"]].sum().reset_index()
    hy["recall_deaths"] = (hy.news_deaths / hy.official_deaths).round(3)
    hy["recall_crashes"] = (hy.news_crashes / hy.official_fatal_crashes).round(3)
    hy.to_csv(D / FN("killcheck_recall_by_half"), index=False)
    print(hy.to_string())
    print("Spearman(official, news deaths by month):", round(mo.official_deaths.corr(mo.news_deaths, method="spearman"), 2))

# by road-user type of victims (crash-level type; multi-death crashes assumed same type)
amap = {"pedestrian": "pedestrian", "bicycle": "bicycle", "two_wheeler": "two_wheeler", "car": "car_taxi_van_lmv",
        "truck": "truck_lorry", "bus": "bus", "autorickshaw": "autorickshaw", "other": "other_motor_vehicle",
        "unknown": "unknown"}
crashes["ru"] = crashes["victim_types"].map(amap).fillna("unknown")
ru = off.query("level=='road_user' and unit==@U")[["road_user", "deaths"]].rename(
    columns={"road_user": "ru", "deaths": "official_deaths"})
nr = crashes.groupby("ru").agg(news_deaths=("deaths", "sum"), news_crashes=("crash_id", "size")).reset_index()
ru = ru.merge(nr, on="ru", how="outer").fillna(0)
ru["recall_deaths"] = (ru.news_deaths / ru.official_deaths.replace(0, float("nan"))).round(3)
ru.to_csv(D / FN("killcheck_recall_by_road_user"), index=False)
print(ru.to_string())

# sensitivity: include borderline crashes (tree fall / snapped power line on moving vehicle)
bl = code[(code.in_district == "Y") & (code.fatal == "Y") & (code.scope == "borderline")]
bl_deaths = int(bl.groupby("crash_id")["deaths"].max().sum())
print("borderline crashes:", bl.crash_id.nunique(), "deaths:", bl_deaths)
# deaths by crash size
print("deaths per crash distribution:", crashes.deaths.value_counts().sort_index().to_dict())
print("outlets per crash:", crashes.outlets.str.count(";").add(1).value_counts().sort_index().to_dict())
print("taluk:", crashes.groupby("taluk").deaths.sum().to_dict())

# by police unit: Mangaluru City commissionerate (Mangaluru, Ullal, Mulki, Moodbidri taluks)
# vs Dakshina Kannada district police (Bantwal, Belthangady, Puttur, Kadaba, Sullia)
city = DC.CFG["city_taluks"]
cu, rurl, units = DC.CFG["city_unit"], DC.CFG["rural_unit"], DC.CFG["units"]
crashes["unit"] = crashes["taluk"].map(lambda t: cu if t in city else rurl)
un = crashes.groupby("unit").agg(news_crashes=("crash_id", "size"), news_deaths=("deaths", "sum")).reset_index()
uo = off.query("level=='annual' and year==2022 and unit in @units")[["unit", "deaths"]]
un = un.merge(uo.rename(columns={"deaths": "official_deaths"}), on="unit")
un["recall_deaths"] = (un.news_deaths / un.official_deaths).round(3)
if DC.KEY != "dk":
    fcu = off.query("level=='monthly'").groupby("unit")["fatal_crashes"].sum()
    un["official_fatal_crashes"] = un["unit"].map(fcu)
    un["recall_crashes"] = (un.news_crashes / un.official_fatal_crashes).round(3)
un.to_csv(D / FN("killcheck_recall_by_unit"), index=False)
print(un.to_string())

# outlet / language overlap
def has(o):
    return crashes.outlets.str.contains(o, regex=False)
dh, pv, uv = has("Deccan Herald"), has("Prajavani"), has("Udayavani")
if DC.KEY != "dk":  # generic overlap: every outlet combination + language sets
    ov = crashes.groupby("outlets").agg(crashes=("crash_id", "size"), deaths=("deaths", "sum")).reset_index()
    ov = ov.rename(columns={"outlets": "set"}).sort_values("crashes", ascending=False)
    lang = pd.DataFrame([dict(set=k, crashes=int(m.sum()), deaths=int(crashes.deaths[m].sum())) for k, m in {
        "English & Kannada (any)": crashes.in_english & crashes.in_kannada,
        "English only": crashes.in_english & ~crashes.in_kannada,
        "Kannada only": ~crashes.in_english & crashes.in_kannada}.items()])
    solo = pd.DataFrame([dict(set=f"unique to {o}", crashes=int((crashes.outlets == o).sum()),
                              deaths=int(crashes.deaths[crashes.outlets == o].sum())) for o in sorted(set(code.outlet))])
    ov = pd.concat([ov, solo, lang], ignore_index=True)
    ov.to_csv(D / FN("killcheck_overlap"), index=False)
    print(ov.to_string())
ov = None if DC.KEY != "dk" else pd.DataFrame([dict(set=k, crashes=int(m.sum()), deaths=int(crashes.deaths[m].sum())) for k, m in {
    "Udayavani only": uv & ~pv & ~dh, "Prajavani only": pv & ~uv & ~dh, "Deccan Herald only": dh & ~uv & ~pv,
    "Udayavani+Prajavani": uv & pv & ~dh, "Udayavani+DH": uv & dh & ~pv, "Prajavani+DH": pv & dh & ~uv,
    "all three": uv & pv & dh, "English & Kannada (any)": crashes.in_english & crashes.in_kannada,
    "English only": crashes.in_english & ~crashes.in_kannada, "Kannada only": ~crashes.in_english & crashes.in_kannada}.items()])
if ov is not None:
    ov.to_csv(D / "killcheck_overlap.csv", index=False)
    print(ov.to_string())
# English outlets separately: DH (English daily) vs Udayavani English edition
uve = code[(code.outlet == "Udayavani") & (code.language == "English") & code.crash_id.isin(crashes.crash_id)].crash_id.unique()
uvk = code[(code.outlet == "Udayavani") & (code.language == "Kannada") & code.crash_id.isin(crashes.crash_id)].crash_id.unique()
for lab, ids in [("Udayavani English edition", uve), ("Udayavani Kannada edition", uvk)]:
    print(lab, len(ids), int(crashes[crashes.crash_id.isin(ids)].deaths.sum()))
