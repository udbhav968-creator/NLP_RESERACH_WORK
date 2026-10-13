"""Runs Experiments 1-5. Usage: python src/run_experiments.py <exp> ; results -> results/*.json"""
import sys, os, json, time, random, collections
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import torch
torch.set_num_threads(int(os.environ.get("THREADS", "1")))
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import f1_score
from lmp_models import BASELINES, LinearCalibrator, MLJudgeBERT, LegalFeatureRegressor
from legal_features import explain

def load(name):
    return [json.loads(l) for l in open(os.path.join(ROOT, "data", name), encoding="utf-8")]
DATA = load(os.environ.get("LMP_DATA", "enhi_lmp.jsonl")); IDENT = load("sanity_identical.jsonl"); UNREL = load("sanity_unrelated.jsonl")
P = lambda rs: [(r["original"], r["simplification"]) for r in rs]
Y = lambda rs: np.array([float(r["score"]) for r in rs])
SEEDS = [0, 1, 2]
EPOCHS = int(os.environ.get("EPOCHS", "40"))

def dec(s):
    s = np.asarray(s); return np.where(s >= 7.5, 2, np.where(s >= 4.5, 1, 0))
def metrics(pred, gold):
    pred, gold = np.asarray(pred, float), np.asarray(gold, float)
    return dict(pearson=float(pearsonr(pred, gold)[0]), spearman=float(spearmanr(pred, gold)[0]),
                rmse=float(np.sqrt(np.mean((pred - gold) ** 2))), mae=float(np.mean(np.abs(pred - gold))),
                f1_decision=float(f1_score(dec(gold), dec(pred), average="macro")),
                f1_notpreserved=float(f1_score(gold < 4.5, pred < 4.5)), n=int(len(gold)))

def make(name, seed, da=True):
    if name == "LegalDiff-GBR": return LegalFeatureRegressor(seed=seed, data_augmentation=da)
    if name == "ML-JudgeBERT": return MLJudgeBERT(use_features=False, seed=seed, epochs=EPOCHS, data_augmentation=da, embed="bpe", max_len=192)
    if name == "ML-JudgeBERT+LegalDiff": return MLJudgeBERT(use_features=True, seed=seed, epochs=EPOCHS, data_augmentation=da, embed="bpe", max_len=192)
    raise KeyError(name)
LEARNED = ["LegalDiff-GBR", "ML-JudgeBERT", "ML-JudgeBERT+LegalDiff"]

def run_baselines(train, tests):
    out = {}
    for b, fn in BASELINES.items():
        cal = LinearCalibrator().fit([fn(o, s) for o, s in P(train)], Y(train))
        out[b] = [cal.predict([fn(o, s) for o, s in P(t)]) for t in tests]
    return out

def run_learned(name, train, tests, seeds=SEEDS, da=True):
    preds = []
    for sd in seeds:
        t0 = time.time(); m = make(name, sd, da).fit(P(train), Y(train), None)
        preds.append([m.predict(P(t)) for t in tests]); print(f"   {name} seed={sd} ({time.time()-t0:.0f}s)", flush=True)
    return preds  # [seed][test_idx] -> array

def save(name, obj):
    with open(os.path.join(ROOT, "results", name + ".json"), "w") as fh: json.dump(obj, fh, indent=1, default=float)

def folds(k=5, seed=7):
    clauses = sorted(set(r["clause"] for r in DATA)); rng = random.Random(seed); rng.shuffle(clauses)
    return [set(clauses[i::k]) for i in range(k)]

# ---------------------------------------------------------------- Experiment 1 (+4 sanity, +5 qualitative inputs)
def exp1():
    rows_pred = {r["id"]: {"gold": r["score"]} for r in DATA + IDENT + UNREL}
    per_seed = collections.defaultdict(lambda: collections.defaultdict(dict))  # model -> seed -> id -> pred
    for fi, test_cl in enumerate(folds()):
        train = [r for r in DATA if r["clause"] not in test_cl]
        tests = [[r for r in DATA if r["clause"] in test_cl], [r for r in IDENT if r["clause"] in test_cl], [r for r in UNREL if r["clause"] in test_cl]]
        print(f"fold {fi}: train={len(train)} test={len(tests[0])}", flush=True)
        for b, pr in run_baselines(train, tests).items():
            for t, p in zip(tests, pr):
                for r, v in zip(t, p): per_seed[b][0][r["id"]] = float(v)
        for name in LEARNED:
            for sd, pr in zip(SEEDS, run_learned(name, train, tests)):
                for t, p in zip(tests, pr):
                    for r, v in zip(t, p): per_seed[name][sd][r["id"]] = float(v)
        # sanity ablation: hybrid without data augmentation (1 seed)
        for sd, pr in zip([0], run_learned("ML-JudgeBERT+LegalDiff", train, tests, seeds=[0], da=False)):
            for t, p in zip(tests, pr):
                for r, v in zip(t, p): per_seed["ML-JudgeBERT+LegalDiff (no DA)"][sd][r["id"]] = float(v)
        save("exp1_raw", {m: {str(s): d for s, d in v.items()} for m, v in per_seed.items()})
    summarize_exp1()

def summarize_exp1():
    raw = json.load(open(os.path.join(ROOT, "results", "exp1_raw.json")))
    out = {"overall": {}, "by_lang": {}, "by_domain": {}, "by_lang_domain": {}, "sanity": {}, "by_error_type": {}}
    subsets = {"overall": {"all": DATA}, "by_lang": {l: [r for r in DATA if r["lang"] == l] for l in ["en", "hi"]},
               "by_domain": {d: [r for r in DATA if r["domain"] == d] for d in ["insurance", "tenancy"]},
               "by_lang_domain": {f"{l}-{d}": [r for r in DATA if r["lang"] == l and r["domain"] == d] for l in ["en", "hi"] for d in ["insurance", "tenancy"]}}
    for model, seeds in raw.items():
        for key, groups in subsets.items():
            out[key][model] = {}
            for g, rs in groups.items():
                ms = [metrics([seeds[s][r["id"]] for r in rs], [r["score"] for r in rs]) for s in seeds]
                out[key][model][g] = {k: (float(np.mean([m[k] for m in ms])), float(np.std([m[k] for m in ms]))) for k in ms[0]}
        sid = list(seeds)
        ip = np.array([[seeds[s][r["id"]] for r in IDENT] for s in sid]).mean(0)
        up = np.array([[seeds[s][r["id"]] for r in UNREL] for s in sid]).mean(0)
        out["sanity"][model] = dict(identical_mean=float(ip.mean()), identical_ge9=float((ip >= 9).mean()),
                                    unrelated_mean=float(up.mean()), unrelated_le2=float((up <= 2).mean()),
                                    identical_by_lang={l: float(np.mean([p for p, r in zip(ip, IDENT) if r["lang"] == l])) for l in ["en", "hi"]},
                                    unrelated_by_lang={l: float(np.mean([p for p, r in zip(up, UNREL) if r["lang"] == l])) for l in ["en", "hi"]})
        mean_pred = {r["id"]: float(np.mean([seeds[s][r["id"]] for s in sid])) for r in DATA}
        et = collections.defaultdict(list)
        for r in DATA: et[r["error_type"]].append((mean_pred[r["id"]], r["score"]))
        out["by_error_type"][model] = {k: dict(pred=float(np.mean([a for a, _ in v])), gold=float(np.mean([b for _, b in v])), n=len(v)) for k, v in et.items()}
    save("exp1_summary", out)
    print(json.dumps(out["overall"], indent=1)[:3000])

# ---------------------------------------------------------------- Experiment 2: cross-lingual transfer
def exp2():
    clauses = sorted(set(r["clause"] for r in DATA)); halves = [set(clauses[0::2]), set(clauses[1::2])]
    res = collections.defaultdict(dict)
    for src in ["en", "hi"]:
        for tgt in ["en", "hi"]:
            preds = collections.defaultdict(lambda: collections.defaultdict(dict))
            for h in range(2):
                train = [r for r in DATA if r["lang"] == src and r["clause"] in halves[h]]
                test = [r for r in DATA if r["lang"] == tgt and r["clause"] in halves[1 - h]]
                print(f"exp2 {src}->{tgt} half {h}: {len(train)}->{len(test)}", flush=True)
                for b, pr in run_baselines(train, [test]).items():
                    for r, v in zip(test, pr[0]): preds[b][0][r["id"]] = float(v)
                for name in LEARNED:
                    for sd, pr in zip(SEEDS[:2], run_learned(name, train, [test], seeds=SEEDS[:2])):
                        for r, v in zip(test, pr[0]): preds[name][sd][r["id"]] = float(v)
            test_all = [r for r in DATA if r["lang"] == tgt]
            for m, sd in preds.items():
                ms = [metrics([sd[s][r["id"]] for r in test_all], [r["score"] for r in test_all]) for s in sd]
                res[f"{src}->{tgt}"][m] = {k: (float(np.mean([x[k] for x in ms])), float(np.std([x[k] for x in ms]))) for k in ms[0]}
            save("exp2_crosslingual", res)

# ---------------------------------------------------------------- Experiment 3: domain + FrJUDGE out-of-language
def exp3():
    res = collections.defaultdict(dict)
    for src, tgt in [("insurance", "tenancy"), ("tenancy", "insurance")]:
        train = [r for r in DATA if r["domain"] == src]; test = [r for r in DATA if r["domain"] == tgt]
        print(f"exp3 {src}->{tgt}", flush=True)
        for b, pr in run_baselines(train, [test]).items(): res[f"{src}->{tgt}"][b] = {k: (v, 0.0) for k, v in metrics(pr[0], Y(test)).items()}
        for name in LEARNED:
            ms = [metrics(p[0], Y(test)) for p in run_learned(name, train, [test], seeds=SEEDS[:2])]
            res[f"{src}->{tgt}"][name] = {k: (float(np.mean([x[k] for x in ms])), float(np.std([x[k] for x in ms]))) for k in ms[0]}
        save("exp3_domain", res)
    fr_tr = load("frjudge_train.jsonl") + load("frjudge_dev.jsonl"); fr_te = load("frjudge_test.jsonl")
    for setting, train in [("EnHi->FrJUDGE (zero-shot)", DATA), ("FrJUDGE->FrJUDGE (in-language)", fr_tr)]:
        print("exp3", setting, flush=True)
        for b, pr in run_baselines(fr_tr if "in-language" in setting else DATA, [fr_te]).items():
            res[setting][b] = {k: (v, 0.0) for k, v in metrics(pr[0], Y(fr_te)).items()}
        for name in LEARNED:
            ms = [metrics(p[0], Y(fr_te)) for p in run_learned(name, train, [fr_te], seeds=SEEDS[:2])]
            res[setting][name] = {k: (float(np.mean([x[k] for x in ms])), float(np.std([x[k] for x in ms]))) for k in ms[0]}
        save("exp3_domain", res)

# ---------------------------------------------------------------- Experiment 5: explanations / error typing
def exp5():
    raw = json.load(open(os.path.join(ROOT, "results", "exp1_raw.json")))
    model = os.environ.get("EXPLAIN_MODEL", "LegalDiff-GBR")
    mp = {r["id"]: float(np.mean([raw[model][s][r["id"]] for s in raw[model]])) for r in DATA}
    gold, pred, rows = [], [], []
    for r in DATA:
        et, expl = explain(r["original"], r["simplification"], mp[r["id"]], r["lang"])
        gold.append(r["error_type"]); pred.append(et)
        rows.append(dict(id=r["id"], lang=r["lang"], domain=r["domain"], gold_score=r["score"], gold_type=r["error_type"],
                         pred_score=mp[r["id"]], pred_type=et, explanation=expl, original=r["original"], simplification=r["simplification"],
                         **{b: float(raw[b]["0"][r["id"]]) for b in BASELINES}, gbr=float(np.mean([raw["LegalDiff-GBR"][s][r["id"]] for s in raw["LegalDiff-GBR"]])),
                         text_only=float(np.mean([raw["ML-JudgeBERT"][s][r["id"]] for s in raw["ML-JudgeBERT"]])),
                         hybrid=float(np.mean([raw["ML-JudgeBERT+LegalDiff"][s][r["id"]] for s in raw["ML-JudgeBERT+LegalDiff"]]))))
    labels = sorted(set(gold))
    from sklearn.metrics import precision_recall_fscore_support, accuracy_score
    p, r_, f, s = precision_recall_fscore_support(gold, pred, labels=labels, zero_division=0)
    per = {l: dict(p=float(a), r=float(b), f1=float(c), n=int(d)) for l, a, b, c, d in zip(labels, p, r_, f, s)}
    bin_g = [g != "NONE" for g in gold]; bin_p = [x != "NONE" for x in pred]
    pb, rb, fb, _ = precision_recall_fscore_support(bin_g, bin_p, average="binary")
    err_only = [(g, x) for g, x in zip(gold, pred) if g != "NONE"]
    out = dict(per_type=per, macro_f1=float(np.mean([v["f1"] for v in per.values()])),
               accuracy=float(accuracy_score(gold, pred)), binary=dict(p=float(pb), r=float(rb), f1=float(fb)),
               type_acc_on_errors=float(np.mean([g == x for g, x in err_only])),
               type_acc_on_detected=float(np.mean([g == x for g, x in err_only if x != "NONE"])),
               n_detected=int(sum(1 for g, x in err_only if x != "NONE")), scoring_model=model,
               per_lang={l: float(np.mean([g == x for g, x, rr in zip(gold, pred, DATA) if rr["lang"] == l and g != "NONE"])) for l in ["en", "hi"]})
    save("exp5_explain", out); save("exp5_rows", rows)
    print(json.dumps({k: v for k, v in out.items() if k != "per_type"}, indent=1))

if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    {"exp1": exp1, "sum1": summarize_exp1, "exp2": exp2, "exp3": exp3, "exp5": exp5}[sys.argv[1]]()
