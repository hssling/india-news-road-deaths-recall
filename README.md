# What reaches the news? Road deaths in online news against police counts, two Karnataka districts, 2022

This repository holds the data and code for a validation study of online news as a source of road-death data in India.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24081423.svg)](https://doi.org/10.5281/zenodo.24081423)
[![reproduce-and-verify](https://github.com/hssling/india-news-road-deaths-recall/actions/workflows/verify.yml/badge.svg)](https://github.com/hssling/india-news-road-deaths-recall/actions/workflows/verify.yml)

- **What was compared.** Every 2022 report of a fatal road crash in 12 Kannada, English and Marathi online outlets was matched against the Karnataka State Police counts for Dakshina Kannada (315 deaths) and Belagavi (913 deaths).
- **Method.** Police totals give deaths minus fatal crashes, which equals the sum of (deaths in a crash − 1). This bounds how often the news reports single-death and multi-death crashes, without a model. A finite-population Bayesian model enumerates every crash-size configuration consistent with the police totals. A second model estimates recall by road-user type.

**Status.** The accompanying manuscript has been submitted for publication. Please cite this archive until the article is out: Siddalingaiah H S. *News reports of road deaths in two Karnataka districts, 2022: coded crash files and code* (v1.0.0). Zenodo; 2026. https://doi.org/10.5281/zenodo.24081423

## Main findings

| | Dakshina Kannada | Belagavi |
|---|---|---|
| Police deaths found in the news | 112 of 315 (35.6%) | 112 of 913 (12.3%) |
| Recall, single-death crashes (model) | 30.5% (25.5–36.1) | 7.1% (5.5–9.1) |
| Recall, multi-death crashes (model) | 83.0% (60.0–96.1) | 57.2% (39.2–75.6) |
| Odds ratio, pedestrian vs two-wheeler crash reported | 0.45 (0.24–0.84) | 0.43 (0.19–0.85) |
| News deaths corrected with the *other* district's recall | 913 (police: 315) | 315 (police: 913) |

## Reproduce

```bash
pip install -r requirements.txt
python verify.py                       # recomputes the reported numbers from data/ and outputs/
pip install -r requirements-bayes.txt  # to refit the models (a few minutes)
python src/06_selection_model.py --belagavi-crashes killcheck_crashes_belagavi_all.csv
python src/06_selection_model.py --tag _kn_en          # sensitivity analysis: Belagavi, Kannada and English outlets only
python src/07_figures.py --belagavi-crashes killcheck_crashes_belagavi_all.csv
```

GitHub Actions redraws the figures from the committed model outputs and runs `verify.py` on every push. Refitting the models is optional (see above).

## Contents

| Path | Contents |
|---|---|
| `data/official_benchmark*.csv` | Police (KSP) 2022 crashes, fatal crashes and deaths: annual, monthly and by road-user type, for each police unit and district |
| `data/killcheck_crashes*.csv` | One row per de-duplicated news crash: date, place, taluk, deaths, victim type, vehicles, outlets and source URLs. `_belagavi_all` is the main Belagavi file; `_belagavi` is the Kannada/English subset |
| `data/killcheck_coding*.csv` | One row per coded article |
| `data/killcheck_articles*.csv` | Every fetched article: URL, date, outlet, fetch status, relevance and crash ID |
| `data/sitemap_screen_counts*.csv` | Archive URLs per outlet and the candidates at each screening pass |
| `data/killcheck_summary*`, `_recall_by_*`, `_overlap*`, `_severity*` | Recall tables |
| `src/01`–`05`, `02`–`09` (`_mr`), `filters*.py`, `polite*.py`, `district_cfg.py` | Archive enumeration, screening and output builders (`KC_DISTRICT=dk` or `belagavi`) |
| `src/06_selection_model.py`, `src/07_figures.py` | Bounds, the finite-population severity model, the road-user model, the transport test, monthly statistics, figures |
| `outputs/` | Model outputs, diagnostics and figures (`_kn_en`: sensitivity analysis) |
| `docs/collection_report.md` | Collection log: outlets, robots decisions, counts, exclusions and audits |

## Collection rules

- robots.txt was obeyed, and sites that exclude automated agents were not used.
- Requests used an identified research user agent, at most one every 2 s per host, with no login or paywall access.
- Collection from a site stopped at its first HTTP 403 or 429.
- No article text was stored. Free-text coder notes were removed from the public files because some name the deceased.

## Licences

- **Code:** MIT.
- **Derived data:** CC BY 4.0.
- **News articles and the police report:** cited, not redistributed.

## Author

Siddalingaiah H S, Department of Community Medicine, Shridevi Institute of Medical Sciences and Research Hospital, Tumakuru, Karnataka, India. ORCID [0000-0002-4771-8285](https://orcid.org/0000-0002-4771-8285).
