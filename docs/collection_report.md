# Kill check: regional online news as a source of district road-traffic deaths, Karnataka

Study question: can regional online news give a validated district-level file of road-traffic deaths in Karnataka, and how selective is that file?
Test unit: one district-year, **Dakshina Kannada (DK), calendar year 2022**.
Date of check: 2026-11-09. Code is in `src/` and outputs are in `data/`.

## Decision: conditional GO

- **Kannada archives can be retrieved for 2022.** Prajavani has daily sitemaps and full article text. Udayavani has monthly sitemaps with headlines, sub-headlines and keywords, but its article bodies cannot be fetched (see §5).
- **Recall is well above the 10% kill threshold.** The news file has 112 of the 315 official deaths (**35.6%**) and 99 of the 300 official fatal crashes (**33.0%**). After allowing for unscreened candidates, the estimate is about 38–40% (§4.6).
- **Three conditions come with the GO:**
  - (a) DK is close to a best case because it has a strong local daily, Udayavani. A second kill check is needed in a district without such a paper, for example Belagavi or Mysuru, using Prajavani, Vijay Karnataka and other papers, before the study goes statewide.
  - (b) Extraction at scale needs automated classification and field extraction, and no LLM API key is configured on this PC. Deccan Herald and Prajavani block AI crawlers in robots.txt. Any LLM processing of their text therefore needs a terms and permissions review, or local processing only.
  - (c) The file is clearly selective. It must be modelled as a biased capture source and cannot be used as a census.

## 1. Official benchmark (`data/official_benchmark.csv`)

- **Sources.** OpenCity data portal, <https://data.opencity.in/dataset/road-accidents-in-karnataka> (dataset author: Vaidyanathan R; organisation: Government of Karnataka). The original publisher is **Karnataka State Police (KSP), "Road Accidents in Karnataka"** annual report, ksp.karnataka.gov.in. Two resources were used:
  - the district-wise CSV for 2020–2023;
  - the KSP 2022 report PDF: Annexure-42 (month-wise figures) and Annexure-30 (persons killed by road-user category).
- **Area covered.** The DK revenue district is two police units: **Dakshina Kannada (district police)** and **Mangaluru City (commissionerate)**.
- **2022 figures.**
  - Dakshina Kannada: 943 crashes and 156 deaths.
  - Mangaluru City: 927 crashes and 159 deaths.
  - **Combined: 1,870 crashes, 300 fatal crashes and 315 deaths.**
- **Internal consistency.** The monthly sums and the road-user sums both equal the annual total for each unit. This is checked in the script, not against hard-coded values.
- **Deaths by road-user type (combined units):** two-wheeler 148, pedestrian 88, car/LMV 33, autorickshaw 16, bus 12, truck 9, other motor vehicle 6, bicycle 3.

## 2. News enumeration (Step 2)

| Outlet (language) | Archive used | Requests | URLs in 2022 sitemaps | Slug candidates (pass 1) | Articles fetched and screened |
|---|---|---|---|---|---|
| Deccan Herald (English) | daily sitemaps `sitemap-daily-YYYY-MM-DD.xml` | 366 | 93,969 | 53 | 53 + 96 (pass 2) |
| Prajavani (Kannada) | daily sitemaps (same Quintype layout); `/district/dakshina-kannada/` section | 366 | 98,960 | 240 (3,176 DK-section URLs) | 240 + 36 (pass 2) |
| Udayavani (Kannada and English editions) | monthly sitemaps `kan/MM-2022.xml`, `eng/MM-2022.xml` | 24 | 81,369 | 688 | 688 + 488 (pass 2, 50% sample) |
| Times of India (English) | city-section monthly sitemaps | 5 | 24,239 (January only) | 31 (not read) | 0. The site returned 403 on a sitemap request, so crawling stopped as the rules require. |
| The Hindu | — | 0 | — | — | robots.txt disallows `/sitemap/archive*`, so it was skipped |

**Pass 1 (place filter).** A URL slug or section had to name a DK place: a list of about 150 tokens covering towns, taluks, localities and spelling variants. The slug also had to contain a road-crash term or a crime-roundup marker. Obvious noise was excluded (COVID, temple car, theft, murder and similar).

**Pass 2 (missed-slug check).** This pass took road-crash slugs that named *no* recognised DK place and *no* other place: 96 from Deccan Herald, 36 from Prajavani and 976 from Udayavani. Deccan Herald and Prajavani were screened in full. Udayavani was screened through a random 50% sample. The aim was to measure how much the place-token filter misses, for example misspellings such as "moodubidri" and slugs with no place at all.

Fetching rules followed throughout:
- robots.txt obeyed, including the OpenCity crawl-delay of 10 s;
- User-Agent `research-feasibility-check (academic injury study)`;
- at most 1 request per 2 s per host;
- no login, paywall or bot-check bypass;
- stop a site on 403 or 429 (triggered once, for Times of India).

Article text was held in memory only. `data/screen_log*.csv` keeps only the URL, date, outlet, language, fetch status and keyword flags. The temporary console excerpts used for reading were deleted.

## 3. Extraction (Step 3)

- **What was read.** I read every fetched headline, and for Deccan Herald and Prajavani every death-flagged excerpt of the full text. I coded each article that reported a road crash in `data/killcheck_coding.csv` (259 rows).
- **De-duplication.** Reports were merged into one crash when they had the same place, a date within ±1 day (later reports of a death after treatment were linked to the original crash), the same vehicles and a consistent death count. Of the 99 crashes, 17 were reported by 2 outlets and 5 by all 3 outlets.
- **Exclusions:**
  - 13 fatal crashes outside DK, including Udupi district, Mysuru, Mandya, Bengaluru, other states and abroad. Some of these victims were DK residents.
  - 16 fatal articles whose location could not be determined. Most are Udayavani headlines with no place; one is the Parappe (Sullia/Kasaragod border) crash with 2 deaths.
  - 2 deaths in 2022 from crashes that happened in 2021.
  - railway deaths.
  - 3 borderline events, kept for a sensitivity analysis only: a tree falling on a moving car, a snapped power line hitting a rider, and a tractor toppling onto a worker.
- **Non-fatal crashes.** 40 DK non-fatal crash reports were hand-coded but not used. In addition, 354 fetched articles had a crash keyword and no death keyword.
- **Basis of the fields.** 70 crashes rest on Udayavani headline, sub-headline and keywords only. 29 have full text (Deccan Herald or Prajavani), alone or together with Udayavani.

## 4. Results (Step 4)

### 4.1 Recall against the official total (`data/killcheck_summary.csv`)

| Scope | Crashes | Deaths | Recall, deaths (of 315) | Recall, fatal crashes (of 300) |
|---|---|---|---|---|
| English (any English outlet) | 79 | 89 | 28.3% | 26.3% |
| — Deccan Herald alone (mainstream English daily) | 7 | 10 | **3.2%** | 2.3% |
| — Udayavani English edition | 77 | 87 | 27.6% | — |
| Kannada (any Kannada outlet) | 77 | 89 | 28.3% | 25.7% |
| — Prajavani (state Kannada daily) | 27 | 34 | 10.8% | 9.0% |
| — Udayavani Kannada edition | 59 | 66 | 21.0% | — |
| **Union** | **99** | **112** | **35.6%** | **33.0%** |

Outlet overlap (`data/killcheck_overlap.csv`), as crashes (deaths):

| Outlets reporting the crash | Crashes (deaths) |
|---|---|
| Udayavani only | 70 (76) |
| Prajavani only | 7 (9) |
| Udayavani and Prajavani | 15 (17) |
| Udayavani and Deccan Herald | 2 (2) |
| All three | 5 (8) |
| Deccan Herald only | 0 |

By language:
- reported in both English and Kannada: 57 crashes;
- English only: 22;
- Kannada only: 20.

What drives recall is how local the outlet is, not the language it publishes in. The state-level English daily (Deccan Herald, 3%) is trivially low. The coastal daily (Udayavani) carries most of the file in both of its editions.

### 4.2 By road-user type of victim (`data/killcheck_recall_by_road_user.csv`)

| Road-user type | Official deaths | News deaths | Recall |
|---|---|---|---|
| Two-wheeler | 148 | 53 | 36% |
| Pedestrian | 88 | 16 | **18%** |
| Car/LMV | 33 | 15 | 45% |
| Autorickshaw | 16 | 4 | 25% |
| Bus | 12 | 3 | 25% |
| Truck | 9 | 2 | 22% |
| Other motor vehicle | 6 | 3 | 50% |
| Bicycle | 3 | 3 | 100% (small numbers) |
| Unknown type | — | 13 | — |

### 4.3 By month (`data/killcheck_recall_by_month.csv`)

- Recall is 15–23% in January–March and 32–50% from April to December.
- Recall is 29% in January–June and 43% in July–December.
- Across months, official deaths and news deaths have a Spearman correlation of 0.57.
- The lower early-year recall may partly be an archive artefact and was not investigated further.

### 4.4 By police unit and taluk (`data/killcheck_recall_by_unit.csv`)

- Dakshina Kannada district police (rural taluks): 60 of 156 deaths (38.5%).
- Mangaluru City commissionerate: 52 of 159 deaths (32.7%).
- News deaths by taluk: Mangaluru 43, Bantwal 19, Belthangady 14, Puttur 14, Kadaba 7, Moodbidri 6, Sullia 6, Mulki 3.

### 4.5 Selection pattern

**What does appear in the news:**
- Multi-fatality crashes are slightly over-represented: 12 of 99 news crashes, 25 of 112 deaths. News deaths per crash are 1.13, against 1.05 in the official data.
- Deaths of prominent people: 2 police ASIs, a Lions Club president, a Yakshagana artiste, a MESCOM engineer, a temple priest, a PE teacher and medical students.
- Crashes that led to a public response: the BMW crash and organ donation, and the pothole death on NH-73 (5 articles across outlets).
- Children and bus-passenger falls.

The coastal Kannada press does report **many single-death two-wheeler crashes**: 87 of the 99 news crashes have one death.

**What is likely missing:**
- **Pedestrians**: about 4 in 5 are missing, and urban pedestrians especially.
- Deaths after a delay in hospital. Only a minority get follow-up stories.
- Urban Mangaluru City crashes are somewhat under-covered.
- Crashes reported only in print or local cable TV.
- Udayavani stories whose headline names no place: 7 or more found in the sample.

### 4.6 Bounds on what an exhaustive screen would find

- The 50% pass-2 sample of Udayavani found 6 new DK fatal crashes (7 deaths). The unscreened half therefore probably holds about 6 more crashes (about 7 deaths).
- There are 16 fatal articles with undetermined location, 20 deaths, part of them in DK.
- The 31 unread Times of India January candidates and the slugs dropped as noise were not checked.
- An exhaustive screen would probably bring union recall to **about 38–42% of deaths**, still well short of a census.

## 5. Retrievability of Kannada archives

- **Prajavani: retrievable.**
  - Daily sitemaps exist back to at least 2022 and are allowed by robots.txt.
  - Full text is available via JSON-LD `articleBody`.
  - A district section (`/district/dakshina-kannada/`) supports filtering.
- **Udayavani: partly retrievable.**
  - Monthly sitemaps are allowed, about 4,000 Kannada and 2,400 English URLs per month.
  - Article pages give the headline, sub-headline, keywords and publication date.
  - The **body text is loaded client-side from a CloudFront host whose robots.txt returns 403**, so it was not fetched. A conservative reading of robots.txt treats this as disallowed. As a result:
    - roundup articles ("crime news") could not be read;
    - place is missing for some headlines.
- **Vijay Karnataka**: robots.txt allows crawling, but the sitemap only covers the last 48 hours, and the archive structure was not tested.
- **Kannada OneIndia**: robots.txt disallows all crawlers (`User-agent: * Disallow: /`).
- **Policy flag.** Deccan Herald and Prajavani (same publisher) explicitly disallow ClaudeBot, anthropic-ai, GPTBot and other AI agents. This check used a research user agent that the wildcard rule allows. A scaled study that passes their text to an LLM should get publisher permission, or run extraction on a local model, and should document this in the ethics statement.

## 6. Effort per district-year and scaling

**HTTP requests: about 2,400**
- Sitemaps: about 760.
- Article pages: 1,601. Each Udayavani fetch also makes 1 redirect.
- Official data: 3.

**Wall-clock time** (at 2 s per host, 3 hosts in parallel):
- about 40 min for sitemaps;
- about 2 h for articles, with Udayavani the bottleneck.

**Reading**
- About 1,600 headlines or excerpts were screened.
- About 400 were death-flagged and read closely.
- 259 article rows were hand-coded and 99 crashes were de-duplicated.
- This is about **6–8 analyst-hours for one bilingual coder** per district-year, excluding verification.

**Scaling to 31 districts × 4 years (124 district-years)**
- About 250–300k requests.
- About 200k headlines.
- About 50k fatal-flagged articles to extract and de-duplicate.
- **Automated LLM (or fine-tuned local model) extraction would be required.** This covers Kannada and English classification, extraction of place, date, deaths and road-user type, and de-duplication across outlets.
- No API key is configured on this PC. Given the robots policies above, a **local multilingual model** together with a human-coded validation sample is the cleaner route.
- Note: the sitemaps are per outlet, not per district. One state-wide sitemap pass serves every district, so the request count grows mainly with the number of article fetches.

## 7. Caveats

- One analyst read and coded everything; there was no double coding.
- Most Udayavani extractions rest on the headline, sub-headline and keywords only.
- Road-user type is assigned at crash level. In multi-death crashes all victims are assumed to be of the same type.
- Date matching uses the publication date when the crash date was not reported.
- Official deaths include deaths within 30 days, which news may not follow up.
- DK has unusually dense local media coverage, so the recall found here is likely an upper bound for Karnataka districts.

## Files

| File | Contents |
|---|---|
| `src/polite.py`, `src/polite_read.py` | Polite fetcher (robots.txt, crawl-delay, 403/429 stop); in-memory reader |
| `src/01_official_benchmark.py` | Builds the benchmark from the KSP CSV and PDF annexures, with consistency checks |
| `src/02_harvest_sitemaps.py` | Harvests 2022 sitemap URL lists (stored in `raw/sitemaps/`; URLs only) |
| `src/03_candidates.py`, `src/03b_residual.py`, `src/filters.py` | Slug filters (pass 1 and pass 2) |
| `src/04_screen.py` | Fetches articles and prints excerpts for manual reading; logs metadata only |
| `src/05_build_outputs.py` | Assembles the outputs and recall tables from the hand coding |
| `data/official_benchmark.csv` | Annual 2020–23, monthly and road-user rows for 2022, per unit and combined |
| `data/killcheck_crashes.csv` | One row per de-duplicated DK fatal crash (99), with source URLs |
| `data/killcheck_articles.csv` | Every fetched article (1,601): URL, date, outlet, language, relevant yes/no, crash id |
| `data/killcheck_coding.csv` | Hand coding per article |
| `data/killcheck_summary.csv`, `_by_month`, `_by_road_user`, `_by_unit`, `_overlap` | Recall tables |
| `data/build_log.txt` | Console output of the build |

---

# Second district-year: Belagavi 2022

Same question, same method, a district without a dominant local daily. Date of check: 2026-11-09. The DK section above is unchanged. All DK outputs were re-built after the code changes and are byte-identical (md5 of all 20 `data/*.csv` files and the build log).

## B0. Decision: NO-GO for a news-based district file in Belagavi (and, by extension, for a statewide file)

- **Union recall is 8.0% of deaths (73 of 913) and 4.9% of fatal crashes (42 of 857).** That is below the 10% kill threshold for deaths and well below it for crashes. After the bounds in §B4.6 it is still only about 8.5–9%.
- The DK result (35.6%) was driven by one outlet, Udayavani. In Belagavi no outlet plays that role: the best single outlet, Prajavani, captures 6.1% of deaths.
- **What news does record in Belagavi is a severity-selected subset**, not a sample. News crashes average 1.74 deaths each, against 1.07 in the official data. 19 of the 42 crashes had two or more deaths, and those 19 account for 50 of the 73 deaths. Pedestrians (3.5%) and city crashes (4.2%) are almost invisible.
- **Why Belagavi and not Mysuru.** The Belagavi 2022 figure is available and unambiguous. Both the district CSV and the PDF annexures list "Belagavi City" and "Belagavi Dist" separately, and the monthly and road-user sums reconcile exactly. Mysuru was therefore not needed.
- **Not tested: Marathi outlets.** Belagavi city and its border taluks have a large Marathi readership (Tarun Bharat, Pudhari, Lokmat). These papers were outside the outlet brief (Kannada and English). They are the one remaining candidate for a local-daily effect like Udayavani's in DK, and they should be checked before Belagavi is written off completely.

## B1. Official benchmark (`data/official_benchmark_belagavi.csv`)

- **Source and script.** Same KSP 2022 report and district CSV as DK, built by `KC_DISTRICT=belagavi python -I src/01_official_benchmark.py`.
- **Police units.** Belagavi City (commissionerate) plus Belagavi Dist (district police).
- **2022 figures:**

| Unit | Crashes | Fatal crashes | Deaths |
|---|---|---|---|
| Belagavi City | 565 | 155 | 167 |
| Belagavi Dist | 1,935 | 702 | 746 |
| **Combined** | **2,500** | **857** | **913** |

- **Internal consistency.** For each unit and for the combined total, annual deaths = the sum of monthly deaths (Annexure-42) = the sum of road-user deaths (Annexure-30). This is asserted in the script.
- **Deaths by road-user type (combined units):**
  - two-wheeler 443
  - pedestrian 144
  - other motor vehicle 120 (47 of them in Belagavi City, a category much larger than in DK, probably tractors and goods autos)
  - car/LMV 91
  - truck/lorry 68
  - bicycle 19
  - bus 12
  - other non-motor 11
  - autorickshaw 5
- **Deaths by month (combined units):**

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 98 | 71 | 65 | 91 | 78 | 58 | 65 | 57 | 74 | 85 | 70 |

  - January–June: 504 deaths.
  - July–December: 409 deaths.

## B2. News enumeration

The DH, PV, UV and TOI 2022 sitemaps harvested for DK were reused unchanged, since they are state-wide and cost no new requests. Five outlets were added after checking their robots.txt with the research user agent. Four use the same Quintype or daily layout as the DK outlets; Public TV is WordPress.

| Outlet (language) | Archive | URLs in 2022 sitemaps | Pass-1 candidates (place + crash slug) | Pass-2 pool → screened | Articles fetched |
|---|---|---|---|---|---|
| Prajavani (Kn) | daily; `/district/belagavi/` section (2,264 URLs) | 98,960 | 183 | 39 → 39 | 222 |
| Udayavani (Kn + En) | monthly; headline, sub-headline and keywords only | 81,369 | 55 | 1,063 → 532 (50% sample) | 587 |
| Deccan Herald (En) | daily | 93,969 | 16 | 94 → 94 | 110 |
| **Vijayavani (Kn), new** | daily `sitemap-daily-YYYY-MM-DD.xml` | 40,857 | 28 | 535 → 268 (50%) | 296 |
| **Kannada Prabha (Kn), new** | daily (6 days returned 404) | 13,392 | 12 | 55 → 55 | 66 |
| **New Indian Express (En), new** | daily (all states) | 123,301 | 13 | 52 → 52 | 65 |
| **Asianet Suvarna News (Kn), new** | daily `sitemap/2022/MM/DD/sitemap.xml.gz` | 62,309 | 55 | 73 → 73 | 125 |
| **Public TV (Kn), new** | WordPress post-sitemaps 41–55; 2022 selected on `<lastmod>` | 28,881 | 69 | 237 → 118 (50%) | 187 |
| Times of India | — | — | 1 | — | 0 (site stopped after the 403 in the DK run) |
| **Total** | | | **431** | **1,231 screened** | **1,658** |

- **Fetch outcomes.** 1,658 of 1,662 fetches were `ok`. The other four were three Asianet HTTP 410 (removed pages) and one Kannada Prabha 404. That 404 was a URL in which the sitemap's "₹" had been mis-decoded; it is a duplicate report of crash C002.
- **Place filter.** Belagavi city, the 15 taluks (including Mudalgi, Kagwad, Yaragatti, Kittur and Nippani) and about 60 towns and localities, with transliteration variants and the Kannada-script names. The list is in `src/filters.py`. Names shared with other districts (Kerur, Bagewadi, Itagi, Konnur and others) were left out on purpose.
- **Pass 2.** Same rule as DK: placeless crash slugs, with the other-place list adapted to Belagavi (DK and coastal names, Maharashtra-border names and neighbouring north-Karnataka taluks). The three large pools (Udayavani, Vijayavani, Public TV) were screened through a 50% random sample using `sample(frac=0.5, random_state=1)`, the call that reproduces the DK Udayavani sample exactly (`src/03c_pass2_sample.py`).
- **Skipped or blocked outlets:**
  - **Samyukta Karnataka.** robots.txt (`samyukthakarnataka.com`) is permissive, but the site publishes no sitemap (`/sitemap.xml`, `/sitemap_index.xml` and `/news-sitemap.xml` all return 404), its homepage is empty (123 bytes), and `samyuktakarnataka.com` timed out. It was not usable.
  - **Vijay Karnataka.** No sitemap at the standard paths: robots.txt and sitemap.xml return 404 from an S3 bucket. This matches the DK note (48-hour sitemap only).
  - **Kannada OneIndia.** robots.txt disallows all agents.
  - **TV9 Kannada.** News sitemap only, no archive (`/sitemap.xml` returns 404).
  - **Vistara News.** Disallows ClaudeBot and anthropic-ai, carries `ai-train=no`, and did not exist for most of 2022. Not used.
  - **Kannada News18.** Disallows ClaudeBot. Not used.
  - **The Hindu and TOI.** As for DK.
- **Policy flag, as in the DK report.** Asianet, Kannada Prabha, Vijayavani, NIE and Public TV allow the wildcard agent. No new outlet returned 403 or 429.

## B3. Extraction

- **Coding.** Rules, exclusions and de-duplication are identical to DK.
- **Volume.** About 1,660 headlines or excerpts were screened and about 770 death-and-crash-flagged items were read. Ambiguous items were re-read in memory with sentence-level excerpts only, and nothing was written to disk.
- **Coding file.** `data/killcheck_coding_belagavi.csv` has 156 article rows:
  - 114 in-district fatal rows, which collapse to 42 crashes;
  - 17 non-fatal (N);
  - 12 outside the district (X), including Belagavi residents killed in Chitradurga, Tumakuru, Vijayapura (Indi), Solapur, Goa and West Bengal;
  - 13 of undetermined location (U, 16 deaths), all Udayavani pass-2 headlines with no place;
  - 1 railway death, excluded.
- **Borderline events (sensitivity only).** 3 crashes, 3 deaths:
  - a tree falling on a moving bike, twice: in the April storm and at Sangolli Rayanna Circle in September;
  - a kite-string (manja) injury to a child riding pillion.
- **Basis of the fields.** 32 crashes rest on full text, 9 on full text plus Udayavani headlines, and 1 on an Udayavani headline only. Udayavani matters much less here than in DK.
- **De-duplication.** 18 of the 42 crashes were reported by two or more outlets. The Kalyal bridge cruiser crash (C002, 8 deaths) was reported by all 8 outlets in 22 articles. Its toll rose from 7 to 8 on 28 June, and the maximum across reports is used.
- **Police unit.** Assigned from the place: places inside the commissionerate count as City, including Kakati PS (Ukkada); everything else counts as District.
  - C002 (Kalyal/Kanabargi, Marihal PS) is assigned to District.
  - If Marihal belongs to the commissionerate, City recall rises to 9.0%.

## B4. Results

### B4.1 Recall against the official total (`data/killcheck_summary_belagavi.csv`)

| Scope | Crashes | Deaths | Recall, deaths (of 913) | Recall, fatal crashes (of 857) |
|---|---|---|---|---|
| Any English outlet (DH, NIE, Udayavani English) | 8 | 24 | 2.6% | 0.9% |
| — Deccan Herald | 5 | 17 | 1.9% | 0.6% |
| — New Indian Express | 3 | 14 | 1.5% | 0.4% |
| Any Kannada outlet | 42 | 73 | 8.0% | 4.9% |
| — Prajavani | 33 | 56 | **6.1%** | 3.9% |
| — Public TV | 13 | 35 | 3.8% | 1.5% |
| — Udayavani (Kn 10 / En 4 crashes) | 10 | 30 | 3.3% | 1.2% |
| — Asianet Suvarna | 9 | 27 | 3.0% | 1.1% |
| — Vijayavani | 9 | 25 | 2.7% | 1.1% |
| — Kannada Prabha | 4 | 16 | 1.8% | 0.5% |
| **Union** | **42** | **73** | **8.0%** | **4.9%** |

By language:
- reported in both English and Kannada: 8 crashes (24 deaths);
- English only: none;
- Kannada only: 34 crashes (49 deaths).

Every English-reported crash is also in Kannada.

Crashes reported by a single outlet only, as crashes (deaths):
- Prajavani 19 (23);
- Asianet 2 (3);
- Public TV 1 (2);
- Udayavani 1 (1);
- Vijayavani 1 (1);
- DH, NIE and Kannada Prabha 0.

Prajavani carries the file. The new outlets add 6 crashes and 10 deaths that none of the DK outlets (DH, PV, UV) had:
- Public TV: C045 (2 deaths);
- Public TV and Vijayavani: C007 and C043 (2 deaths each);
- Vijayavani: C044 (1 death);
- Asianet: C013 (1 death) and C014 (2 deaths).

Without the new outlets, union recall would be 63 of 913 deaths (6.9%).

Per-outlet combinations are in `data/killcheck_overlap_belagavi.csv`.

### B4.2 By road-user type of victim (`data/killcheck_recall_by_road_user_belagavi.csv`)

| Road-user type | Official deaths | News deaths | Recall |
|---|---|---|---|
| Two-wheeler | 443 | 35 | **7.9%** |
| Pedestrian | 144 | 5 | **3.5%** |
| Other motor vehicle | 120 | 1 | 0.8% |
| Car/LMV | 91 | 30 | 33% (24% without the 8-death cruiser crash) |
| Truck/lorry | 68 | 0 | 0% |
| Bicycle | 19 | 0 | 0% |
| Bus | 12 | 2 | 17% |
| Other non-motor | 11 | 0 | 0% |
| Autorickshaw | 5 | 0 | 0% |

### B4.3 By month and half-year (`_by_month_belagavi.csv`, `_by_half_belagavi.csv`)

- **January–June:** 28 of 504 deaths (**5.6%**) and 12 of 467 fatal crashes (2.6%).
- **July–December:** 45 of 409 deaths (**11.0%**) and 30 of 390 fatal crashes (7.7%).
- **Monthly recall** ranges from 0% (April) to 20% (August).
- **Spearman correlation** of official and news deaths across months: **−0.21**. The news series carries no seasonal signal.
- **Archive gap.** As in DK, the first half of the year is thinner. Prajavani's Belagavi section has very few crash items before May.

### B4.4 By police unit and taluk (`_by_unit_belagavi.csv`)

| Unit | News crashes | News deaths | Recall, deaths | Recall, fatal crashes |
|---|---|---|---|---|
| Belagavi City | 7 | 7 | **4.2%** (of 167) | 4.5% (of 155) |
| Belagavi Dist | 35 | 66 | **8.8%** (of 746) | 5.0% (of 702) |

News deaths by taluk:

| Hukkeri | Belagavi (rural) | Nippani | Belagavi City | Saundatti | Athani | Chikkodi | Ramdurg |
|---|---|---|---|---|---|---|---|
| 16 | 14 | 9 | 7 | 5 | 4 | 3 | 3 |

| Gokak | Bailhongal | Khanapur | Kittur | Mudalgi | Yaragatti |
|---|---|---|---|---|---|
| 2 | 2 | 2 | 2 | 2 | 2 |

Coverage follows the NH-48 corridor (Hukkeri, Sankeshwar, Nippani and Hirebagewadi) and the Chikkodi sub-division bureaus. Athani, Gokak and Ramdurg are thin given their size.

### B4.5 Selection pattern

**What does appear in the news:**
- **Multi-fatality crashes.** 19 of 42 news crashes, 50 of 73 deaths. Deaths per crash are 1.74 in the news against 1.07 officially; DK was 1.13 against 1.05.
- **Crashes with state-level response.** CM compensation: C002. The Athani school-bus crash: C005.
- **Victims with status.**
  - three soldiers, in C010, C021 and C022;
  - the wife and daughter of an ASI, in C006;
  - a teacher;
  - students.
- **Crashes on the national highway.**

**What is missing:**
- **Single-death crashes.** Only 23 news crashes, against at least 801 official single-death crashes (857 fatal crashes, 913 deaths).
- **Pedestrians.** More than 96% are missing.
- **Other categories.** City crashes, truck occupants, tractor and goods-auto victims (official "other motor vehicle", 120 deaths) and bicyclists.
- **Deaths after delay.** Only the C002 follow-up was reported.

### B4.6 Bounds on an exhaustive screen

- **Unscreened halves of the sampled pass-2 pools.**
  - The Vijayavani 50% sample found 2 new crashes (3 deaths), so the unscreened half probably holds about 2 more (about 3 deaths).
  - The Udayavani and Public TV samples found no new Belagavi crashes, only duplicates.
- **Undetermined headlines.** 13 Udayavani pass-2 headlines with no place (16 deaths) are mostly coastal. At most a few are likely to be in Belagavi.
- **Borderline events.** These add 3 deaths in the sensitivity analysis, giving 76 deaths (8.3%).
- **Overall.** An exhaustive screen of these 8 outlets would probably reach **about 77–82 deaths (8.5–9%)**. Even Marathi outlets would have to add several hundred deaths to bring Belagavi close to DK.

## B5. Side-by-side with Dakshina Kannada

| Metric | DK 2022 | Belagavi 2022 |
|---|---|---|
| Official deaths, fatal crashes | 315, 300 | 913, 857 |
| Outlets screened | 3 (+TOI stopped) | 8 (+TOI stopped) |
| Articles fetched | 1,601 | 1,658 |
| **Union recall, deaths** | **35.6%** | **8.0%** |
| Union recall, fatal crashes | 33.0% | 4.9% |
| Best single outlet | Udayavani 32.7% | Prajavani 6.1% |
| Mainstream English (DH) | 3.2% | 1.9% |
| Two-wheeler | 36% | 7.9% |
| Pedestrian | 18% | 3.5% |
| Car/LMV | 45% | 33% (24% without C002) |
| City unit / rural unit | 32.7% / 38.5% | 4.2% / 8.8% |
| H1 / H2 | 29% / 43% | 5.6% / 11.0% |
| Deaths per news crash (official) | 1.13 (1.05) | 1.74 (1.07) |
| Share of news crashes with 1 death | 88% | 55% |
| Spearman correlation, monthly | 0.57 | −0.21 |
| Bounded exhaustive estimate | 38–42% | 8.5–9% |

DK's recall depends on Udayavani, a hyper-local daily with dense coverage at taluk level. Where there is no such paper, regional online news drops to under a tenth of road deaths and records mainly the severe and newsworthy crashes. A statewide file built from Kannada and English online news would therefore be heterogeneous across districts by a factor of about 4 in recall. It would also be strongly severity-biased outside the coast, and cannot be treated as one capture source with a single selection model.

## B6. Code changes (DK outputs reproduced exactly)

- **`src/district_cfg.py` (new).** The district is chosen by the environment variable `KC_DISTRICT` (`dk` is the default, `belagavi` the alternative). It sets the police units, the section regex, the city-unit rule and the `_belagavi` file suffix.
- **Scripts 01, 03, 03b, 04 and 05 and `filters.py`.** Parameterised by district. New outlets enter only for districts other than DK.
- **`02_harvest_sitemaps.py`.** Adds the jobs `vv`, `kp`, `nie`, `an` (gzip-aware) and `ptv`. Their sitemaps are in `raw/sitemaps/{vv,kp,nie,an,ptv}_2022.csv` (URLs only).
- **`src/03c_pass2_sample.py` (new).** Builds the pass-2 50% sample.
- **Privacy bug found and fixed in `04_screen.py`.** When a page had no detectable headline, the script logged the reader's return value, which can be body text, in `fetch_status`. This hit the first Public TV run (69 rows) and one Asianet live page.
  - Those log rows were deleted and the pages were re-fetched.
  - The script now logs `NO_TITLE`.
  - `polite_read.py` gained an og:title fallback that works whatever the attribute order, a `<title>` fallback, and a fallback for the published date.
  - All `data/screen_log*.csv` files were checked afterwards. The longest `fetch_status` is 23 characters, and the DK logs were never affected.
- **Temporary files.** The console excerpt files were deleted.

## B7. Effort

**HTTP requests: about 3,250**
- Sitemaps: 1,486 (4 × 366 daily, plus 22 for Public TV). The DH, PV and UV sitemaps were reused, at no cost.
- Robots and sitemap probes: about 35.
- Articles: 1,662, plus about 40 in-memory re-reads.

**Wall-clock time:** about 2.5 h, with Udayavani (redirect plus headline page) again the bottleneck.

**Reading:** about 7–9 analyst-hours for Kannada and English, close to DK, with about 4 times DK's death count and a quarter of the yield.

## B8. Files (Belagavi)

| File | Contents |
|---|---|
| `data/official_benchmark_belagavi.csv` | Annual 2020–23, monthly and road-user rows for 2022: Belagavi City, Belagavi Dist and combined |
| `data/candidates_all_belagavi.csv`, `data/candidates_pass2_belagavi.csv`, `data/candidates_pass2_screen_belagavi.csv`, `data/sitemap_screen_counts_belagavi.csv` | URL-level candidates and counts |
| `data/screen_log_belagavi_*.csv`, `data/screen_log_candidates_pass2_screen_belagavi_*.csv` | Every fetch: URL, outlet, language, date, status, keyword flags |
| `data/killcheck_coding_belagavi.csv` | Hand coding per article (156 rows) |
| `data/killcheck_crashes_belagavi.csv` | One row per de-duplicated Belagavi fatal crash (42), with source URLs |
| `data/killcheck_articles_belagavi.csv` | Every fetched article (1,662) with relevance and crash id |
| `data/killcheck_summary_belagavi.csv`, `_by_month_belagavi`, `_by_half_belagavi`, `_by_road_user_belagavi`, `_by_unit_belagavi`, `_overlap_belagavi` | Recall tables |
| `data/build_log_belagavi.txt` | Console output of the Belagavi build |
| `raw/sitemaps/{vv,kp,nie,an,ptv}_2022.csv` (+ `_log`) | New outlet sitemap URL lists |

## B9. Marathi outlets

Question: does the Marathi press, which a large share of Belagavi city and the border taluks read, close the gap between Belagavi (8.0%) and DK (35.6%)? Same method as B2–B4: 2022 sitemaps (URLs only), a pass-1 place-and-crash slug filter, a pass-2 placeless-slug check, hand coding with the B3 rules, and de-duplication against the 42 existing crashes (date ±2 days, same place or taluk, consistent deaths). Date of check: 2026-11-09. No existing DK or `_belagavi` file was changed: all 52 pre-existing `data/` files and the 18 `raw/sitemaps/` files hash identically before and after.

### B9.1 Outlets

robots.txt was tested for the research user agent, ClaudeBot, anthropic-ai, GPTBot and `*` (`src/06_mr_probe.py`, results in `raw/mr_probe/`). Times-group sites (Maharashtra Times) were not tried.

| Outlet | robots.txt | 2022 archive | Status | 2022 URLs | Pass-1 candidates | Pass-2 pool → screened | Fetched |
|---|---|---|---|---|---|---|---|
| **Tarun Bharat** (Belgaum daily, tarunbharat.com) | all agents allowed | WordPress `post-sitemapN.xml`, ascending, 100 posts each; N = 940–1380 brackets 2022; selected on `<lastmod>` | **usable** | 41,081 | 88 | 371 → 186 (50%), plus pass 2b 366 → 183 (50%) | 457 |
| **Pudhari** (pudhari.news) | all allowed | Quintype daily sitemaps; `/belgaon/` section (478 URLs) | **usable** | 58,660 | 87 | 181 → 181 | 268 |
| **Sakal** (esakal.com) | all allowed | Quintype daily sitemaps; Belgaum news under `/paschim-maharashtra/` | **usable** | 227,681 | 68 | 18 → 18 | 86 |
| **TV9 Marathi** | all allowed | monthly `sitemap/post-2022-<month>-<k>.xml` (48) | **usable** | 45,286 | 6 | 72 → 72 | 78 |
| Belgaum Live (belgaumlive.com) | all allowed | WordPress post-sitemaps ordered by `<lastmod>` (newest first), dated `/YYYY/MM/` URLs; very slow server (about 2 min per sitemap) | **has a 2022 archive and was harvested, but was unreachable at screening time**: TCP connections to 103.174.148.247:443 timed out at about 15:34, 15:40 and 15:57 IST on 2026-11-09 (`raw/mr_probe/belgaumlive_screen_attempts.csv`); not screened, no workaround tried | 3,635 | 194 (the whole site is Belgaum-only, so every crash slug is pass 1; the pass-2 placeless pool is 0 by construction, as for a district section) | — | 0 |
| Lokmat (lokmat.com) | allowed | — | **blocked: HTTP 403** on `sitemap_index.xml`; site stopped as the rules require | — | — | — | 0 |
| Loksatta | **disallows ClaudeBot and anthropic-ai** | — | **skipped by policy** | — | — | — | 0 |
| News18 Lokmat (news18marathi.com) | allowed | the daily index covers only the last 365 days; `daily/2022-06-15.xml` is empty | not usable (no 2022 archive) | — | — | — | 0 |
| Navarashtra | allowed | news and web-story sitemaps only | not usable (no 2022 archive) | — | — | — | 0 |
| Saamana | allowed | WordPress core sitemaps, 2,000 undated URLs each, with no datable 2022 range; a Mumbai paper | not usable (no 2022 archive) | — | — | — | 0 |
| ABP Majha (marathi.abplive.com) | allowed | rolling news sitemaps only; archive paths timed out | not usable (no 2022 archive) | — | — | — | 0 |
| Belgavkar (belgavkar.com) | allowed | 7-page static sitemap; content behind login and membership pages | not usable | — | — | — | 0 |
| inBelgaum, belgaumnews.com | — | — | unreachable (connect timeout, DNS failure) | — | — | — | 0 |

**Filters** (`src/filters_mr.py`, `src/08_mr_candidates.py`)
- Slugs are percent-decoded. The mis-decoded UTF-8 in Pudhari's sitemaps is repaired exactly.
- Place terms: the B2 roman Belagavi place list, plus Marathi romanisations (belgaon, belgoan, nipni and others) and about 90 Devanagari names (district, taluks, towns, city localities and border villages).
- Crash and death terms in roman script: accident, killed, dies, death, mishap, collision, apghat and others.
- Crash and death terms in Devanagari: अपघात, ठार, मृत्यू, जागीच, धडक and others.
- **Pass 2** takes placeless crash slugs from regional sections only: Pudhari Kolhapur and latest, Sakal paschim-maharashtra, TV9 crime and maharashtra, and all of Tarun Bharat. Karnataka, Maharashtra, Goa and other places are excluded in both scripts. Pools larger than 200 were screened through a 50% `sample(random_state=1)`.
- **Pass 2b** (Tarun Bharat only, an extra check) addresses slug truncation. WordPress cuts Devanagari slugs at about 24 characters, so a crash word can be lost. A 50% sample of the truncated Devanagari place-only slugs was screened (183 of 366).

**Fetching**
- 889 articles were fetched: 888 returned `ok` and 1 returned `HTTP 502` (Tarun Bharat). There was no 403 or 429.
- Titles and short in-memory excerpts were read by hand.
- Three Tarun Bharat pages had mis-decoded titles and were re-read with UTF-8 forced. None was a road crash.
- One in-memory re-read of a Tarun Bharat page ran while the screening process was also fetching that host, so two requests may briefly have come less than 2 s apart.
- Screen logs are in `data/screen_logs_mr/`. This sub-folder keeps them out of the `screen_log*.csv` globs of `05_build_outputs.py`.

### B9.2 Coding

`data/killcheck_coding_belagavi_mr.csv` has 106 article rows:
- **75 core in-district fatal rows,** which collapse to 54 crashes.
- **10 non-fatal (N).**
- **14 outside the district (X),** for example:
  - Goa (Mapusa);
  - Chandgad and Radhanagari (Kolhapur);
  - Pandharpur, Dharwad, West Bengal and Chitradurga.
  - A Sakal headline placed a 7-death cruiser crash "in Belgaum"; on re-reading, the crash was in Dharwad taluk.
- **3 not road:** railway deaths and a farm tractor.
- **3 borderline:** tree falls already in the borderline set (C031, C042).

Tarun Bharat's first report of C002 gave 11 deaths. That was an early error, so C002 is coded with the final toll of 8.

### B9.3 De-duplication (`data/killcheck_dedup_check_belagavi_mr.csv`)

- **Matched existing crashes.** 17 Marathi crashes match existing crashes within 0 days, in the same taluk and with the same deaths: C001, C002, C004, C005, C006, C007, C010, C011, C012, C014, C021, C025, C035, C036, C037, C039 and C045.
- **New crashes.** 37 crashes with 39 deaths are new. Some have an existing crash within ±2 days, but each differs in place and victim. For example:
  - C071 (Hirebagewadi IB, a teacher) is not C022 (Desur cross, a soldier);
  - C070 (Basanalgadde, Chikkodi) is not C017 (Mutnal, NH-4).
- **IDs.** New IDs follow C045:
  - C046–C063 are the 18 crashes from Pudhari, Sakal and TV9 Marathi, unchanged from the first build;
  - C064–C082 are the crashes added by Tarun Bharat.
- **Within the Marathi outlets.** Pudhari and Tarun Bharat both reported the Rakaskop bridge truck crash (C062) and the Zadshahapur crash (C046).
- **Undetermined headlines.** Some new crashes may be the same events as the 13 undetermined Udayavani headlines of B3. Those headlines were never counted, so nothing is double-counted.

### B9.4 Recall (`data/killcheck_summary_belagavi_all.csv`)

| Scope | Crashes | Deaths | Recall, deaths (of 913) | Recall, fatal crashes (of 857) |
|---|---|---|---|---|
| Kannada + English (B4, unchanged) | 42 | 73 | 8.0% | 4.9% |
| Any Marathi outlet | 54 | 80 | 8.8% | 6.3% |
| — Tarun Bharat | 31 | 50 | 5.5% | 3.6% |
| — Sakal | 21 | 39 | 4.3% | 2.5% |
| — Pudhari | 16 | 33 | 3.6% | 1.9% |
| — TV9 Marathi | 3 | 7 | 0.8% | 0.4% |
| Marathi only (new) | 37 | 39 | 4.3% | 4.3% |
| **All-outlet union** | **79** | **112** | **12.3%** | **9.2%** |
| Union + borderline (sensitivity) | 82 | 115 | 12.6% | 9.6% |

**What Marathi adds.** The Marathi outlets add 37 crashes and 39 deaths:
- death recall rises from 8.0% to 12.3% (+4.3 points);
- fatal-crash recall almost doubles, from 4.9% to 9.2%.

**Crashes unique to one outlet**, as crashes (deaths):
- Tarun Bharat 19 (20);
- Sakal 12 (12);
- Pudhari 4 (4);
- TV9 Marathi 0.

**Tarun Bharat.** It is the best Marathi outlet, but at 5.5% it is still below Prajavani (6.1%). Without it, the union was 60 crashes and 92 deaths (10.1%). Pass 2b found only a duplicate report of C012, so slug truncation is not a material leak.

### B9.5 Subgroups, all-outlet union (`_by_road_user_belagavi_all`, `_by_unit_belagavi_all`, `_by_half_belagavi_all`)

| Road-user type | Official deaths | Kn + En | All outlets | Recall, all (Kn + En) |
|---|---|---|---|---|
| Two-wheeler | 443 | 35 | 58 | **13.1%** (7.9%) |
| Pedestrian | 144 | 5 | 8 | **5.6%** (3.5%) |
| Car/LMV | 91 | 30 | 33 | 36% (33%) |
| Truck/lorry | 68 | 0 | 2 | 2.9% (0%) |
| Bus | 12 | 2 | 3 | 25% (17%) |
| Bicycle | 19 | 0 | 1 | 5.3% (0%) |
| Other motor vehicle | 120 | 1 | 1 | 0.8% (0.8%) |
| Unknown type | — | 0 | 6 | — |

| Unit | Deaths, Kn + En | Deaths, all | Recall, deaths | Recall, fatal crashes |
|---|---|---|---|---|
| Belagavi City | 7 | 16 | **9.6%** (was 4.2%) | 10.3% (16 of 155) |
| Belagavi Dist | 66 | 96 | **12.9%** (was 8.8%) | 9.0% (63 of 702) |

**By half-year**
- January–June: 52 of 504 deaths (10.3%), up from 5.6%.
- July–December: 60 of 409 deaths (14.7%), up from 11.0%.

**By month.** The Spearman correlation of official and news deaths by month is 0.02. There is still no seasonal signal.

**Where the Marathi press helps.** It fills in the Marathi-reading belt:
- Belagavi city;
- rural Belagavi taluk (Machhe, Piranwadi, Honga, Bhutramanhatti);
- Khanapur, Chikkodi and Nippani.

Gokak, Ramdurg, Saundatti and Athani gain almost nothing.

### B9.6 Severity (`data/killcheck_severity_belagavi_all.csv`)

| Scope | Crashes | Single-death crashes | Multi-death crashes (their deaths) | Deaths per crash |
|---|---|---|---|---|
| Kannada + English | 42 | 23 (55%) | 19 (50) | 1.74 |
| **Marathi only** | **37** | **35 (95%)** | 2 (4) | **1.05** |
| All-outlet union | 79 | 58 (73%) | 21 (54) | 1.42 |
| Official 2022 | 857 | — | — | 1.07 |

**The Marathi-only crashes are almost all single-death.**
- 35 of the 37 killed one person.
- The two exceptions each killed two: the Zadshahapur bike crash (C046) and the chilli-container crash in Tavandi ghat (C066).
- Their 1.05 deaths per crash matches the official 1.07.

So the Marathi local press records the routine crashes that the Kannada and English press misses, especially in the city. The union is still more severity-weighted than the official file (1.42 deaths per crash).

### B9.7 Bounds and implication for B0

**Bounds**
- **Unscreened pass-2 half.** Tarun Bharat's sampled pass-2 half gave 10 new crashes (11 deaths), so the unscreened half probably holds about 10 more crashes (about 11 deaths).
- **Belgaum Live.** Its 194 crash-slug candidates could not be screened: the site stopped accepting connections after the sitemap harvest (three attempts, about 25 minutes apart in total). It is a Belgaum-only site, so it could add a few dozen more, much of it overlapping with Tarun Bharat.
- **Estimate.** An exhaustive screen of the four usable outlets would probably reach about 120–125 deaths (**13–14%**). Belgaum Live could raise this somewhat.

**Implication for B0.** The Marathi press moves Belagavi's death recall from 8.0% to 12.3%, just above the 10% kill threshold. Fatal-crash recall (9.2%) is still just below the threshold, and Belagavi remains about 3 times below DK (35.6%). The B0 conclusion therefore holds in a weaker form:
- a Belagavi news file needs Kannada and Marathi sources together;
- even then, it records only about one death in eight;
- the capture pattern differs by language (Marathi is strong in the city and the western taluks, absent in the east), which adds further heterogeneity to any capture model.

### B9.8 Files and code

| File | Contents |
|---|---|
| `src/06_mr_probe.py`, `src/07_mr_harvest.py` | robots and archive probe; harvest jobs `pu`, `sk`, `tb`, `t9`, `bl` (reuses `harvest()` from `02_harvest_sitemaps.py`) |
| `src/filters_mr.py`, `src/08_mr_candidates.py`, `src/04b_screen_mr.py`, `src/09_mr_build_outputs.py` | Marathi filters, candidates, screening and build (run with `KC_DISTRICT=belagavi`) |
| `raw/sitemaps/{pu,sk,tb,t9,bl}_2022.csv` (+ `_log`), `raw/mr_probe/` | URL lists only; see the note below on Belgaum Live |
| `data/candidates_*_belagavi_mr.csv`, `data/sitemap_screen_counts_belagavi_mr.csv` | URL-level candidates (pass 1, pass 2, pass 2b) |
| `data/screen_logs_mr/screen_log_<pass>_<outlet>.csv` | Every fetch: URL, outlet, language, date, status, keyword flags |
| `data/killcheck_coding_belagavi_mr.csv` | Hand coding (106 rows) |
| `data/killcheck_crashes_belagavi_mr.csv` | 54 Marathi-found crashes, with `match_existing_id` |
| `data/killcheck_crashes_belagavi_mr_new.csv` | The 37 new crashes, in exactly the columns of `killcheck_crashes_belagavi.csv` (C046–C082) |
| `data/killcheck_crashes_belagavi_all.csv` | Union crash file (79 crashes), with Kannada/English and Marathi outlet lists |
| `data/killcheck_summary_belagavi_all.csv`, `_recall_by_road_user/_unit/_half/_month_belagavi_all`, `_overlap_belagavi_all`, `_severity_belagavi_all` | Union recall tables |
| `data/killcheck_articles_belagavi_mr.csv`, `data/killcheck_dedup_check_belagavi_mr.csv`, `data/build_log_belagavi_mr.txt` | Article file (889), de-duplication check, build log |

The Belgaum Live harvest stopped at post-sitemap 82, past the 2022 `lastmod` window. Post-sitemap 6 timed out; it holds 2026 posts.

**Text audit**
- No log field other than the URL is longer than 12 characters, and the only non-`ok` status is `HTTP 502`.
- None of the 20 new output CSVs has a Devanagari or Kannada character outside the URL columns.
- The temporary excerpt files were deleted.
