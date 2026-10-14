"""ML-JudgeBERT with a PRETRAINED multilingual encoder (XLM-R / MuRIL / mBERT) — run on a GPU (e.g. Google Colab T4).

Same protocol as run_experiments.py exp1: 5-fold CV grouped by clause, JUDGEBERT data augmentation
(identical -> 10, unrelated -> 1), MSE regression on the 1-10 LMP scale, metrics r / rho / RMSE / MAE / decision F1,
plus late fusion with LegalDiff-GBR. 20% of the training clauses of every fold are held out as a validation set,
used (a) to keep the best epoch and (b) to choose the fusion weight, so nothing is tuned on data the models were fitted to.

Examples
  python src/finetune_pretrained.py --model xlm-roberta-base
  python src/finetune_pretrained.py --model google/muril-base-cased --epochs 6
  LMP_DATA=enhi_lmp_human.jsonl python src/finetune_pretrained.py --model xlm-roberta-base   # after human annotation
"""
import argparse, json, os, random, sys, time
import numpy as np, torch
from torch.utils.data import DataLoader
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import f1_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from lmp_models import LegalFeatureRegressor, augment

def load(name): return [json.loads(l) for l in open(os.path.join(ROOT, "data", name), encoding="utf-8")]

def dec(s): s = np.asarray(s); return np.where(s >= 7.5, 2, np.where(s >= 4.5, 1, 0))
def corr(f, p, g):
    return 0.0 if np.std(p) < 1e-9 or np.std(g) < 1e-9 else float(f(p, g)[0])   # constant predictions -> 0, not NaN
def metrics(p, g):
    p, g = np.asarray(p, float), np.asarray(g, float)
    return dict(pearson=corr(pearsonr, p, g), spearman=corr(spearmanr, p, g), rmse=float(np.sqrt(np.mean((p - g) ** 2))),
                mae=float(np.mean(np.abs(p - g))), f1_decision=float(f1_score(dec(g), dec(p), average="macro")),
                f1_notpreserved=float(f1_score(g < 4.5, p < 4.5)))

def folds(data, k=5, seed=7):
    cl = sorted(set(r["clause"] for r in data)); rng = random.Random(seed); rng.shuffle(cl)
    return [set(cl[i::k]) for i in range(k)]

class Reg:
    def __init__(self, name, epochs, lr, bs, max_len, seed, device):
        self.name, self.epochs, self.lr, self.bs, self.max_len, self.seed, self.device = name, epochs, lr, bs, max_len, seed, device
    def _batches(self, pairs, y=None, shuffle=False):
        idx = list(range(len(pairs)))
        if shuffle: random.shuffle(idx)
        for i in range(0, len(idx), self.bs):
            b = idx[i:i + self.bs]
            enc = self.tok([pairs[j][0] for j in b], [pairs[j][1] for j in b], truncation=True, max_length=self.max_len, padding=True, return_tensors="pt")
            enc = {k: v.to(self.device) for k, v in enc.items()}
            yield enc, (torch.tensor([y[j] for j in b], dtype=torch.float32, device=self.device) if y is not None else None)
    def fit(self, pairs, y, val_pairs=None, val_y=None):
        random.seed(self.seed); np.random.seed(self.seed); torch.manual_seed(self.seed)
        self.tok = AutoTokenizer.from_pretrained(self.name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.name, num_labels=1).to(self.device)
        yn = [(v - 1) / 9 for v in y]                       # scale to [0,1]
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=0.01)
        steps = self.epochs * ((len(pairs) + self.bs - 1) // self.bs)
        sch = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
        best, self.best_epoch, state = float("inf"), self.epochs, None
        for ep in range(self.epochs):
            self.model.train()
            for enc, yt in self._batches(pairs, yn, shuffle=True):
                out = torch.sigmoid(self.model(**enc).logits.squeeze(-1))
                loss = torch.nn.functional.mse_loss(out, yt)
                opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0); opt.step(); sch.step()
            if val_pairs:                                     # keep the epoch with the lowest validation MSE
                mse = float(np.mean((self.predict(val_pairs) - np.asarray(val_y)) ** 2))
                if mse < best:
                    best, self.best_epoch = mse, ep + 1
                    state = {k: v.detach().to("cpu", copy=True) for k, v in self.model.state_dict().items()}
        if state is not None: self.model.load_state_dict(state)
        return self
    @torch.no_grad()
    def predict(self, pairs):
        self.model.eval(); out = []
        for enc, _ in self._batches(pairs):
            out.extend((1 + 9 * torch.sigmoid(self.model(**enc).logits.squeeze(-1))).float().cpu().tolist())
        return np.array(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="xlm-roberta-base"); ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--max_len", type=int, default=256); ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--folds", type=int, default=5); ap.add_argument("--limit_folds", type=int, default=0)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    data = load(os.environ.get("LMP_DATA", "enhi_lmp.jsonl")); ident = load("sanity_identical.jsonl"); unrel = load("sanity_unrelated.jsonl")
    P = lambda rs: [(r["original"], r["simplification"]) for r in rs]; Y = lambda rs: [float(r["score"]) for r in rs]
    preds = {s: {} for s in a.seeds}; fused = {s: {} for s in a.seeds}
    for fi, test_cl in enumerate(folds(data, a.folds)):
        if a.limit_folds and fi >= a.limit_folds: break
        tr = [r for r in data if r["clause"] not in test_cl]; te = [r for r in data if r["clause"] in test_cl]
        san = [r for r in ident + unrel if r["clause"] in test_cl]
        tr_cl = sorted(set(r["clause"] for r in tr)); random.Random(100 + fi).shuffle(tr_cl)
        val_cl = set(tr_cl[: max(1, len(tr_cl) // 5)])           # inner validation clauses (en/hi twins stay together)
        itr = [r for r in tr if r["clause"] not in val_cl]; val = [r for r in tr if r["clause"] in val_cl]
        trp, try_ = augment(P(itr), Y(itr), seed=fi)
        gbr_in = LegalFeatureRegressor(seed=0).fit(P(itr), Y(itr))  # for choosing the fusion weight on unseen clauses
        gbr = LegalFeatureRegressor(seed=0).fit(P(tr), Y(tr))       # final GBR uses the whole training fold
        g_val, g_te, g_san = gbr_in.predict(P(val)), gbr.predict(P(te)), gbr.predict(P(san))
        for s in a.seeds:
            t0 = time.time(); m = Reg(a.model, a.epochs, a.lr, a.bs, a.max_len, s, device).fit(trp, try_, P(val), Y(val))
            p_te, p_san, p_val = m.predict(P(te)), m.predict(P(san)), m.predict(P(val))
            ws = np.linspace(0, 1, 11)
            w = ws[int(np.argmin([np.mean((w_ * p_val + (1 - w_) * g_val - np.array(Y(val))) ** 2) for w_ in ws]))]
            for r, v, g in zip(te + san, list(p_te) + list(p_san), list(g_te) + list(g_san)):
                preds[s][r["id"]] = float(v); fused[s][r["id"]] = float(w * v + (1 - w) * g)
            print(f"fold {fi} seed {s}: {time.time()-t0:.0f}s, best epoch={m.best_epoch}, fusion weight={w:.1f}", flush=True)
            del m; torch.cuda.empty_cache() if device == "cuda" else None
    ids = [r["id"] for r in data if r["id"] in preds[a.seeds[0]]]
    gold = {r["id"]: r["score"] for r in data}
    res = {}
    for name, P_ in [(a.model, preds), (a.model + " + LegalDiff (late fusion)", fused)]:
        ms = [metrics([P_[s][i] for i in ids], [gold[i] for i in ids]) for s in a.seeds]
        res[name] = {k: (float(np.mean([m[k] for m in ms])), float(np.std([m[k] for m in ms]))) for k in ms[0]}
        for lang in ["en", "hi"]:
            li = [i for i in ids if f"-{lang}-" in i]
            res[name]["pearson_" + lang] = float(np.mean([corr(pearsonr, np.array([P_[s][i] for i in li]), np.array([gold[i] for i in li], float)) for s in a.seeds]))
        idn = [r["id"] for r in ident if r["id"] in P_[a.seeds[0]]]; unr = [r["id"] for r in unrel if r["id"] in P_[a.seeds[0]]]
        res[name]["identical_mean"] = float(np.mean([P_[s][i] for s in a.seeds for i in idn]))
        res[name]["unrelated_mean"] = float(np.mean([P_[s][i] for s in a.seeds for i in unr]))
    tag = a.model.replace("/", "_") + ("" if os.environ.get("LMP_DATA", "enhi_lmp.jsonl") == "enhi_lmp.jsonl" else "_human")
    json.dump(res, open(os.path.join(ROOT, "results", f"pretrained_{tag}.json"), "w"), indent=1)
    json.dump({"gold": {i: gold.get(i) for i in preds[a.seeds[0]]},
               "pred": {i: float(np.mean([preds[s][i] for s in a.seeds])) for i in preds[a.seeds[0]]},
               "fused": {i: float(np.mean([fused[s][i] for s in a.seeds])) for i in preds[a.seeds[0]]}},
              open(os.path.join(ROOT, "results", f"pretrained_{tag}_predictions.json"), "w"), indent=0)
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
