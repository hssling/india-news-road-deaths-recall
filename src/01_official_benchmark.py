"""Build data/official_benchmark.csv for Dakshina Kannada (revenue district) 2022.

District-parameterised (env KC_DISTRICT, see district_cfg.py): KC_DISTRICT=belagavi writes
data/official_benchmark_belagavi.csv for 'Belagavi City' + 'Belagavi Dist'. Default = DK, unchanged.

Dakshina Kannada revenue district = two police units in KSP statistics:
  'Dakshina Kannada' (district police, rural/taluks) + 'Mangaluru City' (commissionerate).
Sources (downloaded to raw/official/ from data.opencity.in, publisher Karnataka State Police):
  district_2020_2023.csv   -> annual crashes & deaths 2020-2023
  ksp_report_2022.pdf      -> Annexure-42 (month-wise, PDF idx 113-118) and
                              Annexure-30 (road-user category of persons killed, PDF idx 95-97)
"""
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg as DC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "official"
OUT = ROOT / "data" / DC.fname("official_benchmark")
UNITS = DC.CFG["units"]
COMBINED = DC.CFG["combined"]
CSV_URL = ("https://data.opencity.in/dataset/1df26ed7-573e-4b9e-8315-5d204736d254/resource/"
           "c1f7e00d-b3ec-4a1a-84b3-cc73464bb8d9/download/c52e6463-6456-46da-b907-96eef186a5d9.csv")
PDF_URL = ("https://data.opencity.in/dataset/1df26ed7-573e-4b9e-8315-5d204736d254/resource/"
           "99847520-6b11-4c68-bbe2-3381363d6cd7/download/820bd4dc-3f44-41d3-95af-8776598dfb3d.pdf")
PUB = "Karnataka State Police, 'Road Accidents in Karnataka 2022' (via OpenCity data portal)"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def unit_rows(page):
    out = {}
    for tb in page.extract_tables():
        for row in tb:
            if len(row) > 1 and row[1] in UNITS:
                out[row[1]] = [int(c) for c in row[2:]]
    missing = set(UNITS) - set(out)
    if missing:
        sys.exit(f"unit rows missing on page: {missing}")
    return out


rows = []
annual = pd.read_csv(RAW / "district_2020_2023.csv", encoding="utf-8-sig")
annual = annual[annual["District"].isin(UNITS)]
assert len(annual) == 2, "both police units must be present"
for y in (2020, 2021, 2022, 2023):
    for _, r in annual.iterrows():
        rows.append(dict(level="annual", year=y, period=str(y), unit=r["District"], road_user="all",
                         crashes=int(r[f"Road Crashes {y}"]), fatal_crashes=None,
                         deaths=int(r[f"Deaths {y}"]), source_table="District-wise CSV 2020-2023",
                         source_url=CSV_URL))

pdf = pdfplumber.open(RAW / "ksp_report_2022.pdf")
# Annexure-42: each page = two months; per month: fatal acc, total acc, killed, grievous, minor, total inj
for k, idx in enumerate(range(113, 119)):
    d = unit_rows(pdf.pages[idx])
    for half in (0, 1):
        m = MONTHS[2 * k + half]
        for u in UNITS:
            v = d[u][6 * half: 6 * half + 6]
            rows.append(dict(level="monthly", year=2022, period=m, unit=u, road_user="all",
                             crashes=v[1], fatal_crashes=v[0], deaths=v[2],
                             source_table="KSP 2022 Annexure-42", source_url=PDF_URL))
# Annexure-30: persons killed by road-user category (Male, Female, Total triplets)
cats = {95: ["pedestrian", "bicycle", "two_wheeler"], 96: ["car_taxi_van_lmv", "truck_lorry", "bus"],
        97: ["autorickshaw", "other_motor_vehicle", "other_non_motor"]}
for idx, names in cats.items():
    d = unit_rows(pdf.pages[idx])
    for j, c in enumerate(names):
        for u in UNITS:
            rows.append(dict(level="road_user", year=2022, period="2022", unit=u, road_user=c,
                             crashes=None, fatal_crashes=None, deaths=d[u][3 * j + 2],
                             source_table="KSP 2022 Annexure-30", source_url=PDF_URL))

df = pd.DataFrame(rows)
df["publisher"] = PUB
# combined revenue-district rows
comb = (df.groupby(["level", "year", "period", "road_user", "source_table", "source_url", "publisher"],
                   sort=False, dropna=False)[["crashes", "fatal_crashes", "deaths"]]
          .sum(min_count=1).reset_index())
comb["unit"] = COMBINED
df = pd.concat([df, comb[df.columns]], ignore_index=True)

# internal consistency checks against the annual CSV (not hardcoded literals)
for u in UNITS + [COMBINED]:
    a = df.query("level=='annual' and year==2022 and unit==@u")["deaths"].iloc[0]
    m = df.query("level=='monthly' and unit==@u")["deaths"].sum()
    ru = df.query("level=='road_user' and unit==@u")["deaths"].sum()
    print(f"{u}: annual={a} monthly_sum={m} road_user_sum={ru}")
    assert a == m == ru, f"inconsistent totals for {u}"
df.to_csv(OUT, index=False)
print("wrote", OUT, len(df))
