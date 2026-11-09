"""Pass-2 screening list for a non-DK district (KC_DISTRICT): data/candidates_pass2_screen_<district>.csv.

Replicates the DK rule: small pass-2 pools are screened in full; the large placeless pools are screened
through a 50% random sample with pandas .sample(frac=0.5, random_state=1) (the DK Udayavani sample
is reproduced exactly by this call). For Belagavi this applies to Udayavani, Vijayavani and Public TV; Prajavani,
Deccan Herald, Kannada Prabha, New Indian Express and Asianet Suvarna are screened in full.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg as DC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if DC.KEY == "dk":
    sys.exit("DK pass-2 screen file already exists (candidates_pass2_screen.csv); not regenerated")
SAMPLED = {"Udayavani", "Vijayavani", "Public TV"}  # Public TV added later (same rule: large pool)
a = pd.read_csv(ROOT / "data" / DC.fname("candidates_pass2"))
parts = []
for o in a["outlet"].drop_duplicates():
    x = a[a.outlet == o].reset_index(drop=True)
    if o in SAMPLED:
        x = x.sample(frac=0.5, random_state=1).sort_index()
    parts.append(x)
out = pd.concat(parts, ignore_index=True)
out.to_csv(ROOT / "data" / DC.fname("candidates_pass2_screen"), index=False)
print(pd.concat([a.groupby("outlet").size().rename("pool"), out.groupby("outlet").size().rename("screened")], axis=1))
