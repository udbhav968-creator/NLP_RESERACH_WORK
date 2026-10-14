"""Interactive demo: score any original/simplified legal sentence pair.
Trains LegalDiff-GBR on all EnHi-LMP pairs (+ augmentation) and prints score, decision, error type and explanation.
Usage:  python src/demo.py                       # runs the built-in examples
        python src/demo.py "original" "simplified"
"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from lmp_models import LegalFeatureRegressor
from legal_features import explain

def decision(s): return "Preserved" if s >= 7.5 else ("Partially Preserved" if s >= 4.5 else "Not Preserved")

rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", os.environ.get("LMP_DATA", "enhi_lmp.jsonl")), encoding="utf-8")]
model = LegalFeatureRegressor(seed=0).fit([(r["original"], r["simplification"]) for r in rows], [float(r["score"]) for r in rows])

EXAMPLES = [
    ("The borrower shall repay the loan in twelve equal monthly instalments.",
     "The borrower must pay back the loan in 12 equal monthly payments."),
    ("The borrower shall repay the loan in twelve equal monthly instalments.",
     "The borrower may pay back the loan in 24 monthly payments."),
    ("The lessee shall not keep pets in the flat without the written permission of the lessor.",
     "The lessee can keep pets in the flat."),
]
pairs = [tuple(sys.argv[1:3])] if len(sys.argv) >= 3 else EXAMPLES
for i, (o, s) in enumerate(pairs, 1):
    score = float(model.predict([(o, s)])[0])
    etype, why = explain(o, s, score)
    print(f"--- Pair {i} ---")
    print(f"Original      : {o}")
    print(f"Simplified    : {s}")
    print(f"LMP score     : {score:.1f} / 10")
    print(f"Decision      : {decision(score)}")
    print(f"Error type    : {etype}")
    print(f"Explanation   : {why}\n")
