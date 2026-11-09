"""Slug filters for district road-crash candidates (token-based).

District is chosen by district_cfg (env KC_DISTRICT; default 'dk' = Dakshina Kannada, unchanged).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import district_cfg  # noqa: E402

# DK district / taluk / town / locality tokens (prefix match on slug tokens)
DK_PLACE_PREFIX = [
    "mangalur", "mangalor", "mluru", "dakshina", "puttur", "puttoor", "bantwal", "bantval",
    "belthang", "beltang", "belthngady", "sullia", "sullya", "sulya", "ullal", "surathkal", "suratkal",
    "moodbidri", "moodabidri", "mudbidri", "moodubidire", "mudubidire", "moodbidre", "kadaba", "vitla", "vittal",
    "mulki", "uppinang", "bajpe", "kateel", "subrahmanya", "subramanya", "kukke", "dharmasthala",
    "ujire", "kinnigoli", "konaje", "farangipet", "kalladka", "nelyadi", "gundya", "shiradi", "charmadi",
    "sampaje", "jalsoor", "jalsur", "bellare", "kotekar", "thokkottu", "thokottu", "tokkottu", "deralakatte",
    "kankanady", "pumpwel", "panambur", "nanthoor", "padil", "kavoor", "kuloor", "bikarnakatte", "hampankatta",
    "kottara", "bondel", "haleangadi", "gurpur", "guruvayanakere", "guruvayankere", "punjalkatte", "madanthyar",
    "venoor", "naravi", "aladangady", "kokkada", "kaniyoor", "aranthodu", "kumbra", "kabaka", "saletoor",
    "kaikamba", "polali", "siddakatte", "mudipu", "talapady", "thalapady", "pilikula", "vamanjoor",
    "neermarga", "baikampady", "jeppu", "kadri", "permude", "edapadavu", "panemangalore", "melkar",
    "kudupu", "mukka", "kulai", "maripalla", "kallapu", "valachil", "ganjimutt",
]
DK_PLACE_EXACT = {"dk", "bc"}  # 'dk' = Dakshina Kannada; 'bc' as in bc-road

# Belagavi district: city, 15 taluks (incl. new Mudalgi, Kagwad, Yaragatti, Kittur, Nippani) and
# frequently reported towns / localities, with transliteration variants (prefix match on slug tokens).
# Ambiguous names shared with other districts (Kerur, Bagewadi, Itagi, Konnur, Kabbur, Nagaral, Mamadapur)
# are deliberately left out; they are reached by the district section filter and pass 2 instead.
BEL_PLACE_PREFIX = [
    "belagavi", "belgaum", "belgavi", "belagav", "belgam", "belagaavi", "gokak", "ghataprabha", "ghatprabha",
    "chikkodi", "chikodi", "athani", "nippani", "nipani", "bailhongal", "bailahongal", "saundatti", "soundatti",
    "savadatti", "savadathi", "savdatti", "ramdurg", "ramadurg", "khanapur", "hukkeri", "hukeri", "raibag",
    "raybag", "rayabag", "kittur", "kitturu", "mudalgi", "mudalagi", "kagwad", "kagawad", "yaragatti",
    "yargatti", "sankeshwar", "sankeshwara", "kudachi", "harugeri", "sadalga", "ankali", "yamakanmardi",
    "kakati", "hirebagewadi", "hindalga", "udyambag", "tilakwadi", "kanabargi", "nesargi", "murgod",
    "munavalli", "londa", "jamboti", "nandgad", "mangasuli", "shedbal", "ainapur",
    "telsang", "ghodageri", "kangrali", "peeranwadi", "machhe", "desur",
    "kadoli", "ugar", "katkol", "torgal", "sureban", "ankalgi", "akkatangerhal",
    "chachadi", "hulkund", "hirekodi", "examba", "sadalaga", "bedkihal", "karoshi",
]
BEL_PLACE_EXACT = {"bgm", "sambra"}  # Sambra (airport) exact only
# Kannada-script district / taluk names (matched on decoded URL or title text)
BEL_PLACE_KN = re.compile("ಬೆಳಗಾವಿ|ಬೆಳಗಾಂ|ಗೋಕಾಕ|ಘಟಪ್ರಭಾ|ಚಿಕ್ಕೋಡಿ|ಅಥಣಿ|ನಿಪ್ಪಾಣಿ|ಬೈಲಹೊಂಗಲ|ಸವದತ್ತಿ|ರಾಮದುರ್ಗ|"
                          "ಖಾನಾಪುರ|ಹುಕ್ಕೇರಿ|ರಾಯಬಾಗ|ಕಿತ್ತೂರು|ಮೂಡಲಗಿ|ಕಾಗವಾಡ|ಯರಗಟ್ಟಿ|ಸಂಕೇಶ್ವರ|ಕುಡಚಿ|ಹಾರೂಗೇರಿ|ಮುರಗೋಡ|ಕಾಕತಿ|"
                          "ಹಿರೇಬಾಗೇವಾಡಿ|ಮುನವಳ್ಳಿ|ಉಗಾರ")
if district_cfg.KEY == "belagavi":
    PLACE_PREFIX, PLACE_EXACT, PLACE_KN = BEL_PLACE_PREFIX, BEL_PLACE_EXACT, BEL_PLACE_KN
else:
    PLACE_PREFIX, PLACE_EXACT, PLACE_KN = DK_PLACE_PREFIX, DK_PLACE_EXACT, None

CRASH_PREFIX = [
    "accident", "crash", "collision", "collid", "kill", "death", "dead", "mishap", "overturn", "topple",
    "bike", "scooter", "motorcycl", "two-wheeler", "twowheeler", "lorry", "lorries", "truck", "tanker", "bus",
    "jeep", "rickshaw", "pickup", "tempo", "bolero", "omni", "rider", "pillion", "pedestrian",
    "apagh", "apag", "aphag", "savu", "mrut", "mruth", "fatal", "tipper", "ksrtc", "ambulance", "skid",
    "vehicle", "car", "cars", "van", "auto", "hit", "hits", "run", "runs", "ran", "rammed", "rams",
    "die", "dies", "died", "dying", "succumb", "injur", "hurt", "biker", "scooty", "highway", "nh",
]
ROUNDUP = ["crime-news", "crime-brief", "news-in-brief", "briefs", "crime-roundup", "dk-news", "crime-report"]


def slug_of(url):
    s = url.lower().split("?")[0].rstrip("/")
    parts = s.split("/")
    if "articleshow" in parts:  # Times of India: slug precedes /articleshow/<id>.cms
        return parts[parts.index("articleshow") - 1]
    s = parts[-1]
    return re.sub(r"\.(html|cms|ece)$", "", s)


def tokens(text):
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def has_place(text):
    if PLACE_KN is not None and PLACE_KN.search(text):
        return True
    toks = tokens(text)
    return any(t in PLACE_EXACT or any(t.startswith(p) for p in PLACE_PREFIX) for t in toks)


def has_crash(text):
    toks = tokens(text)
    joined = "-".join(toks)
    if "two-wheeler" in joined or "run-over" in joined:
        return True
    for t in toks:
        for p in CRASH_PREFIX:
            if len(p) <= 4:
                if t == p:
                    return True
            elif t.startswith(p):
                return True
    return False


def is_candidate(url, section_is_dk=False):  # section_is_dk = URL is in the district's section
    path = url.lower().split("?")[0]
    slug = slug_of(url)
    if not (has_place(path) or section_is_dk):
        return False, ""
    if any(r in slug for r in ROUNDUP):
        return True, "roundup"
    if has_crash(slug):
        return True, "crash_term"
    return False, ""
