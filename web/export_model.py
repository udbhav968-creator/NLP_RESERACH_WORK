"""Export the API's LegalDiff-GBR model (api/lmp_service.py) to web/model.json for the in-browser checker,
plus web/tests.json: features, scores and explanations for 1,053 pairs that web/test.js must reproduce exactly.
Run from the repository root:  python web/export_model.py && node web/test.js"""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
import numpy as np
from api.lmp_service import LMPService, LF

svc = LMPService(); g = svc.model
trees = [dict(f=e.tree_.feature.tolist(), t=e.tree_.threshold.tolist(), l=e.tree_.children_left.tolist(), r=e.tree_.children_right.tolist(),
              v=[float(x) for x in e.tree_.value[:, 0, 0]]) for e in g.estimators_[:, 0]]
model = dict(init=float(g.init_.constant_[0][0]), lr=g.learning_rate, trees=trees, features=LF.FEATURE_NAMES, n_train=svc.meta["n_train"])
lex = dict(NUM_WORDS=LF.NUM_WORDS, TIME_UNITS=LF.TIME_UNITS, UNIT_CANON=LF.UNIT_CANON, MULT=LF.MULT, ELISIONS=sorted(LF.ELISIONS), LEX=LF.LEX, ROLES=LF.ROLES)
json.dump(dict(model=model, lex=lex), open(R / "web" / "model.json", "w", encoding="utf-8"), ensure_ascii=False)

L = lambda n: [json.loads(l) for l in open(R / "data" / n, encoding="utf-8")]
pairs = [(r["original"], r["simplification"]) for r in L("enhi_lmp.jsonl") + L("sanity_identical.jsonl") + L("sanity_unrelated.jsonl") + L("frjudge_test.jsonl")]
pairs += [("The borrower shall repay the loan in twelve equal monthly instalments.", "The borrower may pay back the loan in 24 monthly payments."),
          ("Rs. 15,00,000 shall be paid within 30 days.", "15 lakh rupees must be paid within one month."),
          ("The tenant's deposit of ₹2 lakh can't be withheld.", "The tenant’s deposit of 2,00,000 cannot be held back.")]
X = np.array([LF.features(o, s)[0] for o, s in pairs]); P = np.clip(g.predict(X), 1, 10)
tests = []
for (o, s), x, p in zip(pairs, X, P):
    et, why = LF.explain(o, s, float(p))
    tests.append(dict(o=o, s=s, x=x.tolist(), p=float(p), et=et, why=why, lang=LF.detect_lang(o)))
json.dump(tests, open(R / "web" / "tests.json", "w", encoding="utf-8"), ensure_ascii=False)
print("trees", len(trees), "tests", len(tests))
