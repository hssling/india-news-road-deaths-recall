"""Severity and road-user selection in news reports of road deaths: Dakshina Kannada and Belagavi, 2022.

Inputs (all aggregate; no article text):
  data/killcheck_crashes*.csv          de-duplicated news crashes (deaths, victim type)
  data/official_benchmark*.csv         KSP 2022 fatal crashes, deaths, deaths by road-user type

Three analyses:
  1. Partial identification (no model). D - F = sum over crashes of (k - 1) is known from the police totals, and the
     news gives the same sum for the crashes it reports. This yields exact recall of "excess" deaths and sharp bounds on
     recall of single-death and multi-death crashes, using only: every news crash is an official crash.
  2. Model A (severity). Crash size k - 1 ~ NegBin(lambda, r) among official fatal crashes; recall pi(k) = pi1 for
     k = 1 and pi2 for k >= 2 (step model; sensitivity: monotone logit gradient in log k among k >= 2).
     Likelihood: D - F ~ NegBin(F lambda, F r)  [sum of F iid NB2]; news crash counts by size, plus the unreported
     cell, ~ Multinomial(F, p_k pi(k)). Fitted per district.
  3. Model B (road-user type). Recall of fatal crashes by victim type g (pedestrian, two-wheeler, car/LMV, other):
     logit q_dg = alpha_d + gamma_g + delta_dg, delta_dg ~ N(0, sigma). Official fatal crashes by type are not
     published, so N_dg = deaths_dg * F_d / D_d. Unknown victim type in news (DK) is handled as a latent split.
Then transport: use one district's recall to correct the other district's news count.

Usage:  python src/06_selection_model.py [--belagavi-crashes FILE ...] [--tag TAG] [--quick]
"""
import argparse, json, os, pathlib
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
import numpy as np, pandas as pd
import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS

P = pathlib.Path(__file__).resolve().parents[1]; D = P / "data"; O = P / "outputs"; O.mkdir(exist_ok=True)
ap = argparse.ArgumentParser()
ap.add_argument("--belagavi-crashes", nargs="+", default=["killcheck_crashes_belagavi.csv"])
ap.add_argument("--tag", default="")
ap.add_argument("--quick", action="store_true")
args = ap.parse_args()
NW, NS = (500, 500) if args.quick else (2000, 2000)
K = 10                                                     # crash sizes 1..K, tail lumped into K
GROUPS = ["pedestrian", "two_wheeler", "car", "other"]
OFF_MAP = {"pedestrian": "pedestrian", "two_wheeler": "two_wheeler", "car_taxi_van_lmv": "car", "truck_lorry": "other",
           "bus": "other", "autorickshaw": "other", "other_motor_vehicle": "other", "bicycle": "other", "other_non_motor": "other"}
NEWS_MAP = {"pedestrian": "pedestrian", "two_wheeler": "two_wheeler", "car": "car", "autorickshaw": "other",
            "bicycle": "other", "bus": "other", "truck": "other", "other": "other", "unknown": "unknown"}


def official(fname, combined_prefix):
    b = pd.read_csv(D / fname); b = b[b.year == 2022]
    ann = b[(b.level == "annual") & b.unit.str.startswith(combined_prefix)]
    assert len(ann) == 1, (fname, ann)
    mon = b[(b.level == "monthly") & b.unit.str.startswith(combined_prefix)]
    F, Dd = int(mon.fatal_crashes.sum()), int(ann.deaths.iloc[0])
    assert int(mon.deaths.sum()) == Dd
    ru = b[(b.level == "road_user") & b.unit.str.startswith(combined_prefix)]
    assert int(ru.deaths.sum()) == Dd
    g = ru.assign(g=ru.road_user.map(OFF_MAP)).groupby("g").deaths.sum().reindex(GROUPS).astype(int)
    return F, Dd, g


def news(files):
    c = pd.concat([pd.read_csv(D / f) for f in files], ignore_index=True)
    assert c.crash_id.is_unique, "duplicate crash ids across files"
    c["g"] = c.victim_types.str.split(";").str[0].map(NEWS_MAP)
    assert c.g.notna().all(), c[c.g.isna()].victim_types.unique()
    return c


dists = {"Dakshina Kannada": dict(off=official("official_benchmark.csv", "DK revenue district"), crashes=["killcheck_crashes.csv"]),
         "Belagavi": dict(off=official("official_benchmark_belagavi.csv", "Belagavi revenue district"), crashes=args.belagavi_crashes)}
for d, v in dists.items():
    v["news"] = news(v["crashes"])
    F, Dd, g = v["off"]
    print(f"{d}: official F={F} D={Dd} by type={g.to_dict()} | news crashes={len(v['news'])} deaths={v['news'].deaths.sum()}")

# ---------------------------------------------------------------- 1. partial identification
rows = []
for d, v in dists.items():
    F, Dd, _ = v["off"]; c = v["news"]
    s = int((c.deaths == 1).sum()); m = int((c.deaths >= 2).sum()); e_news = int(c.deaths.sum() - len(c)); e_off = Dd - F
    assert e_news <= e_off, d
    R = e_off - e_news                                      # excess deaths in crashes the news missed
    M_lo, M_hi = m + (1 if R > 0 else 0), m + R             # official multi-death crashes: sharp, assumption-free
    M_lo_cap = m + int(np.ceil(R / (K - 1)))                # if no crash exceeds K deaths
    rows.append(dict(district=d, official_fatal_crashes=F, official_deaths=Dd, official_excess=e_off,
                     news_crashes=len(c), news_deaths=int(c.deaths.sum()), news_single=s, news_multi=m, news_excess=e_news,
                     unseen_excess=R, recall_deaths=c.deaths.sum() / Dd, recall_crashes=len(c) / F, recall_excess_exact=e_news / e_off,
                     M_official_lo=M_lo, M_official_lo_capK=M_lo_cap, M_official_hi=M_hi,
                     recall_single_lo=s / (F - M_lo), recall_single_hi=s / (F - M_hi),
                     recall_multi_lo=m / M_hi, recall_multi_hi=m / M_lo, recall_multi_hi_capK=m / M_lo_cap,
                     log_or_lo=np.log((m / M_hi) / (1 - m / M_hi)) - np.log((s / (F - M_lo)) / (1 - s / (F - M_lo)))))
bounds = pd.DataFrame(rows); bounds.to_csv(O / f"bounds{args.tag}.csv", index=False)
print(bounds.T.to_string())


# ---------------------------------------------------------------- 2. Model A: severity selection (finite population)
# The 2022 official crashes are a fixed finite population: n_k crashes of size k with sum n_k = F and sum k n_k = D.
# News crashes m_k ~ Binomial(n_k, pi(k)), with n_k >= m_k. Every configuration n consistent with (F, D, m) is
# enumerated exactly: the unseen excess R = (D - F) - (news excess) is a partition of R into parts (k - 1), k = 2..K.
# Prior over configurations: Multinomial(F, p), p_k = truncated NegBin2(lambda, r) on k - 1.
def partitions(n, maxpart):
    if n == 0:
        yield []
        return
    for p_ in range(min(n, maxpart), 0, -1):
        for rest in partitions(n - p_, p_):
            yield [p_] + rest


def configs(F, Dd, m):                                       # m: news counts by size k = 1..K
    R = (Dd - F) - int(((np.arange(1, K + 1) - 1) * m).sum())
    assert R >= 0
    rows = []
    for part in partitions(R, K - 1):
        n = m.copy()
        for j in part: n[j] += 1                              # part j: an unreported crash of size j + 1 (index j)
        n[0] = F - n[1:].sum()
        rows.append(n)
    n = np.array(rows)
    assert (n[:, 0] >= m[0]).all() and (n.sum(1) == F).all() and ((n * np.arange(1, K + 1)).sum(1) == Dd).all()
    return n


def size_probs(lam, r):
    p = jnp.exp(dist.NegativeBinomial2(lam, r).log_prob(jnp.arange(K)))
    return p / p.sum()                                       # P(k = 1..K), truncated at K


def lchoose(n, k): return jax.scipy.special.gammaln(n + 1) - jax.scipy.special.gammaln(k + 1) - jax.scipy.special.gammaln(n - k + 1)


def model_a(F, n_cfg, m, gradient=False):
    lam = numpyro.sample("lam", dist.Exponential(5.0))
    r = numpyro.sample("r", dist.LogNormal(0.0, 1.5))
    pi1 = numpyro.sample("pi1", dist.Beta(1, 1)); pi2 = numpyro.sample("pi2", dist.Beta(1, 1))
    k = jnp.arange(1, K + 1)
    if gradient:
        b = numpyro.sample("b", dist.HalfNormal(1.0))
        pik = jnp.where(k == 1, pi1, jax.nn.sigmoid(jax.scipy.special.logit(pi2) + b * jnp.log(k / 2.0)))
    else:
        pik = jnp.where(k == 1, pi1, pi2)
    pk = size_probs(lam, r)
    lprior = jax.scipy.special.gammaln(F + 1.0) - jax.scipy.special.gammaln(n_cfg + 1.0).sum(1) + (n_cfg * jnp.log(pk)).sum(1)
    llik = (lchoose(n_cfg, m) + m * jnp.log(pik) + (n_cfg - m) * jnp.log1p(-pik)).sum(1)
    lw = lprior + llik
    numpyro.factor("ll", jax.scipy.special.logsumexp(lw))
    numpyro.deterministic("lw", lw); numpyro.deterministic("pik", pik); numpyro.deterministic("pk", pk)


def run(model, seed, accept=0.95, **kw):
    mc = MCMC(NUTS(model, target_accept_prob=accept), num_warmup=NW, num_samples=NS, num_chains=4, progress_bar=False)
    mc.run(jax.random.PRNGKey(seed), **kw)
    s = mc.get_samples(); diag = numpyro.diagnostics.summary(mc.get_samples(group_by_chain=True))
    rhat = max(float(np.nanmax(v["r_hat"])) for kk, v in diag.items() if kk in ("lam", "r", "pi1", "pi2", "b", "alpha", "gamma", "delta", "sigma", "u"))
    ess = min(float(np.nanmin(v["n_eff"])) for kk, v in diag.items() if kk in ("lam", "r", "pi1", "pi2", "b", "alpha", "gamma", "delta", "sigma", "u"))
    div = int(mc.get_extra_fields()["diverging"].sum())
    return {k: np.asarray(v) for k, v in s.items()}, dict(rhat=rhat, ess=ess, divergences=div)


def q(x): return dict(med=float(np.median(x)), lo=float(np.percentile(x, 2.5)), hi=float(np.percentile(x, 97.5)))


res, diags, draws = [], {}, {}
rng = np.random.default_rng(2022)
for variant, grad, drop_big in (("main", False, False), ("gradient", True, False), ("drop_largest", False, True)):
    for i, (d, v) in enumerate(dists.items()):
        F, Dd, _ = v["off"]; c = v["news"]
        if drop_big:                                        # remove the largest news crash and its deaths from both sides
            big = c.deaths.max(); assert (c.deaths == big).sum() == 1
            c = c[c.deaths != big]; F, Dd = F - 1, Dd - big
        m = np.bincount(np.clip(c.deaths.values, 1, K), minlength=K + 1)[1:]
        n_cfg = configs(F, Dd, m)
        s, dg = run(model_a, 11 + i, F=float(F), n_cfg=jnp.array(n_cfg, dtype=jnp.float32), m=jnp.array(m, dtype=jnp.float32), gradient=grad)
        dg["n_configurations"] = int(len(n_cfg)); diags[f"A_{variant}_{d}"] = dg
        w = np.exp(s["lw"] - s["lw"].max(1, keepdims=True)); w /= w.sum(1, keepdims=True)
        pick = np.array([rng.choice(len(n_cfg), p=wi) for wi in w])
        M = n_cfg[pick, 1:].sum(1)                            # realised official multi-death crashes, per draw
        logor = np.log(s["pi2"] / (1 - s["pi2"])) - np.log(s["pi1"] / (1 - s["pi1"]))
        out = dict(variant=variant, district=d, pi1=q(s["pi1"]), pi2=q(s["pi2"]), log_or=q(logor), or_=q(np.exp(logor)),
                   M_official=q(M), recall_multi_realised=q(m[1:].sum() / M), recall_single_realised=q(m[0] / (F - M)),
                   r=q(s["r"]), lam=q(s["lam"]))
        res.append(out)
        if variant == "main": draws[d] = s
        print(variant, d, {k: (round(v_["med"], 4), round(v_["lo"], 4), round(v_["hi"], 4)) for k, v_ in out.items() if isinstance(v_, dict)}, dg)
flat = [dict(variant=r_["variant"], district=r_["district"], **{f"{k}_{s_}": v_[s_] for k, v_ in r_.items() if isinstance(v_, dict) for s_ in ("med", "lo", "hi")}) for r_ in res]
pd.DataFrame(flat).to_csv(O / f"model_a_severity{args.tag}.csv", index=False)

# ---------------------------------------------------------------- transport: correct district X's news count with district Y's recall
tr = []
for target, source in (("Belagavi", "Dakshina Kannada"), ("Dakshina Kannada", "Belagavi")):
    c = dists[target]["news"]; Dd = dists[target]["off"][1]; s_ = draws[source]
    single = (c.deaths == 1).sum(); multi_deaths = c.deaths[c.deaths >= 2].sum(); total = c.deaths.sum()
    Ds = dists[source]["off"][1]; crude = np.full(len(s_["pi1"]), total * Ds / dists[source]["news"].deaths.sum())   # deaths / source death recall
    sev = single / s_["pi1"] + multi_deaths / s_["pi2"]
    own = draws[target]; own_sev = single / own["pi1"] + multi_deaths / own["pi2"]
    tr.append(dict(target=target, recall_from=source, official_deaths=int(Dd), news_deaths=int(total),
                   crude_correction=q(crude), severity_correction=q(sev), own_district_severity_correction=q(own_sev)))
trf = [dict(target=t["target"], recall_from=t["recall_from"], official_deaths=t["official_deaths"], news_deaths=t["news_deaths"],
            **{f"{k}_{s2}": t[k][s2] for k in ("crude_correction", "severity_correction", "own_district_severity_correction") for s2 in ("med", "lo", "hi")}) for t in tr]
pd.DataFrame(trf).to_csv(O / f"transport{args.tag}.csv", index=False); print(pd.DataFrame(trf).T.to_string())

# ---------------------------------------------------------------- 3. Model B: road-user type
dn = list(dists); nd, ng = len(dn), len(GROUPS)
N = np.zeros((nd, ng), int); Y = np.zeros((nd, ng), int); U = np.zeros(nd, int); DEATHS = np.zeros((nd, ng), int); NEWSD = np.zeros((nd, ng), int)
for i, d in enumerate(dn):
    F, Dd, g = dists[d]["off"]; c = dists[d]["news"]
    DEATHS[i] = g.values; N[i] = np.round(g.values * F / Dd).astype(int)
    vc = c.g.value_counts(); Y[i] = [int(vc.get(x, 0)) for x in GROUPS]; U[i] = int(vc.get("unknown", 0))
    NEWSD[i] = [int(c.deaths[c.g == x].sum()) for x in GROUPS]
has_u = U > 0
print("Model B cells N (official fatal crashes, approx):\n", N, "\nY:\n", Y, "\nunknown:", U)


def model_b(N, Y, U):
    alpha = numpyro.sample("alpha", dist.Normal(-1.5, 2.0).expand([nd]))
    gamma = numpyro.sample("gamma", dist.Normal(0.0, 1.5).expand([ng - 1]))      # two-wheeler (index 1) is the reference
    gam = jnp.concatenate([gamma[:1], jnp.zeros(1), gamma[1:]])
    sigma = numpyro.sample("sigma", dist.HalfNormal(0.5))
    delta = numpyro.sample("delta", dist.Normal(0.0, 1.0).expand([nd, ng]))
    qdg = jax.nn.sigmoid(alpha[:, None] + gam[None, :] + sigma * delta)
    u = numpyro.sample("u", dist.Beta(1, 1).expand([nd]))
    u = jnp.where(jnp.array(has_u), u, 0.0)
    numpyro.sample("y", dist.Binomial(N, qdg * (1 - u[:, None])), obs=Y)
    numpyro.sample("unk", dist.Poisson(jnp.clip(u * (N * qdg).sum(1), 1e-9)), obs=U)
    numpyro.deterministic("q", qdg)


sb, dgb = run(model_b, 99, accept=0.99, N=jnp.array(N), Y=jnp.array(Y), U=jnp.array(U)); diags["B"] = dgb
qd = sb["q"]
rb = []
for i, d in enumerate(dn):
    w = DEATHS[i] / DEATHS[i].sum()
    news_share = qd[:, i, :] * w / (qd[:, i, :] * w).sum(1, keepdims=True)
    for j, gname in enumerate(GROUPS):
        rb.append(dict(district=d, road_user=gname, official_deaths=int(DEATHS[i, j]), official_crashes_approx=int(N[i, j]),
                       news_crashes=int(Y[i, j]), news_deaths=int(NEWSD[i, j]),
                       **{f"recall_{k}": v for k, v in q(qd[:, i, j]).items()},
                       official_share=float(w[j]), **{f"news_share_{k}": v for k, v in q(news_share[:, j]).items()},
                       **{f"share_ratio_{k}": v for k, v in q(news_share[:, j] / w[j]).items()}))
    or_ped = qd[:, i, 0] / (1 - qd[:, i, 0]) / (qd[:, i, 1] / (1 - qd[:, i, 1]))
    rb.append(dict(district=d, road_user="OR pedestrian vs two-wheeler", **{f"recall_{k}": v for k, v in q(or_ped).items()}))
rbf = pd.DataFrame(rb); rbf.to_csv(O / f"model_b_road_user{args.tag}.csv", index=False)
print(rbf.round(3).to_string())

# ---------------------------------------------------------------- monthly heterogeneity (descriptive): chi-square of news deaths vs official
mon = []
from scipy.stats import spearmanr, chi2_contingency
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
for d, fb, pref in (("Dakshina Kannada", "official_benchmark.csv", "DK revenue district"), ("Belagavi", "official_benchmark_belagavi.csv", "Belagavi revenue district")):
    b = pd.read_csv(D / fb); b = b[(b.year == 2022) & (b.level == "monthly") & b.unit.str.startswith(pref)].set_index("period").reindex(MONTHS)
    c = dists[d]["news"]; mnum = pd.to_datetime(c.crash_date).dt.month
    nd_ = np.array([c.deaths[mnum == m].sum() for m in range(1, 13)]); od = b.deaths.values.astype(int)
    rho = spearmanr(od, nd_).statistic; chi = chi2_contingency(np.array([nd_, od - nd_]))
    mon.append(dict(district=d, spearman_official_vs_news=float(rho), chi2=float(chi.statistic), df=int(chi.dof), p=float(chi.pvalue),
                    recall_min=float((nd_ / od).min()), recall_max=float((nd_ / od).max()),
                    h1_recall=float(nd_[:6].sum() / od[:6].sum()), h2_recall=float(nd_[6:].sum() / od[6:].sum())))
pd.DataFrame(mon).to_csv(O / f"monthly{args.tag}.csv", index=False); print(pd.DataFrame(mon).to_string())
json.dump(diags, open(O / f"diagnostics{args.tag}.json", "w"), indent=1); print(json.dumps(diags, indent=1))
