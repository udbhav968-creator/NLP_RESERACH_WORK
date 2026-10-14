"""LegalDiff: language-aware legal-difference features + rule-based error typing and explanations.
Lexicons cover English (en), Hindi (hi) and a small French (fr) list used only for the FrJUDGE transfer check."""
import re, unicodedata

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

NUM_WORDS = {
    "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
           "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "twenty-four": 24, "thirty": 30, "forty-eight": 48,
           "fifty": 50, "ninety-first": 91, "twice": 2, "double": 2, "half": 0.5, "first": 1, "fifth": 5, "lakh": 100000},
    "hi": {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
           "ग्यारह": 11, "बारह": 12, "पंद्रह": 15, "बीस": 20, "चौबीस": 24, "तीस": 30, "अड़तालीस": 48, "पचास": 50,
           "इक्यानवेवें": 91, "दोगुना": 2, "दोगुने": 2, "आधा": 0.5, "पाँचवें": 5, "लाख": 100000},
    "fr": {"un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
           "douze": 12, "quinze": 15, "trente": 30},
}
TIME_UNITS = {
    "en": ["day", "days", "month", "months", "year", "years", "hour", "hours", "week", "weeks", "date", "time", "convenient", "immediately"],
    "hi": ["दिन", "दिनों", "माह", "महीने", "महीनों", "महीना", "वर्ष", "वर्षों", "साल", "सालों", "घंटे", "घंटों", "घंटा", "सप्ताह", "हफ्ते", "हफ़्ते", "तारीख", "तिथि", "समय", "सुविधा"],
    "fr": ["jour", "jours", "mois", "an", "ans", "année", "années", "heure", "heures", "semaine", "semaines", "date", "délai"],
}
UNIT_CANON = {}
for _c, _ws in {"day": ["day", "days", "दिन", "दिनों", "jour", "jours"],
                "month": ["month", "months", "माह", "महीने", "महीनों", "महीना", "mois"],
                "year": ["year", "years", "वर्ष", "वर्षों", "साल", "सालों", "an", "ans", "année", "années"],
                "hour": ["hour", "hours", "घंटे", "घंटों", "घंटा", "heure", "heures"],
                "week": ["week", "weeks", "सप्ताह", "हफ्ते", "हफ़्ते", "semaine", "semaines"],
                "date": ["date", "तारीख", "तिथि"]}.items():
    for _w in _ws: UNIT_CANON[_w] = _c
def unit(w): return UNIT_CANON.get(w, w)
MULT = {"lakh": 1e5, "लाख": 1e5, "crore": 1e7, "करोड़": 1e7, "thousand": 1e3, "हज़ार": 1e3, "हजार": 1e3, "million": 1e6}
ELISIONS = {"l'", "d'", "n'", "s'", "c'", "j'", "m'", "t'", "qu'", "lorsqu'", "jusqu'", "puisqu'"}
LEX = {
    "neg": {"en": ["not", "no", "never", "cannot", "nor", "without", "neither", "none"], "hi": ["नहीं", "न", "कभी", "बिना"],
            "fr": ["ne", "pas", "aucun", "aucune", "jamais", "n'", "ni", "sans"]},
    "oblig": {"en": ["shall", "must", "required", "compulsory", "mandatory", "liable", "responsible", "always"],
              "hi": ["होगा", "होगी", "होंगे", "होंगी", "करेगा", "करेगी", "करेंगे", "अनिवार्य", "ज़रूरी", "जरूरी", "उत्तरदायी", "हमेशा"],
              "fr": ["doit", "doivent", "obligatoire", "tenu", "tenue", "exige"]},
    "perm": {"en": ["may", "can", "entitled", "optional", "should", "try", "convenient", "allowed", "permitted", "option"],
             "hi": ["सकता", "सकती", "सकते", "वैकल्पिक", "चाहें", "चाहिए", "कोशिश", "हकदार", "सुविधा", "विकल्प"],
             "fr": ["peut", "peuvent", "facultatif", "possible", "droit"]},
    "cond": {"en": ["if", "unless", "provided", "subject", "only", "when", "where", "long", "case", "after", "before", "until"],
             "hi": ["यदि", "अगर", "बशर्ते", "तभी", "जब", "केवल", "शर्त", "बाद", "पहले", "तक"],
             "fr": ["si", "lorsque", "lorsqu'", "seulement", "condition", "après", "avant", "jusqu'", "dès"]},
    "exc": {"en": ["except", "unless", "excepted", "excluding", "other", "apart", "save", "besides", "but"],
            "hi": ["सिवाय", "छोड़कर", "अलावा", "अतिरिक्त", "लेकिन", "किंतु"],
            "fr": ["sauf", "excepté", "exception", "hormis", "mais"]},
    "quant": {"en": ["all", "any", "every", "each", "only", "entire", "full", "total", "whole", "either", "both", "solely", "single", "mainly", "never"],
              "hi": ["सभी", "सारा", "सारी", "सारे", "कोई", "हर", "प्रत्येक", "केवल", "ही", "पूरा", "पूरी", "कुल", "किसी", "मुख्यतः", "एक"],
              "fr": ["tout", "tous", "toute", "toutes", "chaque", "seul", "seule", "entier", "total", "aucun"]},
}
ROLES = {
    "en": {"insurer": "INSURER", "company": "INSURER", "insured": "INSURED", "you": "INSURED", "your": "INSURED", "policyholder": "INSURED",
           "nominee": "NOMINEE", "landlord": "LANDLORD", "tenant": "TENANT", "broker": "BROKER", "court": "COURT", "authority": "AUTHORITY",
           "doctor": "DOCTOR", "administrator": "TPA", "police": "POLICE", "society": "SOCIETY", "neighbours": "THIRD", "person": "THIRD", "party": "THIRD"},
    "hi": {"बीमाकर्ता": "INSURER", "कंपनी": "INSURER", "बीमित": "INSURED", "आप": "INSURED", "आपको": "INSURED", "आपके": "INSURED", "आपकी": "INSURED",
           "आपका": "INSURED", "आपसे": "INSURED", "पॉलिसीधारक": "INSURED", "नामांकित": "NOMINEE", "मालिक": "LANDLORD", "किरायेदार": "TENANT",
           "ब्रोकर": "BROKER", "अदालत": "COURT", "प्राधिकरण": "AUTHORITY", "डॉक्टर": "DOCTOR", "चिकित्सक": "DOCTOR", "प्रशासक": "TPA",
           "पुलिस": "POLICE", "सोसाइटी": "SOCIETY", "पड़ोसियों": "THIRD", "व्यक्ति": "THIRD", "पक्ष": "THIRD"},
    "fr": {"assureur": "INSURER", "assuré": "INSURED", "assurée": "INSURED", "vous": "INSURED", "votre": "INSURED", "personne": "THIRD", "tiers": "THIRD"},
}
# keep every lexicon in NFC so it matches NFC-normalised tokens (nukta letters such as ज़ / ड़)
_N = lambda w: unicodedata.normalize("NFC", w)
NUM_WORDS = {l: {_N(w): v for w, v in d.items()} for l, d in NUM_WORDS.items()}
TIME_UNITS = {l: [_N(w) for w in ws] for l, ws in TIME_UNITS.items()}
LEX = {c: {l: [_N(w) for w in ws] for l, ws in d.items()} for c, d in LEX.items()}
ROLES = {l: {_N(w): v for w, v in d.items()} for l, d in ROLES.items()}
UNIT_CANON = {_N(w): c for w, c in UNIT_CANON.items()}
MULT = {_N(w): v for w, v in MULT.items()}

FEATURE_NAMES = ["num_missing", "num_added", "dur_mismatch", "neg_diff", "neg_absdiff", "oblig_diff", "perm_diff", "modal_flip",
                 "cond_lost", "cond_added", "exc_lost", "exc_added", "quant_absdiff", "role_jaccard_dist", "role_subject_change",
                 "len_ratio", "coverage", "novelty", "time_word_change"]

def detect_lang(text):
    if re.search(r"[ऀ-ॿ]", text): return "hi"
    if re.search(r"[éèêàçùâîôû]|\b(le|la|les|des|est|une)\b", text.lower()): return "fr"
    return "en"

_ALL_NUM_WORDS = None
def tokens(text):
    """Lower-cased word tokens. Devanagari danda (। ॥) is punctuation, n't -> not, possessive 's removed,
    French elisions split (l'assureur -> l' assureur), hyphenated compounds split unless they are number words."""
    global _ALL_NUM_WORDS
    if _ALL_NUM_WORDS is None: _ALL_NUM_WORDS = {w for d in NUM_WORDS.values() for w in d}
    t = unicodedata.normalize("NFC", text).translate(DEV_DIGITS).lower()
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"n't\b", " not", t)
    t = re.sub(r"(?<=\w)'s\b", "", t)
    t = re.sub(r"\b(\w{1,7}')(?=\w)", r"\1 ", t)
    out = []
    for w in re.findall(r"[\wऀ-ॣ०-ॿ'\-]+|[%₹]", t):
        if w not in ELISIONS: w = w.strip("'")
        w = w.strip("-")
        if not w: continue
        if "-" in w and w not in _ALL_NUM_WORDS: out.extend(p for p in w.split("-") if p)
        else: out.append(w)
    return out

def _num(s):
    return float(s.replace(",", ""))

def numbers(text, lang):
    t = unicodedata.normalize("NFC", text).translate(DEV_DIGITS).lower()
    vals = []
    # Indian-format and plain numerals: "15,00,000", "25,000", "1%", "91st", "2 lakh", "1 crore"
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", t):
        v = _num(m.group(0))
        mm = re.match(r"\s*([^\s\d,.;:]+)", t[m.end():m.end() + 12])
        if mm and mm.group(1) in MULT: v *= MULT[mm.group(1)]
        vals.append(v)
    toks = tokens(text)
    words = NUM_WORDS.get(lang, {})
    units = set(TIME_UNITS.get(lang, []))
    for i, w in enumerate(toks):
        if w in words and w not in ("lakh", "लाख", "first"):
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            # "one"/"एक"/"un" are also articles ("a"): count them only before a time unit or multiplier
            if w in ("one", "एक", "un") and nxt not in units and nxt not in MULT: continue
            v = float(words[w])
            if nxt in MULT: v *= MULT[nxt]
            vals.append(v)
    return vals

def durations(text, lang):
    toks = tokens(text); units = set(TIME_UNITS.get(lang, []))
    out = []
    for i, w in enumerate(toks):
        if w in units:
            window = " ".join(toks[max(0, i - 3):i])
            nums = numbers(window, lang)
            out.append((nums[-1] if nums else None, unit(w)))
    return out

def count(toks, cat, lang):
    lex = set(LEX[cat].get(lang, []))
    return sum(1 for w in toks if w in lex)

def modal_counts(toks, lang):
    """(obligation, permission) counts. A negated permission ("cannot", "may not", "नहीं ... सकता", "ne peut pas")
    is a prohibition, i.e. the same deontic force as "shall not", so it is counted as obligation, not permission."""
    ob_lex, pe_lex, neg = set(LEX["oblig"].get(lang, [])), set(LEX["perm"].get(lang, [])), set(LEX["neg"].get(lang, []))
    ob = pe = 0
    for i, w in enumerate(toks):
        if w in ob_lex: ob += 1
        elif lang == "en" and w == "cannot": ob += 1
        elif w in pe_lex:
            before, after = toks[max(0, i - (4 if lang == "hi" else 2)):i], toks[i + 1:i + 3]
            negated = any(x in neg for x in before) or (lang != "hi" and any(x in neg for x in after))
            if negated: ob += 1
            else: pe += 1
    return ob, pe

def roles(toks, lang):
    r = ROLES.get(lang, {})
    seq = [r[w] for w in toks if w in r]
    return seq

def features(original, simplification, lang=None):
    lang = lang or detect_lang(original)
    to, ts = tokens(original), tokens(simplification)
    no, ns = numbers(original, lang), numbers(simplification, lang)
    from collections import Counter
    co, cs = Counter(no), Counter(ns)
    num_missing = sum((co - cs).values()); num_added = sum((cs - co).values())
    do, ds = durations(original, lang), durations(simplification, lang)
    dur_mismatch = len(set(do) ^ set(ds)) if (do or ds) else 0
    f = {}
    f["num_missing"], f["num_added"], f["dur_mismatch"] = num_missing, num_added, min(dur_mismatch, 4)
    neg_o, neg_s = count(to, "neg", lang), count(ts, "neg", lang)
    f["neg_diff"] = neg_s - neg_o; f["neg_absdiff"] = abs(neg_s - neg_o)
    (ob_o, pe_o), (ob_s, pe_s) = modal_counts(to, lang), modal_counts(ts, lang)
    f["oblig_diff"] = ob_s - ob_o; f["perm_diff"] = pe_s - pe_o
    f["modal_flip"] = int((ob_o > 0 and ob_s == 0 and pe_s > pe_o) or (pe_o > 0 and pe_s == 0 and ob_s > ob_o) or (pe_s > pe_o and ob_s < ob_o))
    c_o, c_s = count(to, "cond", lang), count(ts, "cond", lang)
    e_o, e_s = count(to, "exc", lang), count(ts, "exc", lang)
    f["cond_lost"] = max(c_o - c_s, 0); f["cond_added"] = max(c_s - c_o, 0)
    f["exc_lost"] = max(e_o - e_s, 0); f["exc_added"] = max(e_s - e_o, 0)
    f["quant_absdiff"] = abs(count(to, "quant", lang) - count(ts, "quant", lang))
    ro, rs = roles(to, lang), roles(ts, lang)
    so, ss = set(ro), set(rs)
    f["role_jaccard_dist"] = 1 - (len(so & ss) / len(so | ss)) if (so | ss) else 0.0
    f["role_subject_change"] = int(bool(ro) and bool(rs) and ro[0] != rs[0])
    f["len_ratio"] = len(ts) / max(len(to), 1)
    vo, vs = set(to), set(ts)
    f["coverage"] = len(vo & vs) / max(len(vo), 1)
    f["novelty"] = len(vs - vo) / max(len(vs), 1)
    tu = set(TIME_UNITS.get(lang, []))
    f["time_word_change"] = len({unit(w) for w in to if w in tu} ^ {unit(w) for w in ts if w in tu})
    return [float(f[k]) for k in FEATURE_NAMES], f, lang

# ---------------- Explanation / error typing -----------------
def explain(original, simplification, score, lang=None):
    """Return (error_type, explanation) using the LegalDiff features; score = model LMP prediction."""
    _, f, lang = features(original, simplification, lang)
    no, ns = numbers(original, lang), numbers(simplification, lang)
    if score >= 7.5:
        return "NONE", "Legal meaning appears preserved; no legally salient difference detected."
    def fmt(v): return str(int(v)) if float(v).is_integer() else str(v)
    to, ts = tokens(original), tokens(simplification)
    pol_o, pol_s = count(to, "neg", lang) > 0, count(ts, "neg", lang) > 0
    ro, rs = roles(to, lang), roles(ts, lang)
    if pol_o != pol_s and not f["modal_flip"]:
        return "NEGATION", "Polarity changed: negation %s in the simplification, reversing the rule." % ("added" if pol_s else "removed")
    if f["modal_flip"] or (f["oblig_diff"] != 0 and f["perm_diff"] != 0 and f["oblig_diff"] * f["perm_diff"] < 0):
        return "MODALITY", "Deontic force changed (obligation vs. permission/discretion)."
    miss = sorted(set(no) - set(ns)); add = sorted(set(ns) - set(no))
    is_time = f["dur_mismatch"] > 0 or f["time_word_change"] > 0
    if miss and add:
        et = "DATE" if is_time else "NUMBER"
        return et, "%s changed: %s -> %s." % ("Time limit" if is_time else "Amount/quantity", ", ".join(map(fmt, miss)), ", ".join(map(fmt, add)))
    if add and f["len_ratio"] > 1.15:
        return "HALLUC", "New figure(s) %s introduced together with content absent from the original." % ", ".join(map(fmt, add))
    if set(rs) - set(ro) or f["role_subject_change"]:
        return "ENTITY", "Rights/duties assigned to a different party (%s)." % ", ".join(sorted(set(rs) - set(ro)) or ["subject changed"])
    if f["exc_lost"] > 0:
        return "EXC_REMOVED", "An exception/carve-out in the original is missing, widening the rule."
    if f["len_ratio"] > 1.15 or f["cond_added"] or f["exc_added"]:
        return "HALLUC", "Simplification adds content (new duty, condition or benefit) absent from the original."
    if miss and is_time:
        return "DATE", "Time limit (%s) removed or altered." % ", ".join(map(fmt, miss))
    if score >= 5.5:
        return "MINOR", "Minor detail omitted; core legal effect largely retained."
    if miss or f["cond_lost"] > 0 or f["len_ratio"] < 0.75:
        return "OMIT_COND", "A condition or qualifying clause of the original is omitted."
    if f["quant_absdiff"] > 0:
        return "SCOPE", "Scope changed (quantifier/coverage such as any/only/all differs)."
    return "SCOPE", "Legal scope of the rule differs from the original."
