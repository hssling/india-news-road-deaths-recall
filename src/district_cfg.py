"""District configuration for the kill-check pipeline.

Select the district with the environment variable KC_DISTRICT (default 'dk', so every
script reproduces the original Dakshina Kannada outputs and file names unchanged).
  KC_DISTRICT=belagavi python -I src/01_official_benchmark.py
Output files for a non-default district carry the suffix '_<district>' (e.g.
data/killcheck_crashes_belagavi.csv).
"""
import os
import re

DISTRICTS = {
    "dk": dict(
        name="Dakshina Kannada",
        units=["Dakshina Kannada", "Mangaluru City"],
        city_unit="Mangaluru City", rural_unit="Dakshina Kannada",
        combined="DK revenue district (DK + Mangaluru City)",
        # taluks policed by the Mangaluru City commissionerate (crash-level unit assignment)
        city_taluks={"Mangaluru", "Mulki", "Moodbidri"},
        section_re=r"/district/dakshina-kannada/|/city/mangaluru/|/mangaluru/",
        pv_section="/district/dakshina-kannada/",
    ),
    "belagavi": dict(
        name="Belagavi",
        units=["Belagavi City", "Belagavi Dist"],
        city_unit="Belagavi City", rural_unit="Belagavi Dist",
        combined="Belagavi revenue district (Belagavi City + Belagavi Dist)",
        # 'Belagavi City' taluk label is used for crashes inside the commissionerate limits
        # (city police stations incl. Kakati, Udyambag, Tilakwadi, Shahapur, Camp, Market, APMC, Malmaruti)
        city_taluks={"Belagavi City"},
        section_re=r"/district/belagavi/|/belagavi/|/belgaum/",
        pv_section="/district/belagavi/",
    ),
}

KEY = os.environ.get("KC_DISTRICT", "dk").lower()
if KEY not in DISTRICTS:
    raise SystemExit(f"unknown KC_DISTRICT {KEY!r}; choose from {list(DISTRICTS)}")
CFG = DISTRICTS[KEY]
SUFFIX = "" if KEY == "dk" else f"_{KEY}"
OTHER_SUFFIXES = [f"_{k}" for k in DISTRICTS if k != "dk" and k != KEY]


def fname(stem, ext=".csv"):
    """data file name for the current district, e.g. fname('killcheck_crashes') -> killcheck_crashes_belagavi.csv"""
    return f"{stem}{SUFFIX}{ext}"


def own_file(path_name):
    """True if a glob hit (e.g. screen_log*.csv) belongs to the current district."""
    if SUFFIX:
        return SUFFIX in path_name
    return not any(re.search(re.escape(s) + r"(_|\.|$)", path_name) for s in [f"_{k}" for k in DISTRICTS if k != "dk"])
