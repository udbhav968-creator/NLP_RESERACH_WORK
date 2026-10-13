"""Select >=15 legally difficult cases for qualitative error analysis (E5)."""
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, "results", "exp5_rows.json")))
EMB = "WordLlama cosine (semantic)"
# hard = error pairs that the generic embedding baseline scores too high (largest over-estimation first)
err = [r for r in rows if r["gold_type"] not in ("NONE",)]
err.sort(key=lambda r: -(r[EMB] - r["gold_score"]))
picked, seen = [], collections.Counter()
for r in err:
    key = (r["gold_type"], r["lang"])
    if seen[key] >= 1: continue
    picked.append(r); seen[key] += 1
    if len(picked) >= 16: break
# add 2 faithful paraphrases that baselines under-score
faith = sorted([r for r in rows if r["gold_type"] == "NONE"], key=lambda r: r["chrF (lexical)"])[:2]
picked += faith
json.dump(picked, open(os.path.join(ROOT, "results", "exp5_cases.json"), "w"), ensure_ascii=False, indent=1)
for r in picked:
    print(r["id"], r["gold_type"], r["gold_score"], round(r[EMB], 1), round(r["gbr"], 1), round(r["pred_score"], 1), r["pred_type"])
