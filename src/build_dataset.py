"""Assemble the EN-HI Legal Meaning Preservation (EnHi-LMP) dataset + sanity holdouts + FrJUDGE splits."""
import json, random, sys, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "data"))
import en_insurance, en_tenancy, hi_insurance, hi_tenancy

def decision(score):
    return "Preserved" if score >= 8 else ("Partially Preserved" if score >= 5 else "Not Preserved")

pairs = []
for en_mod, hi_mod, domain in [(en_insurance, hi_insurance, "insurance"), (en_tenancy, hi_tenancy, "tenancy")]:
    hi_map = {r[0]: r for r in hi_mod.ROWS}
    assert len(en_mod.ROWS) == 40 and len(hi_map) == 40
    for (cid, o, f, fs, p, pt, ps) in en_mod.ROWS:
        _, oh, fh, ph = hi_map[cid]
        for lang, (oo, ff, pp) in [("en", (o, f, p)), ("hi", (oh, fh, ph))]:
            pairs.append(dict(id=f"{cid}-{lang}-F", clause=cid, lang=lang, domain=domain, original=oo,
                              simplification=ff, score=fs, error_type="NONE", decision=decision(fs)))
            pairs.append(dict(id=f"{cid}-{lang}-P", clause=cid, lang=lang, domain=domain, original=oo,
                              simplification=pp, score=ps, error_type=pt, decision=decision(ps)))

os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

# Sanity holdouts (never used for training): identical -> 10, unrelated -> 1
rng = random.Random(13)
originals = collections.OrderedDict()
for r in pairs: originals[(r["clause"], r["lang"])] = r
ident, unrel = [], []
keys = list(originals)
for (cid, lang), r in originals.items():
    ident.append(dict(id=f"{cid}-{lang}-ID", clause=cid, lang=lang, domain=r["domain"], original=r["original"], simplification=r["original"], score=10))
    other_dom = [k for k in keys if k[1] == lang and originals[k]["domain"] != r["domain"]]
    k = rng.choice(other_dom)
    unrel.append(dict(id=f"{cid}-{lang}-UN", clause=cid, lang=lang, domain=r["domain"], original=r["original"], simplification=originals[k]["simplification"] if "simplification" in originals[k] else originals[k]["original"], score=1))
for name, rows in [("sanity_identical", ident), ("sanity_unrelated", unrel)]:
    with open(os.path.join(ROOT, "data", name + ".jsonl"), "w", encoding="utf-8") as fh:
        for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")

# v2 extension: two more single-error simplifications per clause (EN + parallel HI), ids <clause>-<lang>-P2 / -P3.
# Added after the sanity sets are built, so the sanity pairs are unchanged.
sys.path.insert(0, os.path.join(ROOT, "data", "extra"))
import importlib
dom = {r["clause"]: r["domain"] for r in pairs}
orig = {(r["clause"], r["lang"]): r["original"] for r in pairs}
seen = collections.Counter()
for part in ["part_ins_a", "part_ins_b", "part_ten_a", "part_ten_b"]:
    for (cid, et, sc, en, hi) in importlib.import_module(part).EXTRA:
        seen[cid] += 1; k = seen[cid] + 1                      # P2, P3
        for lang, txt in [("en", en), ("hi", hi)]:
            pairs.append(dict(id=f"{cid}-{lang}-P{k}", clause=cid, lang=lang, domain=dom[cid], original=orig[(cid, lang)],
                              simplification=txt, score=sc, error_type=et, decision=decision(sc)))
with open(os.path.join(ROOT, "data", "enhi_lmp.jsonl"), "w", encoding="utf-8") as fh:
    for r in pairs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")

# FrJUDGE (Beauchemin et al., 2025; CC-BY-NC-SA 4.0) official splits — real human LMP labels (mean of 5 annotators)
src = "/tmp/ext/JUDGEBERT/datastore/training"   # clone of github.com/GRAAL-Research/JUDGEBERT; skipped if absent
for split in (["train", "dev", "test"] if os.path.isdir(src) else []):
    rows = [json.loads(l) for l in open(os.path.join(src, f"{split}_FrJUDGE.jsonl"), encoding="utf-8")]
    with open(os.path.join(ROOT, "data", f"frjudge_{split}.jsonl"), "w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            fh.write(json.dumps(dict(id=f"FR-{split}-{i}", lang="fr", domain="insurance", original=r["original"],
                                     simplification=r["simplification"], score=float(r["label"])), ensure_ascii=False) + "\n")

c = collections.Counter((r["lang"], r["domain"]) for r in pairs)
print("pairs:", len(pairs), dict(c))
print("decisions:", collections.Counter(r["decision"] for r in pairs))
print("error types:", collections.Counter(r["error_type"] for r in pairs))
print("sanity:", len(ident), len(unrel))
