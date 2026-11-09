"""Recompute the numbers reported in the paper from data/ and outputs/; exit 1 on any failure.

Counts, recall, the assumption-free bounds and the monthly statistics are recomputed from the coded crash files and the
police benchmark. Model quantities are read from the committed model outputs (refit with src/06_selection_model.py).
Expected values in results/expected_key_results.json are the values printed in the manuscript.
"""
import json, pathlib, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr, chi2_contingency

R = pathlib.Path(__file__).resolve().parent; D = R / "data"; O = R / "outputs"
E = json.loads((R / "results/expected_key_results.json").read_text(encoding="utf-8"))
fails, n = [], 0


def check(name, got, want, tol=0):
    global n; n += 1; ok = abs(float(got) - float(want)) <= tol + 1e-9
    print(f"{'PASS' if ok else 'FAIL'}  {name:66s} got {float(got):11.4f}  expected {float(want):11.4f}")
    if not ok: fails.append(name)


def p1(x): return round(100 * x, 1)


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DIST = {"dakshina_kannada": ("official_benchmark.csv", "DK revenue district", "killcheck_crashes.csv"),
        "belagavi": ("official_benchmark_belagavi.csv", "Belagavi revenue district", "killcheck_crashes_belagavi_all.csv")}
for key, (bf, pref, cf) in DIST.items():
    e = E[key]; b = pd.read_csv(D / bf); b = b[(b.year == 2022) & b.unit.str.startswith(pref)]
    mon = b[b.level == "monthly"].set_index("period").reindex(MONTHS)
    F, Dd = int(mon.fatal_crashes.sum()), int(b[b.level == "annual"].deaths.iloc[0])
    check(f"{key}: police fatal crashes", F, e["fatal_crashes"]); check(f"{key}: police deaths", Dd, e["deaths"])
    check(f"{key}: monthly deaths sum to annual", mon.deaths.sum(), Dd); check(f"{key}: road-user deaths sum to annual", b[b.level == "road_user"].deaths.sum(), Dd)
    c = pd.read_csv(D / cf)
    check(f"{key}: news crashes", len(c), e["news_crashes"]); check(f"{key}: news deaths", c.deaths.sum(), e["news_deaths"])
    check(f"{key}: recall of deaths (%)", p1(c.deaths.sum() / Dd), e["recall_deaths_pct"]); check(f"{key}: recall of fatal crashes (%)", p1(len(c) / F), e["recall_crashes_pct"])
    check(f"{key}: news deaths per crash", round(c.deaths.sum() / len(c), 2), e["news_deaths_per_crash"]); check(f"{key}: police deaths per crash", round(Dd / F, 2), e["police_deaths_per_crash"])
    # assumption-free bounds
    s, m = int((c.deaths == 1).sum()), int((c.deaths >= 2).sum()); En = int(c.deaths.sum() - len(c)); Rr = (Dd - F) - En
    Mlo, Mhi = m + (Rr > 0), m + Rr
    check(f"{key}: deaths beyond the first, police", Dd - F, e["excess_police"]); check(f"{key}: deaths beyond the first, news", En, e["excess_news"])
    check(f"{key}: share of deaths beyond the first reported (%)", p1(En / (Dd - F)), e["excess_recall_pct"])
    check(f"{key}: bound, single-death recall low (%)", p1(s / (F - Mlo)), e["bound_single_pct"][0]); check(f"{key}: bound, single-death recall high (%)", p1(s / (F - Mhi)), e["bound_single_pct"][1])
    check(f"{key}: bound, multi-death recall low (%)", p1(m / Mhi), e["bound_multi_pct"][0]); check(f"{key}: bound, multi-death recall high (%)", p1(m / Mlo), e["bound_multi_pct"][1])
    check(f"{key}: bound, police multi-death crashes low", Mlo, e["bound_M"][0]); check(f"{key}: bound, police multi-death crashes high", Mhi, e["bound_M"][1])
    # monthly
    mn = pd.to_datetime(c.crash_date).dt.month; nd = np.array([c.deaths[mn == k].sum() for k in range(1, 13)]); od = mon.deaths.values.astype(int)
    chi = chi2_contingency(np.array([nd, od - nd]))
    check(f"{key}: monthly Spearman rho", round(spearmanr(od, nd).statistic, 2), e["spearman"]); check(f"{key}: monthly chi-square", round(chi.statistic, 1), e["chi2"])
    check(f"{key}: monthly chi-square p", round(chi.pvalue, 3), e["chi2_p"], 0.0005)
    if "monthly_recall_range_pct" in e:
        check(f"{key}: lowest monthly recall (%)", p1((nd / od).min()), e["monthly_recall_range_pct"][0]); check(f"{key}: highest monthly recall (%)", p1((nd / od).max()), e["monthly_recall_range_pct"][1])
    # model outputs
    a = pd.read_csv(O / "model_a_severity.csv"); dname = {"dakshina_kannada": "Dakshina Kannada", "belagavi": "Belagavi"}[key]
    g = lambda v, k: a[(a.variant == v) & (a.district == dname)].iloc[0][k]
    for k, pre, f_, d_ in (("pi1", "pi1", 100, 1), ("pi2", "pi2", 100, 1), ("or", "or_", 1, 1)):
        for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e[f"model_{k}"]):
            check(f"{key}: model {k} {lab}", round(f_ * g("main", f"{pre}_{suf}"), d_), want)
    check(f"{key}: realized police multi-death crashes low", g("main", "M_official_lo"), e["model_M"][0]); check(f"{key}: realized police multi-death crashes high", g("main", "M_official_hi"), e["model_M"][1])
    for v in ("gradient", "drop_largest"):
        if f"or_{v}" in e:
            for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e[f"or_{v}"]): check(f"{key}: odds ratio {v} {lab}", round(g(v, f"or__{suf}"), 1), want)
    rb = pd.read_csv(O / "model_b_road_user.csv"); rb = rb[rb.district == dname].set_index("road_user")
    for ru in ("pedestrian", "two_wheeler"):
        for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e[f"recall_{ru}_pct"]): check(f"{key}: recall {ru} {lab} (%)", round(100 * rb.loc[ru, f"recall_{suf}"], 1), want)
    for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e["or_pedestrian"]): check(f"{key}: OR pedestrian vs two-wheeler {lab}", round(rb.loc["OR pedestrian vs two-wheeler", f"recall_{suf}"], 2), want)
    check(f"{key}: news/police share, pedestrian", round(rb.loc["pedestrian", "share_ratio_med"], 2), e["share_ratio_pedestrian"]); check(f"{key}: news/police share, car", round(rb.loc["car", "share_ratio_med"], 2), e["share_ratio_car"])
    tr = pd.read_csv(O / "transport.csv").set_index("target").loc[dname]
    check(f"{key}: transport, crude", round(tr.crude_correction_med), e["transport_crude"])
    for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e["transport_severity"]): check(f"{key}: transport, severity {lab}", round(tr[f"severity_correction_{suf}"]), want)
    for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e["transport_own"]): check(f"{key}: own-district correction {lab}", round(tr[f"own_district_severity_correction_{suf}"]), want)

# Belagavi outlet and language groups
a = pd.read_csv(D / "killcheck_crashes_belagavi_all.csv"); e = E["belagavi"]
for lab, msk in (("kannada", a.in_kannada), ("english", a.in_english), ("marathi", a.in_marathi)):
    check(f"belagavi: any {lab} outlet, deaths (% of police)", p1(a.deaths[msk].sum() / 913), e[f"any_{lab}_pct"])
mo = a[~a.in_kn_en]
check("belagavi: Marathi-only crashes", len(mo), e["marathi_only_crashes"]); check("belagavi: Marathi-only deaths", mo.deaths.sum(), e["marathi_only_deaths"])
check("belagavi: Marathi-only single-death crashes", (mo.deaths == 1).sum(), e["marathi_only_single"])
kn = pd.read_csv(D / "killcheck_crashes_belagavi.csv"); check("belagavi: Kannada/English file is the in_kn_en subset", len(kn), int(a.in_kn_en.sum()))
k2 = pd.read_csv(O / "model_a_severity_kn_en.csv"); k2 = k2[(k2.variant == "main") & (k2.district == "Belagavi")].iloc[0]
check("belagavi, Kannada/English only: pi1 median (%)", round(100 * k2.pi1_med, 1), e["kn_en_pi1_pct"])
for lab, suf, want in zip(("median", "lo", "hi"), ("med", "lo", "hi"), e["kn_en_or"]): check(f"belagavi, Kannada/English only: OR {lab}", round(k2[f"or__{suf}"], 1), want)
summ = {"dakshina_kannada": pd.read_csv(D / "killcheck_summary.csv"), "belagavi": pd.concat([pd.read_csv(D / "killcheck_summary_belagavi.csv"), pd.read_csv(D / "killcheck_summary_belagavi_all.csv")])}
for key, outlets in E["outlet_deaths_pct"].items():
    for o, want in outlets.items():
        r = summ[key][summ[key].scope == f"outlet: {o}"].iloc[0]; check(f"{key}: {o} deaths (% of police)", p1(r.deaths / r.official_deaths), want)
for key, fs in (("dakshina_kannada", ["killcheck_coding.csv"]), ("belagavi", ["killcheck_coding_belagavi.csv", "killcheck_coding_belagavi_mr.csv"])):
    cd_ = pd.concat([pd.read_csv(D / f) for f in fs]); Dd = E[key]["deaths"]; nd = E[key]["news_deaths"]
    bl = cd_[(cd_.in_district == "Y") & (cd_.fatal == "Y") & (cd_.scope == "borderline")].drop_duplicates("crash_id").deaths.sum()
    un = cd_[(cd_.in_district == "U") & (cd_.fatal == "Y")].drop_duplicates(["crash_date", "place"]).deaths.sum()
    check(f"{key}: recall with borderline events (%)", p1((nd + bl) / Dd), E[key]["recall_with_borderline_pct"])
    check(f"{key}: recall, undetermined location counted in-district (%)", p1((nd + un) / Dd), E[key]["recall_with_undetermined_pct"])
arts = sum(len(pd.read_csv(D / f)) for f in ("killcheck_articles.csv", "killcheck_articles_belagavi.csv", "killcheck_articles_belagavi_mr.csv"))
check("articles fetched and screened", arts, E["articles_screened"])
dg = json.loads((O / "diagnostics.json").read_text()); dk2 = json.loads((O / "diagnostics_kn_en.json").read_text()); allfits = list(dg.values()) + list(dk2.values())
check("max R-hat, all fits incl. sensitivity", round(max(v["rhat"] for v in allfits), 3), E["max_rhat"], 0.0005)
check("every bulk ESS exceeds 2,000 (1 = yes)", int(min(v["ess"] for v in allfits) > E["min_ess_floor"]), 1)
check("divergent transitions, all fits", sum(v["divergences"] for v in allfits), 0)
for k, want in (("A_main_Dakshina Kannada", E["dakshina_kannada"]["configurations"]), ("A_main_Belagavi", E["belagavi"]["configurations"])):
    check(f"enumerated configurations, {k[7:]}", dg[k]["n_configurations"], want)
print(f"\n{n - len(fails)}/{n} checks passed")
sys.exit(1 if fails else 0)
