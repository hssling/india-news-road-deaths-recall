"""Figures (greyscale, Arial, 600 dpi TIFF + PNG).
Figure 1 Recall of official fatal crashes in news reports, 2022: (A) by crash size (sharp bounds as bars; finite-
         population posterior as points with 95% CrI); (B) by victim road-user type (Model B, median and 95% CrI).
Figure 2 Monthly recall of official road deaths (Jeffreys 95% interval), with the annual recall as a dashed line.
Usage: python src/07_figures.py [--tag TAG] [--belagavi-crashes FILE ...]
"""
import argparse, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy.stats import beta
from PIL import Image

P = pathlib.Path(__file__).resolve().parents[1]; D = P / "data"; O = P / "outputs"
ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="")
ap.add_argument("--belagavi-crashes", nargs="+", default=["killcheck_crashes_belagavi.csv"]); args = ap.parse_args()
K, DG, MG, LG = "#000000", "#4d4d4d", "#8c8c8c", "#d0d0d0"
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": 8, "axes.linewidth": 0.6})
pct = FuncFormatter(lambda v, _: f"{100 * v:g}%")
DIST = ["Dakshina Kannada", "Belagavi"]; MK = {"Dakshina Kannada": ("o", K, K), "Belagavi": ("s", K, "white")}
OFF = 0.13


def save(fig, name):
    for ax in fig.axes:
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.savefig(O / f"{name}{args.tag}.png", dpi=600)
    Image.open(O / f"{name}{args.tag}.png").convert("L").save(O / f"{name}{args.tag}.tif", dpi=(600, 600), compression="tiff_lzw")
    plt.close(fig)


bd = pd.read_csv(O / f"bounds{args.tag}.csv").set_index("district")
ma = pd.read_csv(O / f"model_a_severity{args.tag}.csv"); ma = ma[ma.variant == "main"].set_index("district")
mb = pd.read_csv(O / f"model_b_road_user{args.tag}.csv"); mb = mb[~mb.road_user.str.startswith("OR")]

fig, (a, b) = plt.subplots(1, 2, figsize=(7.09, 3.2), gridspec_kw=dict(width_ratios=[1, 1.35]))
for i, d in enumerate(DIST):
    m, ec, fc = MK[d]; dx = (i - 0.5) * 2 * OFF
    for x, lo, hi, med, clo, chi in ((0, bd.loc[d, "recall_single_hi"], bd.loc[d, "recall_single_lo"], ma.loc[d, "recall_single_realised_med"],
                                      ma.loc[d, "recall_single_realised_lo"], ma.loc[d, "recall_single_realised_hi"]),
                                     (1, bd.loc[d, "recall_multi_lo"], bd.loc[d, "recall_multi_hi"], ma.loc[d, "recall_multi_realised_med"],
                                      ma.loc[d, "recall_multi_realised_lo"], ma.loc[d, "recall_multi_realised_hi"])):
        a.add_patch(plt.Rectangle((x + dx - 0.07, lo), 0.14, max(hi - lo, 1e-4), color=LG, lw=0, zorder=1))
        a.plot([x + dx, x + dx], [clo, chi], color=DG, lw=1.0, zorder=2)
        a.plot(x + dx, med, m, mec=ec, mfc=fc, ms=5, zorder=3, label=d if x == 0 else None)
    a.plot(2 + dx, bd.loc[d, "recall_excess_exact"], m, mec=ec, mfc=fc, ms=5)
a.set_yscale("log"); a.set_ylim(0.015, 1.05); a.yaxis.set_major_formatter(pct)
a.set_xticks([0, 1, 2]); a.set_xticklabels(["Single-death\ncrashes", "Multi-death\ncrashes", "Deaths after\nthe first"])
a.set_xlim(-0.55, 2.55); a.tick_params(axis="x", labelsize=7); a.set_ylabel("Share of official crashes or deaths in the news")
a.legend(frameon=False, fontsize=7, loc="lower right")
a.text(-0.2, 1.03, "A", transform=a.transAxes, fontsize=10, fontweight="bold")
LAB = {"pedestrian": "Pedestrian", "two_wheeler": "Two-wheeler", "car": "Car, jeep\nor van", "other": "Other"}
for i, d in enumerate(DIST):
    m, ec, fc = MK[d]; t = mb[mb.district == d].reset_index(drop=True); dx = (i - 0.5) * 2 * OFF
    for j, r in t.iterrows():
        b.plot([j + dx, j + dx], [r.recall_lo, r.recall_hi], color=DG, lw=1.0)
        b.plot(j + dx, r.recall_med, m, mec=ec, mfc=fc, ms=5)
b.set_yscale("log"); b.set_ylim(0.004, 1.05); b.yaxis.set_major_formatter(pct)
b.set_xticks(range(4)); b.set_xticklabels([LAB[g] for g in mb.road_user.unique()]); b.set_xlim(-0.5, 3.5)
b.set_ylabel("Share of official fatal crashes in the news")
b.text(-0.16, 1.03, "B", transform=b.transAxes, fontsize=10, fontweight="bold")
fig.tight_layout(w_pad=2.5); save(fig, "Figure_1")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
fig, axs = plt.subplots(1, 2, figsize=(7.09, 2.8), sharey=True)
for ax, d, fb, pref, files in ((axs[0], "Dakshina Kannada", "official_benchmark.csv", "DK revenue district", ["killcheck_crashes.csv"]),
                               (axs[1], "Belagavi", "official_benchmark_belagavi.csv", "Belagavi revenue district", args.belagavi_crashes)):
    bm = pd.read_csv(D / fb); bm = bm[(bm.year == 2022) & (bm.level == "monthly") & bm.unit.str.startswith(pref)].set_index("period").reindex(MONTHS)
    c = pd.concat([pd.read_csv(D / f) for f in files]); mn = pd.to_datetime(c.crash_date).dt.month
    nd = np.array([c.deaths[mn == k].sum() for k in range(1, 13)]); od = bm.deaths.values.astype(int)
    lo = beta.ppf(0.025, nd + 0.5, od - nd + 0.5); hi = beta.ppf(0.975, nd + 0.5, od - nd + 0.5); lo[nd == 0] = 0
    x = np.arange(1, 13)
    ax.vlines(x, lo, hi, color=DG, lw=1.0); ax.plot(x, nd / od, MK[d][0], mec=K, mfc=MK[d][2], ms=4.5)
    ax.axhline(nd.sum() / od.sum(), color=MG, lw=0.9, ls=(0, (3, 1.5)))
    ax.set_xticks(x); ax.set_xticklabels([m[0] for m in MONTHS]); ax.set_title(f"{d} ({od.sum()} deaths)", fontsize=8)
    ax.yaxis.set_major_formatter(pct)
axs[0].set_ylabel("Share of official deaths in the news"); axs[0].set_ylim(0, 0.75)
fig.tight_layout(w_pad=1.5); save(fig, "Figure_2")
for f in ("Figure_1", "Figure_2"): print(f, Image.open(O / f"{f}{args.tag}.tif").size)
