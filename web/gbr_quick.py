"""GBR-only replica of exp1/exp3/exp5 (same folds, seeds and metric code) for the live checker's model card."""
import sys, json, collections, numpy as np
sys.argv = ["x"]; sys.path.insert(0, "src")
import run_experiments as RE
from lmp_models import chrf, LinearCalibrator
from legal_features import explain
from sklearn.metrics import precision_recall_fscore_support
D, I, U = RE.DATA, RE.IDENT, RE.UNREL
per = collections.defaultdict(dict); chr_ = {}
for fi, tc in enumerate(RE.folds()):
    tr = [r for r in D if r["clause"] not in tc]; tests = [r for r in D + I + U if r["clause"] in tc]
    for sd in RE.SEEDS:
        m = RE.make("LegalDiff-GBR", sd).fit(RE.P(tr), RE.Y(tr), None)
        for r, v in zip(tests, m.predict(RE.P(tests))): per[sd][r["id"]] = float(v)
    cal = LinearCalibrator().fit([chrf(o, s) for o, s in RE.P(tr)], RE.Y(tr))
    for r, v in zip(tests, cal.predict([chrf(o, s) for o, s in RE.P(tests)])): chr_[r["id"]] = float(v)
def avg(rs, src): ms = [RE.metrics([src[s][r["id"]] for r in rs], [r["score"] for r in rs]) for s in src]; return {k: float(np.mean([m[k] for m in ms])) for k in ms[0]}
out = dict(all=avg(D, per), en=avg([r for r in D if r["lang"] == "en"], per), hi=avg([r for r in D if r["lang"] == "hi"], per),
           chrf=RE.metrics([chr_[r["id"]] for r in D], [r["score"] for r in D]))
ip = np.mean([[per[s][r["id"]] for r in I] for s in per], 0); up = np.mean([[per[s][r["id"]] for r in U] for s in per], 0)
out["sanity"] = dict(identical=float(ip.mean()), unrelated=float(up.mean()))
mp = {r["id"]: float(np.mean([per[s][r["id"]] for s in per])) for r in D}
gold = [r["error_type"] for r in D]; pred = [explain(r["original"], r["simplification"], mp[r["id"]], r["lang"])[0] for r in D]
_, _, fb, _ = precision_recall_fscore_support([g != "NONE" for g in gold], [x != "NONE" for x in pred], average="binary")
out["detect_f1"] = float(fb); out["type_acc"] = float(np.mean([g == x for g, x in zip(gold, pred) if g != "NONE"]))
fr_te = RE.load("frjudge_test.jsonl")
out["fr_zero_shot"] = float(np.mean([RE.metrics(RE.make("LegalDiff-GBR", s).fit(RE.P(D), RE.Y(D), None).predict(RE.P(fr_te)), RE.Y(fr_te))["pearson"] for s in RE.SEEDS[:2]]))
json.dump(out, open("web/stats640.json", "w"), indent=1)
print(json.dumps({k: (round(v, 3) if isinstance(v, float) else {a: round(b, 3) for a, b in v.items() if a in ("pearson", "rmse", "f1_notpreserved", "identical", "unrelated")}) for k, v in out.items()}))
