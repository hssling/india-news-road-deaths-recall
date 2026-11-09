"""Marathi-outlet URL filters for the Belagavi check (extends filters.py; filters.py itself is unchanged).

Slugs are matched after percent-decoding (Tarun Bharat slugs are Devanagari). Place evidence is the
roman Belagavi token list of filters.py plus Marathi-romanised variants and Devanagari names of the
district, its taluks and the localities most often named in Marathi reports. Crash evidence is the
roman crash-token list of filters.py plus Marathi terms in roman and Devanagari script.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filters as F  # noqa: E402  (KC_DISTRICT must be 'belagavi')

assert F.PLACE_PREFIX is F.BEL_PLACE_PREFIX, "run with KC_DISTRICT=belagavi"

# Marathi-romanised spellings seen in Pudhari / Sakal / Belgaum Live slugs (prefix match on tokens)
MR_PLACE_PREFIX = F.BEL_PLACE_PREFIX + [
    "belgaon", "belgav", "belagaon", "belgoan", "belgum", "belgam", "nipni", "chikkodi", "nipanee", "sankeshwar", "sankeswar", "hukeri", "kagwad",
    "uchgaon", "uchagaon", "yellur", "yelloor", "yallur", "anagol", "angol", "kangrali", "hindalga", "machhe",
    "machche", "piranwadi", "kakti", "halga", "kanakumbi", "kankumbi", "belgundi", "bachi", "jamboti",
    "nandgad", "londa", "gunji", "ramdurg", "saundatti", "savdatti", "bailhongal", "kittur",
    "mudalgi", "raibag", "kudchi", "ugar", "shedbal", "athni", "gokak", "ghataprabha", "hirebagewadi",
    "sutgatti", "kanbargi", "vantmuri", "honga", "bijgarni", "kinaye", "sulga", "rajhans", "khadarwadi",
    "dhamne", "mutage", "kadolkar", "shindolli", "basurte", "kallehol", "majgaon", "tilakwadi",
]
MR_PLACE_EXACT = F.BEL_PLACE_EXACT | {"bgm"}
# Devanagari (Marathi) names: district, taluks, towns, Belgaum-city localities and border villages
MR_PLACE_DEV = re.compile(
    "बेळगाव|बेळगावी|बेळगांव|बेलगाम|बेळगावात|बेळगावच|चिक्कोडी|चिकोडी|निपाणी|खानापूर|अथणी|हुक्केरी|गोकाक|"
    "घटप्रभा|रामदुर्ग|सौंदत्ती|सवदत्ती|बैलहोंगल|संकेश्वर|कित्तूर|रायबाग|मुडलगी|मूडलगी|कागवाड|यरगट्टी|कुडची|उगार|"
    "हिरेबागेवाडी|काकती|हिंडलगा|हिंडलगी|उचगाव|येळ्ळूर|कंग्राळी|मच्छे|पिरनवाडी|अनगोळ|टिळकवाडी|शहापूर|वडगाव|"
    "सांबरा|हलगा|जांबोटी|नंदगड|लोंढा|कणकुंबी|बेळगुंदी|बाची|कडोली|सुळगा|बस्तवाड|मुतगा|गोजगा|आंबेवाडी|"
    "होनगा|भुतरामहट्टी|सुतगट्टी|यमकनमर्डी|स्तवनिधी|कोगनोळी|बोरगाव|कुर्ली|मांगूर|अक्कोळ|सदलगा|शेडबाळ|"
    "ऐनापूर|मोळे|कारदगा|गळतगा|जत्राट|बेनाडी|ममदापूर|शिरगुप्पी")
# Ambiguous Devanagari names (also in Maharashtra): शहापूर (Thane), वडगाव (many), बोरगाव (many), भोज.
# They are allowed to make a slug a candidate; in_district is decided at coding from the text.

MR_CRASH_DEV = re.compile(
    "अपघात|ठार|मृत्यू|मृत्यु|जागीच|धडक|उलटून|उलटली|उलटला|पलटी|चिरडून|चिरडले|दुचाकी|ट्रक|कंटेनर|टँकर|"
    "टेम्पो|ट्रॅक्टर|डंपर|रिक्षा|बसची|बसला|बसने|कारची|कारला|कारने|जीप|क्रुझर|दुर्घटना|गतप्राण|प्राण गमाव|"
    "जखमी|मृत|मरण|बळी|ठोकर|ठोकरले")
MR_CRASH_ROMAN = ["apghat", "apaghat", "aphghat", "thar", "mrutyu", "mrityu", "jagich", "dhadak", "dhadkel",
                  "dhadakel", "ulatli", "ulatun", "dumper", "container", "cruiser", "tractor", "biker", "riders",
                  "dies", "killed", "accident", "accidental", "mishap", "collision", "death", "dead"]
# road-unrelated noise for Marathi slugs (temple-car festivals, theft, drowning, wildlife, politics ...)
MR_NOISE = re.compile(
    r"covid|corona|positive|rathotsav|rath-yatra|theft|stolen|chori|चोरी|drown|बुडून|बुडाल|suicide|आत्महत्या|"
    r"murder|खून|हत्या|leopard|बिबट|elephant|हत्ती|gava|गवा|election|निवडणूक|cricket|क्रिकेट|film|movie|"
    r"चित्रपट|fire-brigade|electrocut|शॉक|विजेचा|lightning|वीज कोसळ|snake|साप|dog-bite|कुत्र")
ROMAN_OTHER = F.ROUNDUP


def dec(url):
    return unquote(url.lower().split("?")[0])


def slug_of(url):
    return unquote(F.slug_of(url))


# compiled equivalents of the token-prefix loops (token = maximal [a-z0-9] run; prefix match at token start)
_B = r"(?<![a-z0-9])"
_PLACE_RE = re.compile(_B + "(?:" + "|".join(sorted(map(re.escape, set(MR_PLACE_PREFIX)), key=len, reverse=True))
                       + ")|" + _B + "(?:" + "|".join(map(re.escape, MR_PLACE_EXACT)) + ")(?![a-z0-9])")
_short = [p for p in F.CRASH_PREFIX if len(p) <= 4]
_long = [p for p in F.CRASH_PREFIX if len(p) > 4] + MR_CRASH_ROMAN
_CRASH_RE = re.compile(_B + "(?:" + "|".join(map(re.escape, _short)) + ")(?![a-z0-9])|" + _B + "(?:"
                       + "|".join(sorted(map(re.escape, set(_long)), key=len, reverse=True)) + ")|"
                       + _B + r"two[^a-z0-9]+wheeler|" + _B + r"run[^a-z0-9]+over")


def has_place(text):
    t = unquote(text).lower()
    return bool(MR_PLACE_DEV.search(t) or F.BEL_PLACE_KN.search(t) or _PLACE_RE.search(t))


def has_crash(text):
    t = unquote(text).lower()
    return bool(MR_CRASH_DEV.search(t) or _CRASH_RE.search(t))


def _has_place_slow(text):  # reference implementation (used by the self-test only)
    t = unquote(text)
    if MR_PLACE_DEV.search(t) or F.BEL_PLACE_KN.search(t):
        return True
    return any(x in MR_PLACE_EXACT or any(x.startswith(p) for p in MR_PLACE_PREFIX) for x in F.tokens(t))


def _has_crash_slow(text):
    t = unquote(text)
    if MR_CRASH_DEV.search(t) or F.has_crash(t):
        return True
    return any(any(x.startswith(p) for p in MR_CRASH_ROMAN) for x in F.tokens(t))


def is_candidate(url, section=False):
    path, slug = dec(url), slug_of(url)
    if not (has_place(path) or section):
        return False, ""
    if any(r in slug for r in ROMAN_OTHER):
        return True, "roundup"
    if has_crash(slug):
        return True, "crash_term"
    return False, ""
