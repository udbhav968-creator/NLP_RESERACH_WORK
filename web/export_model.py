"""Train LegalDiff-GBR on all EnHi-LMP pairs (+ augmentation) and export trees, lexicons and test vectors as JSON."""
import sys, json, os
ROOT = "."; sys.path.insert(0, ROOT + "/src")
import numpy as np
from lmp_models import LegalFeatureRegressor, augment
import legal_features as LF
L = lambda n: [json.loads(l) for l in open(f"{ROOT}/data/{n}", encoding="utf-8")]
D = L("enhi_lmp.jsonl")
m = LegalFeatureRegressor(seed=0).fit([(r["original"], r["simplification"]) for r in D], [float(r["score"]) for r in D])
g = m.m
trees = []
for est in g.estimators_[:, 0]:
    t = est.tree_
    trees.append(dict(f=t.feature.tolist(), t=t.threshold.tolist(), l=t.children_left.tolist(), r=t.children_right.tolist(),
                      v=[float(x) for x in t.value[:, 0, 0]]))
init = float(g.init_.constant_[0][0]) if hasattr(g.init_, "constant_") else float(g._raw_predict_init(np.zeros((1, 19)))[0][0])
model = dict(init=init, lr=g.learning_rate, trees=trees, features=LF.FEATURE_NAMES, n_train=len(D))
lex = dict(NUM_WORDS=LF.NUM_WORDS, TIME_UNITS=LF.TIME_UNITS, UNIT_CANON=LF.UNIT_CANON, MULT=LF.MULT, ELISIONS=sorted(LF.ELISIONS),
           LEX=LF.LEX, ROLES=LF.ROLES)
json.dump(dict(model=model, lex=lex), open("web/model.json", "w", encoding="utf-8"), ensure_ascii=False)
# test vectors
tests = []
pairs = [(r["original"], r["simplification"]) for r in D + L("sanity_identical.jsonl") + L("sanity_unrelated.jsonl") + L("frjudge_test.jsonl")]
pairs += [("The borrower shall repay the loan in twelve equal monthly instalments.", "The borrower may pay back the loan in 24 monthly payments."),
          ("Rs. 15,00,000 shall be paid within 30 days.", "15 lakh rupees must be paid within one month."),
          ("The tenant's deposit of ₹2 lakh can't be withheld.", "The tenant’s deposit of 2,00,000 cannot be held back.")]
X = np.array([LF.features(o, s)[0] for o, s in pairs]); P = m.predict(pairs)
for (o, s), x, p in zip(pairs, X, P):
    et, why = LF.explain(o, s, float(p))
    tests.append(dict(o=o, s=s, x=x.tolist(), p=float(p), et=et, why=why, lang=LF.detect_lang(o)))
json.dump(tests, open("web/tests.json", "w", encoding="utf-8"), ensure_ascii=False)
print("init", init, "trees", len(trees), "tests", len(tests))
