"""Model service: LegalDiff features + LegalDiff-GBR scorer + rule-based explainer.

Pure scikit-learn (no torch), so the API image stays small. Training reproduces
src/lmp_models.LegalFeatureRegressor exactly (same augmentation, seed and hyper-parameters),
so the API, the web checker (web/lmp.js) and the experiments all score a pair identically.
"""
from __future__ import annotations
import json, os, random, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import legal_features as LF  # noqa: E402

MODEL_PATH = Path(os.environ.get("LMP_MODEL", ROOT / "api" / "model.joblib"))
DATA_PATH = ROOT / "data" / "enhi_lmp.jsonl"
TYPE_LABELS = {"NONE": "No legal change found", "NEGATION": "Negation reversed", "MODALITY": "Obligation / permission changed",
               "NUMBER": "Amount or number changed", "DATE": "Time limit changed", "OMIT_COND": "Condition dropped",
               "EXC_REMOVED": "Exception removed", "SCOPE": "Scope changed", "ENTITY": "Wrong party", "HALLUC": "Content added",
               "MINOR": "Minor detail omitted"}


def decision(score: float) -> str:
    return "Preserved" if score >= 7.5 else ("Partially preserved" if score >= 4.5 else "Not preserved")


def augment(pairs, y, seed):
    """JUDGEBERT augmentation, identical to src/lmp_models.augment: identical pair -> 10, unrelated pair -> 1."""
    pairs, y = list(pairs), list(map(float, y)); rng = random.Random(seed)
    simps = [s for _, s in pairs]
    for o in sorted(set(o for o, _ in pairs)):
        own = {s for oo, s in pairs if oo == o}
        pairs.append((o, o)); y.append(10.0)
        cand = rng.choice(simps)
        while cand in own: cand = rng.choice(simps)
        pairs.append((o, cand)); y.append(1.0)
    return pairs, y


def train(data_path: Path = DATA_PATH, out: Path = MODEL_PATH, seed: int = 0) -> dict:
    from sklearn.ensemble import GradientBoostingRegressor
    import joblib
    rows = [json.loads(l) for l in open(data_path, encoding="utf-8")]
    pairs, y = augment([(r["original"], r["simplification"]) for r in rows], [r["score"] for r in rows], seed)
    X = np.array([LF.features(o, s)[0] for o, s in pairs])
    m = GradientBoostingRegressor(random_state=seed, n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8).fit(X, y)
    meta = dict(model="LegalDiff-GBR", n_train=len(rows), n_trees=200, max_depth=3, features=LF.FEATURE_NAMES, seed=seed)
    joblib.dump({"model": m, "meta": meta}, out)
    return meta


class LMPService:
    def __init__(self, path: Path = MODEL_PATH):
        import joblib
        if not Path(path).exists():
            train(out=Path(path))
        blob = joblib.load(path)
        self.model, self.meta = blob["model"], blob["meta"]
        stats = ROOT / "web" / "stats640.json"
        self.meta["cv"] = json.load(open(stats)) if stats.exists() else None

    def score_many(self, pairs: list[tuple[str, str]]) -> list[dict]:
        feats = [LF.features(o, s) for o, s in pairs]
        preds = np.clip(self.model.predict(np.array([f[0] for f in feats])), 1, 10) if feats else []
        out = []
        for (o, s), (_, f, lang), p in zip(pairs, feats, preds):
            p = float(p); et, why = LF.explain(o, s, p, lang)
            out.append(dict(score=round(p, 4), decision=decision(p), error_type=et, error_label=TYPE_LABELS[et],
                            explanation=why, lang=lang, features={k: float(v) for k, v in f.items()}))
        return out

    def score(self, original: str, simplification: str) -> dict:
        return self.score_many([(original, simplification)])[0]


if __name__ == "__main__":
    print(train())
