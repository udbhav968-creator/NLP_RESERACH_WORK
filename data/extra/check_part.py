"""Validate one extra-perturbation part file. Usage: python3 check_part.py part_ins_a.py"""
import sys, os, re, importlib.util, collections
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.dirname(HERE)
sys.path.insert(0, DATA)
import en_insurance, en_tenancy, hi_insurance, hi_tenancy

TYPES = {"NEGATION": (1, 2), "MODALITY": (1, 3), "NUMBER": (2, 3), "DATE": (2, 4), "OMIT_COND": (1, 5), "EXC_REMOVED": (2, 3),
         "SCOPE": (2, 5), "ENTITY": (1, 3), "HALLUC": (1, 4), "MINOR": (5, 7)}
EN = {r[0]: r for r in en_insurance.ROWS + en_tenancy.ROWS}
HI = {r[0]: r for r in hi_insurance.ROWS + hi_tenancy.ROWS}
DEV = re.compile(r"[ऀ-ॿ]")

path = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(HERE, sys.argv[1])
spec = importlib.util.spec_from_file_location("part", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
errs, per = [], collections.defaultdict(list)
for i, row in enumerate(m.EXTRA):
    if len(row) != 5: errs.append(f"row {i}: needs 5 fields (cid, type, score, en, hi)"); continue
    cid, t, s, en, hi = row
    per[cid].append(t)
    if cid not in EN: errs.append(f"{cid}: unknown clause id"); continue
    if t not in TYPES: errs.append(f"{cid}: bad type {t}"); continue
    lo, hi_ = TYPES[t]
    if not (isinstance(s, int) and lo <= s <= hi_): errs.append(f"{cid} {t}: score {s} outside {lo}-{hi_}")
    if t == EN[cid][5]: errs.append(f"{cid}: type {t} repeats the existing perturbation type")
    if DEV.search(en): errs.append(f"{cid} {t}: English text contains Devanagari")
    if not DEV.search(hi): errs.append(f"{cid} {t}: Hindi text has no Devanagari")
    if en.strip() in (EN[cid][2].strip(), EN[cid][4].strip()): errs.append(f"{cid} {t}: English identical to existing faithful/perturbed")
    if hi.strip() in (HI[cid][2].strip(), HI[cid][3].strip()): errs.append(f"{cid} {t}: Hindi identical to existing faithful/perturbed")
    if len(en) < 25 or len(hi) < 20: errs.append(f"{cid} {t}: text too short")
for cid, ts in per.items():
    if len(ts) != 2: errs.append(f"{cid}: needs exactly 2 rows, has {len(ts)}")
    elif ts[0] == ts[1]: errs.append(f"{cid}: both rows have type {ts[0]}")
print("rows:", len(m.EXTRA), "clauses:", len(per))
print("types:", dict(collections.Counter(r[1] for r in m.EXTRA)))
print("\n".join(errs) if errs else "OK - no problems")
