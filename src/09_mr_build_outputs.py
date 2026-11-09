"""Assemble the Marathi-outlet extension of the Belagavi kill check and the all-outlet union.

Run with KC_DISTRICT=belagavi. Reads (never writes) the existing Belagavi outputs:
  data/killcheck_crashes_belagavi.csv (42 Kannada/English crashes), data/killcheck_coding_belagavi.csv,
  data/official_benchmark_belagavi.csv
and the Marathi inputs:
  data/killcheck_coding_belagavi_mr.csv  hand coding; ref = 'Outlet:i' (pass 1) or 'P2:Outlet:i' (pass 2), index into
      the outlet subset of candidates_all_belagavi_mr.csv / candidates_pass2_screen_belagavi_mr.csv (as 04b screened them);
      crash_id = an existing id (C001-C045) when the report matches an existing crash, 'M##' for a crash not in the
      Kannada/English file (one M id per de-duplicated new crash), X / N / blank as in the original coding.
  data/screen_logs_mr/screen_log_*.csv  every fetch (04b_screen_mr.py)
Writes (suffix _belagavi_mr / _belagavi_all only):
  killcheck_articles_belagavi_mr.csv, killcheck_crashes_belagavi_mr.csv (Marathi-found crashes, with match column),
  killcheck_dedup_check_belagavi_mr.csv, killcheck_summary_belagavi_all.csv, killcheck_recall_by_road_user_belagavi_all.csv,
  killcheck_recall_by_unit_belagavi_all.csv, killcheck_recall_by_half_belagavi_all.csv,
  killcheck_recall_by_month_belagavi_all.csv, killcheck_overlap_belagavi_all.csv, killcheck_severity_belagavi_all.csv,
  killcheck_crashes_belagavi_all.csv (union crash file)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg as DC  # noqa: E402

assert DC.KEY == "belagavi"
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
MR, ALL = "_belagavi_mr", "_belagavi_all"

# ---------------------------------------------------------------- inputs
old = pd.read_csv(D / "killcheck_crashes_belagavi.csv", dtype=str).fillna("")
old["deaths"] = old["deaths"].astype(int)
old_code = pd.read_csv(D / "killcheck_coding_belagavi.csv", dtype=str).fillna("")
code = pd.read_csv(D / f"killcheck_coding{MR}.csv", dtype=str).fillna("")
code["deaths"] = pd.to_numeric(code["deaths"], errors="coerce").fillna(0).astype(int)
cands = {"P1": pd.read_csv(D / f"candidates_all{MR}.csv"), "P2": pd.read_csv(D / f"candidates_pass2_screen{MR}.csv"),
         "P2B": pd.read_csv(D / f"candidates_pass2b_screen{MR}.csv")}


def resolve(ref):
    parts = ref.split(":")
    p = parts[0] if parts[0] in ("P2", "P2B") else "P1"
    outlet, i = parts[-2], int(parts[-1])
    sub = cands[p][cands[p]["outlet"].str.contains(outlet, case=False, regex=False)]
    r = sub.iloc[i]
    return pd.Series(dict(url=r.url, outlet=r.outlet, language=r.language,
                          pass_={"P1": "pass1", "P2": "pass2", "P2B": "pass2b"}[p]))


code = pd.concat([code, code["ref"].apply(resolve)], axis=1)
assert not code["url"].duplicated().any(), code[code["url"].duplicated(keep=False)]
logs = sorted((D / "screen_logs_mr").glob("screen_log_*.csv"))
screen = pd.concat([pd.read_csv(f, dtype=str) for f in logs]).fillna("")
assert set(code["url"]) <= set(screen["url"]), "coded URL never fetched"
pub = screen.drop_duplicates("url").set_index("url")["pub_date"]
code["pub_date"] = code["url"].map(pub).fillna("")
core = code["scope"] == "core"
infat = (code["in_district"] == "Y") & (code["fatal"] == "Y")

# ---------------------------------------------------------------- new crash ids (M## -> C046...)
mrows = code[infat & core & code["crash_id"].str.startswith("M")]
# ids are kept stable across runs: M01-M18 (first batch: Pudhari, Sakal, TV9 Marathi) were issued C046-C063 in
# date order; crashes added with Tarun Bharat (M19-M37) are C064-C082 in date order; crashes added with
# Belgaum Live (M38+) follow from C083 in date order
first = mrows.assign(cd=pd.to_datetime(mrows["crash_date"]),
                     batch=pd.cut(mrows["crash_id"].str[1:].astype(int), [0, 18, 37, 999], labels=False)).groupby("crash_id")[["batch", "cd"]].min()
first = first.sort_values(["batch", "cd"])
used = set(old["crash_id"]) | set(old_code["crash_id"])
nxt = max(int(c[1:]) for c in used if c.startswith("C") and c[1:].isdigit()) + 1
newid = {m: f"C{nxt + k:03d}" for k, m in enumerate(first.index)}
code["final_id"] = code["crash_id"].map(lambda c: newid.get(c, c))

# ---------------------------------------------------------------- articles file
arts = screen[["url", "pub_date", "outlet", "language", "fetch_status"]].drop_duplicates("url").copy()
cmap = code.groupby("url")["final_id"].apply(lambda s: ";".join(sorted(set(x for x in s if x))))
arts["crash_id"] = arts["url"].map(cmap).fillna("")
arts["relevant"] = arts["url"].map((code.assign(r=infat & core)).groupby("url")["r"].any()).map({True: "yes", False: "no"}).fillna("no")
kind = code.groupby("url").apply(
    lambda g: "Belagavi fatal crash" if ((g.in_district == "Y") & (g.fatal == "Y")).any()
    else ("Belagavi non-fatal crash" if (g.in_district == "Y").any() else "crash outside Belagavi / undetermined"),
    include_groups=False)
arts["relevance_note"] = arts["url"].map(kind).fillna("not a road crash / not Belagavi")
arts.to_csv(D / f"killcheck_articles{MR}.csv", index=False)

# ---------------------------------------------------------------- Marathi crash file
fat = code[infat & core & code["final_id"].str.startswith("C")]


def agg(g):
    return pd.Series(dict(
        crash_date=g["crash_date"].replace("", pd.NA).dropna().min(),
        place=max(g["place"], key=len), taluk=max(g["taluk"], key=len), deaths=int(g["deaths"].max()),
        victim_types=max(g["victim_types"], key=len), vehicles=max(g["vehicles"], key=len),
        n_articles=len(g), outlets=";".join(sorted(set(g["outlet"]))), basis=";".join(sorted(set(g["basis"]))),
        source_urls=" ".join(g["url"]), notes=" | ".join(x for x in g["notes"] if x)))


mr = fat.groupby("final_id").apply(agg, include_groups=False).reset_index().rename(columns={"final_id": "crash_id"})
mr["match_existing_id"] = mr["crash_id"].where(mr["crash_id"].isin(old["crash_id"]), "")
mr["status"] = mr["match_existing_id"].map(lambda x: "matches existing Kannada/English crash" if x else "new (Marathi only)")
mr = mr.sort_values("crash_date")
cols = ["crash_id", "match_existing_id", "status", "crash_date", "place", "taluk", "deaths", "victim_types", "vehicles",
        "n_articles", "outlets", "basis", "source_urls", "notes"]
mr[cols].to_csv(D / f"killcheck_crashes{MR}.csv", index=False)
# new Marathi-only crashes in exactly the columns of killcheck_crashes_belagavi.csv (ids C046+, no collision)
nw = mr[mr["match_existing_id"] == ""].assign(in_english=False, in_kannada=False)
assert not set(nw["crash_id"]) & used, "new crash id collides with an existing id"
nw[list(old.columns)].to_csv(D / f"killcheck_crashes{MR}_new.csv", index=False)

# ---------------------------------------------------------------- de-duplication check (date +-2 d, taluk, deaths)
o = old.assign(cd=pd.to_datetime(old["crash_date"]))
chk = []
for r in mr.itertuples():
    cd = pd.to_datetime(r.crash_date)
    near = o[(o.cd - cd).abs().dt.days <= 2]
    same_tk = near[near.taluk == r.taluk]
    if r.match_existing_id:
        e = o[o.crash_id == r.match_existing_id].iloc[0]
        chk.append(dict(crash_id=r.crash_id, kind="matched", date_gap_days=abs((e.cd - cd).days), taluk_mr=r.taluk,
                        taluk_existing=e.taluk, deaths_mr=r.deaths, deaths_existing=e.deaths,
                        other_candidates_pm2d=";".join(x for x in near.crash_id if x != r.match_existing_id)))
    else:
        chk.append(dict(crash_id=r.crash_id, kind="new", date_gap_days="", taluk_mr=r.taluk, taluk_existing="",
                        deaths_mr=r.deaths, deaths_existing="",
                        other_candidates_pm2d=";".join(f"{x.crash_id}({x.taluk},{x.deaths}d,{x.crash_date})" for x in near.itertuples())))
chk = pd.DataFrame(chk)
chk.to_csv(D / f"killcheck_dedup_check{MR}.csv", index=False)
print(chk.to_string())
bad = chk[(chk.kind == "matched") & ((chk.date_gap_days.astype(str).replace("", "0").astype(int) > 2) | (chk.taluk_mr != chk.taluk_existing))]
print("matched crashes outside the +-2 d / same-taluk rule:", bad.crash_id.tolist())

# ---------------------------------------------------------------- union crash file
mro = mr.set_index("crash_id")
u = old.copy()
u["outlets_mr"] = u["crash_id"].map(mro["outlets"]).fillna("")
u["deaths"] = [max(d, int(mro.loc[c, "deaths"])) if c in mro.index else d for c, d in zip(u.crash_id, u.deaths)]
u["in_kn_en"] = True
newc = mr[mr["match_existing_id"] == ""].copy()
newc = newc.assign(outlets_mr=newc["outlets"], outlets="", in_kn_en=False, in_english="False", in_kannada="False")
u = pd.concat([u, newc[["crash_id", "crash_date", "place", "taluk", "deaths", "victim_types", "vehicles", "outlets",
                        "outlets_mr", "in_kn_en", "in_english", "in_kannada", "source_urls", "notes"]]], ignore_index=True)
u["in_marathi"] = u["outlets_mr"] != ""
u["outlets_all"] = [";".join(x for x in (a, b) if x) for a, b in zip(u.outlets, u.outlets_mr)]
u = u.sort_values("crash_date")
u.to_csv(D / f"killcheck_crashes{ALL}.csv", index=False)

# ---------------------------------------------------------------- recall summary
off = pd.read_csv(D / "official_benchmark_belagavi.csv")
U = DC.CFG["combined"]
tot = int(off.query("level=='annual' and year==2022 and unit==@U")["deaths"].iloc[0])
fcr = int(off.query("level=='monthly' and unit==@U")["fatal_crashes"].sum())


def row(lab, s):
    return dict(scope=lab, crashes=len(s), deaths=int(s.deaths.sum()), official_deaths=tot,
                recall_deaths=round(s.deaths.sum() / tot, 3), official_fatal_crashes=fcr, recall_crashes=round(len(s) / fcr, 3))


rows = [row("Kannada + English outlets (existing file)", u[u.in_kn_en]),
        row("Marathi outlets (any)", u[u.in_marathi]),
        row("Marathi only (not in Kannada/English file)", u[u.in_marathi & ~u.in_kn_en]),
        row("Kannada/English crashes also found in Marathi", u[u.in_marathi & u.in_kn_en]),
        row("All-outlet union (Kannada + English + Marathi)", u)]
only2b = set(fat.groupby("final_id")["pass_"].agg(lambda s: set(s) == {"pass2b"}).loc[lambda x: x].index)
rows.append(row("All-outlet union, standard passes only (without Tarun Bharat pass-2b finds)",
                u[~(u.crash_id.isin(only2b) & ~u.in_kn_en)]))
for ol in sorted(set(code["outlet"])):
    rows.append(row(f"outlet: {ol}", u[u.outlets_mr.str.contains(ol, regex=False)]))
# sensitivity: borderline events (existing + Marathi) added
blo = old_code[(old_code.in_district == "Y") & (old_code.fatal == "Y") & (old_code.scope == "borderline")]
blm = code[infat & (code.scope == "borderline")]
bl = pd.concat([blo[["crash_id", "deaths"]].assign(deaths=lambda x: x.deaths.astype(int)), blm[["final_id", "deaths"]].rename(columns={"final_id": "crash_id"})])
bl = bl.groupby("crash_id")["deaths"].max()
r = row("All-outlet union + borderline events (sensitivity)", u)
r.update(crashes=len(u) + len(bl), deaths=int(u.deaths.sum() + bl.sum()))
r.update(recall_deaths=round(r["deaths"] / tot, 3), recall_crashes=round(r["crashes"] / fcr, 3))
rows.append(r)
summ = pd.DataFrame(rows)
summ.to_csv(D / f"killcheck_summary{ALL}.csv", index=False)
print(summ.to_string())
print("borderline crashes:", bl.to_dict())

# ---------------------------------------------------------------- by road user
amap = {"pedestrian": "pedestrian", "bicycle": "bicycle", "two_wheeler": "two_wheeler", "car": "car_taxi_van_lmv",
        "truck": "truck_lorry", "bus": "bus", "autorickshaw": "autorickshaw", "other": "other_motor_vehicle",
        "unknown": "unknown"}
u["ru"] = u["victim_types"].map(amap).fillna("unknown")
ru = off.query("level=='road_user' and unit==@U")[["road_user", "deaths"]].rename(columns={"road_user": "ru", "deaths": "official_deaths"})
for lab, s in [("kn_en", u[u.in_kn_en]), ("all", u)]:
    g = s.groupby("ru").agg(**{f"news_deaths_{lab}": ("deaths", "sum"), f"news_crashes_{lab}": ("crash_id", "size")}).reset_index()
    ru = ru.merge(g, on="ru", how="outer")
ru = ru.fillna(0)
for lab in ("kn_en", "all"):
    ru[f"recall_deaths_{lab}"] = (ru[f"news_deaths_{lab}"] / ru.official_deaths.replace(0, float("nan"))).round(3)
ru.to_csv(D / f"killcheck_recall_by_road_user{ALL}.csv", index=False)
print(ru.to_string())

# ---------------------------------------------------------------- by police unit
city = DC.CFG["city_taluks"]
u["unit"] = u["taluk"].map(lambda t: DC.CFG["city_unit"] if t in city else DC.CFG["rural_unit"])
uo = off.query("level=='annual' and year==2022 and unit in @DC.CFG['units']")[["unit", "deaths"]].rename(columns={"deaths": "official_deaths"})
uo["official_fatal_crashes"] = uo["unit"].map(off.query("level=='monthly'").groupby("unit")["fatal_crashes"].sum())
for lab, s in [("kn_en", u[u.in_kn_en]), ("all", u)]:
    g = s.groupby("unit").agg(**{f"news_crashes_{lab}": ("crash_id", "size"), f"news_deaths_{lab}": ("deaths", "sum")}).reset_index()
    uo = uo.merge(g, on="unit", how="left")
uo = uo.fillna(0)
for lab in ("kn_en", "all"):
    uo[f"recall_deaths_{lab}"] = (uo[f"news_deaths_{lab}"] / uo.official_deaths).round(3)
    uo[f"recall_crashes_{lab}"] = (uo[f"news_crashes_{lab}"] / uo.official_fatal_crashes).round(3)
uo.to_csv(D / f"killcheck_recall_by_unit{ALL}.csv", index=False)
print(uo.to_string())

# ---------------------------------------------------------------- by month / half-year
u["month"] = pd.to_datetime(u["crash_date"]).dt.month_name()
mo = off.query("level=='monthly' and unit==@U")[["period", "deaths", "fatal_crashes"]].rename(
    columns={"period": "month", "deaths": "official_deaths", "fatal_crashes": "official_fatal_crashes"})
for lab, s in [("kn_en", u[u.in_kn_en]), ("all", u)]:
    g = s.groupby("month").agg(**{f"news_crashes_{lab}": ("crash_id", "size"), f"news_deaths_{lab}": ("deaths", "sum")}).reset_index()
    mo = mo.merge(g, on="month", how="left")
mo = mo.fillna(0)
mo["recall_deaths_all"] = (mo.news_deaths_all / mo.official_deaths).round(3)
mo.to_csv(D / f"killcheck_recall_by_month{ALL}.csv", index=False)
mo["half"] = ["H1 (Jan-Jun)" if i < 6 else "H2 (Jul-Dec)" for i in range(len(mo))]
hy = mo.groupby("half")[[c for c in mo.columns if c.startswith(("official", "news"))]].sum().reset_index()
for lab in ("kn_en", "all"):
    hy[f"recall_deaths_{lab}"] = (hy[f"news_deaths_{lab}"] / hy.official_deaths).round(3)
    hy[f"recall_crashes_{lab}"] = (hy[f"news_crashes_{lab}"] / hy.official_fatal_crashes).round(3)
hy.to_csv(D / f"killcheck_recall_by_half{ALL}.csv", index=False)
print(hy.to_string())
print("Spearman(official, all-outlet news deaths by month):", round(mo.official_deaths.corr(mo.news_deaths_all, method="spearman"), 2))

# ---------------------------------------------------------------- overlap and severity
ov = [dict(set=k, crashes=int(m.sum()), deaths=int(u.deaths[m].sum())) for k, m in {
    "Kannada/English and Marathi": u.in_kn_en & u.in_marathi, "Kannada/English only": u.in_kn_en & ~u.in_marathi,
    "Marathi only": ~u.in_kn_en & u.in_marathi}.items()]
for ol in sorted(set(code["outlet"])):
    m = u.outlets_all == ol
    ov.append(dict(set=f"unique to {ol}", crashes=int(m.sum()), deaths=int(u.deaths[m].sum())))
pd.DataFrame(ov).to_csv(D / f"killcheck_overlap{ALL}.csv", index=False)
print(pd.DataFrame(ov).to_string())
sev = []
for lab, s in [("Kannada + English", u[u.in_kn_en]), ("Marathi only", u[~u.in_kn_en]), ("All-outlet union", u)]:
    one, multi = s[s.deaths == 1], s[s.deaths >= 2]
    sev.append(dict(scope=lab, crashes=len(s), deaths=int(s.deaths.sum()), single_death_crashes=len(one),
                    multi_death_crashes=len(multi), deaths_in_multi=int(multi.deaths.sum()),
                    share_single=round(len(one) / max(len(s), 1), 3), deaths_per_crash=round(s.deaths.sum() / max(len(s), 1), 2)))
sev.append(dict(scope="Official 2022 (combined units)", crashes=fcr, deaths=tot, single_death_crashes="",
                multi_death_crashes="", deaths_in_multi="", share_single="", deaths_per_crash=round(tot / fcr, 2)))
sev = pd.DataFrame(sev)
sev.to_csv(D / f"killcheck_severity{ALL}.csv", index=False)
print(sev.to_string())
print("deaths per crash (union):", u.deaths.value_counts().sort_index().to_dict())
print("taluk deaths (union):", u.groupby("taluk").deaths.sum().sort_values(ascending=False).to_dict())
print("new crash id map:", newid)
print("coding rows:", len(code), code.groupby(["in_district", "fatal", "scope"]).size().to_dict())
