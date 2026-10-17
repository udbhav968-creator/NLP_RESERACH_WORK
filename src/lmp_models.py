"""Baselines (generic similarity) and ML-JudgeBERT (JUDGEBERT-inspired transformer cross-encoder regressor)."""
import math, random, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import sacrebleu
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, normalizers, decoders
from legal_features import features, FEATURE_NAMES

# ------------------------------------------------------------------ baselines
_WL = None
def wordllama():
    """Load WordLlama offline if its files are bundled, otherwise download them (needs internet once)."""
    global _WL
    if _WL is None:
        import shutil, wordllama as _wlpkg
        from pathlib import Path
        from wordllama import WordLlama
        pkg = Path(_wlpkg.__file__).parent
        src, dst = pkg / "tokenizers" / "l2_supercat_tokenizer_config.json", pkg / "tokenizer" / "l2_supercat_tokenizer_config.json"
        try:
            if src.exists() and not dst.exists():
                dst.parent.mkdir(exist_ok=True); shutil.copy(src, dst)
        except OSError:
            pass
        try:
            _WL = WordLlama.load(disable_download=True)
        except Exception:
            _WL = WordLlama.load()
    return _WL

def chrf(o, s):
    return sacrebleu.sentence_chrf(s, [o]).score / 100.0

def wl_cosine(o, s):
    return float(wordllama().similarity(o, s))

def wl_tokenscore(o, s):
    """BERTScore-style greedy-alignment F1 over WordLlama token embeddings (static, multilingual tokenizer)."""
    wl = wordllama()
    E = wl.embedding if isinstance(wl.embedding, np.ndarray) else np.asarray(wl.embedding)
    def emb(t):
        ids = [i for i in wl.tokenizer.encode(t).ids if i > 2]
        v = E[ids].astype(np.float32); v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-8); return v
    a, b = emb(o), emb(s)
    sim = a @ b.T
    r, p = sim.max(1).mean(), sim.max(0).mean()
    return float(2 * p * r / (p + r + 1e-8))

BASELINES = {"chrF (lexical)": chrf, "WordLlama cosine (semantic)": wl_cosine, "Token-alignment F1 (BERTScore-style)": wl_tokenscore}

class LinearCalibrator:
    """Maps a similarity in [0,1] to the 1-10 LMP scale, fitted on training folds only."""
    def fit(self, x, y):
        x, y = np.asarray(x), np.asarray(y)
        self.a, self.b = np.polyfit(x, y, 1) if np.std(x) > 1e-9 else (0.0, float(np.mean(y)))
        return self
    def predict(self, x):
        return np.clip(self.a * np.asarray(x) + self.b, 1, 10)

# ------------------------------------------------------------------ tokenizer
def train_tokenizer(texts, vocab_size=3000):
    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.normalizer = normalizers.Sequence([normalizers.NFKC(), normalizers.Lowercase()])
    tok.pre_tokenizer = pre_tokenizers.Sequence([pre_tokenizers.Metaspace(), pre_tokenizers.Digits(individual_digits=True)])
    tok.decoder = decoders.Metaspace()
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, min_frequency=2, special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]"],
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    tok.train_from_iterator(texts, trainer)
    return tok

# ------------------------------------------------------------------ model
class CrossEncoder(nn.Module):
    """[CLS] original [SEP] simplification [SEP] -> Transformer encoder -> CLS + pooled interaction (+ legal features) -> LMP."""
    def __init__(self, vocab, d=128, layers=2, heads=4, ff=256, max_len=192, n_feat=0, dropout=0.1):
        super().__init__()
        self.tok = nn.Embedding(vocab, d, padding_idx=0); self.pos = nn.Embedding(max_len, d); self.seg = nn.Embedding(2, d)
        enc = nn.TransformerEncoderLayer(d, heads, ff, dropout, batch_first=True, activation="gelu", norm_first=True)
        self.enc = nn.TransformerEncoder(enc, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.n_feat = n_feat
        self.head = nn.Sequential(nn.Linear(4 * d + n_feat, 128), nn.GELU(), nn.Dropout(dropout), nn.Linear(128, 1))
    def forward(self, ids, seg, mask, feats=None):
        pos = torch.arange(ids.size(1), device=ids.device).unsqueeze(0)
        h = self.tok(ids) + self.pos(pos) + self.seg(seg)
        h = self.norm(self.enc(h, src_key_padding_mask=~mask))
        cls = h[:, 0]
        m0 = (mask & (seg == 0)).unsqueeze(-1).float(); m1 = (mask & (seg == 1)).unsqueeze(-1).float()
        u = (h * m0).sum(1) / m0.sum(1).clamp(min=1); v = (h * m1).sum(1) / m1.sum(1).clamp(min=1)
        z = [cls, u - v, u * v, (u - v).abs()]
        if self.n_feat: z.append(feats)
        return 1 + 9 * torch.sigmoid(self.head(torch.cat(z, -1)).squeeze(-1))

def encode(tok, o, s, max_len=192):
    a = tok.encode(o).ids[: (max_len - 3) // 2 + 20]; b = tok.encode(s).ids
    cls, sep = tok.token_to_id("[CLS]"), tok.token_to_id("[SEP]")
    ids = [cls] + a + [sep]; seg = [0] * len(ids)
    rest = max_len - len(ids) - 1
    ids += b[:rest] + [sep]; seg += [1] * (len(b[:rest]) + 1)
    return ids, seg

def batchify(enc_list, feats=None):
    L = max(len(i) for i, _ in enc_list)
    ids = torch.zeros(len(enc_list), L, dtype=torch.long); seg = torch.zeros_like(ids); mask = torch.zeros(len(enc_list), L, dtype=torch.bool)
    for k, (i, s) in enumerate(enc_list):
        ids[k, :len(i)] = torch.tensor(i); seg[k, :len(s)] = torch.tensor(s); mask[k, :len(i)] = True
    f = torch.tensor(np.asarray(feats), dtype=torch.float32) if feats is not None else None
    return ids, seg, mask, f

class _Enc:
    def __init__(self, ids): self.ids = ids

class WordLlamaTokenizer:
    """Llama-2 SentencePiece tokenizer shipped with WordLlama; embeddings are distilled Llama-2 token vectors (256-d)."""
    def __init__(self):
        self.wl = wordllama(); self.E = np.asarray(self.wl.embedding, dtype=np.float32)
    def encode(self, t): return _Enc([i for i in self.wl.tokenizer.encode(t).ids if i > 2])
    def token_to_id(self, t): return {"[CLS]": 1, "[SEP]": 2}[t]
    def get_vocab_size(self): return self.E.shape[0]

def _device():
    """GPU when available (Colab), unless LMP_DEVICE=cpu. CPU results are bit-for-bit reproducible; GPU runs can differ slightly."""
    import os
    want = os.environ.get("LMP_DEVICE", "auto")
    return torch.device("cuda" if want != "cpu" and torch.cuda.is_available() else "cpu")


class MLJudgeBERT:
    """Wrapper: training with JUDGEBERT-style data augmentation (identical -> 10, unrelated -> 1)."""
    def __init__(self, use_features=False, epochs=40, lr=5e-4, seed=0, data_augmentation=True, vocab_size=3000, embed="wordllama", max_len=320):
        self.use_features, self.epochs, self.lr, self.seed, self.da, self.vocab_size = use_features, epochs, lr, seed, data_augmentation, vocab_size
        self.embed, self.max_len = embed, max_len
    def _feats(self, pairs):
        X = np.array([features(o, s)[0] for o, s in pairs], dtype=np.float32)
        return X
    def fit(self, pairs, y, tokenizer_texts):
        random.seed(self.seed); np.random.seed(self.seed); torch.manual_seed(self.seed)
        pairs, y = list(pairs), list(map(float, y))
        if self.da: pairs, y = augment(pairs, y, self.seed)
        if self.embed == "wordllama":
            self.tok = WordLlamaTokenizer(); d = 256
        else:
            if tokenizer_texts is None: tokenizer_texts = [t for p in pairs for t in p]
            self.tok = train_tokenizer(tokenizer_texts, self.vocab_size); d = 128
        enc = [encode(self.tok, o, s, self.max_len) for o, s in pairs]
        F_ = None
        if self.use_features:
            Xf = self._feats(pairs); self.mu, self.sd = Xf.mean(0), Xf.std(0) + 1e-6; F_ = (Xf - self.mu) / self.sd
        self.dev = _device()
        self.model = CrossEncoder(self.tok.get_vocab_size(), d=d, ff=2 * d, max_len=self.max_len, n_feat=len(FEATURE_NAMES) if self.use_features else 0)
        if self.embed == "wordllama":
            E = torch.tensor(self.tok.E); E = E / E.norm(dim=1, keepdim=True).clamp(min=1e-6)
            self.model.tok.weight.data.copy_(E)
        self.model.to(self.dev)
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=0.01)
        n = len(pairs); bs = 16; steps = self.epochs * math.ceil(n / bs)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=self.lr, total_steps=steps, pct_start=0.1)
        yt = torch.tensor(y, device=self.dev)
        self.model.train()
        for ep in range(self.epochs):
            perm = np.random.permutation(n)
            for i in range(0, n, bs):
                idx = perm[i:i + bs]
                ids, seg, mask, f = (t.to(self.dev) if t is not None else None for t in batchify([enc[j] for j in idx], F_[idx] if F_ is not None else None))
                loss = F.mse_loss(self.model(ids, seg, mask, f), yt[torch.as_tensor(idx, device=self.dev)])
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(self.model.parameters(), 1.0); opt.step(); sched.step()
        return self
    @torch.no_grad()
    def predict(self, pairs):
        self.model.eval(); out = []
        pairs = list(pairs)
        F_ = None
        if self.use_features:
            F_ = (self._feats(pairs) - self.mu) / self.sd
        for i in range(0, len(pairs), 64):
            ids, seg, mask, f = (t.to(self.dev) if t is not None else None for t in batchify([encode(self.tok, o, s, self.max_len) for o, s in pairs[i:i + 64]], F_[i:i + 64] if F_ is not None else None))
            out.extend(self.model(ids, seg, mask, f).cpu().tolist())
        return np.array(out)

def augment(pairs, y, seed):
    pairs, y = list(pairs), list(map(float, y)); rng = random.Random(seed)
    simps = [s for _, s in pairs]
    for o in sorted(set(o for o, _ in pairs)):
        own = {s for oo, s in pairs if oo == o}
        pairs.append((o, o)); y.append(10.0)
        cand = rng.choice(simps)
        while cand in own: cand = rng.choice(simps)
        pairs.append((o, cand)); y.append(1.0)
    return pairs, y

class LegalFeatureRegressor:
    """Ablation: gradient-boosted regressor on LegalDiff features only (no transformer)."""
    def __init__(self, seed=0, data_augmentation=True): self.seed, self.da = seed, data_augmentation
    def fit(self, pairs, y, tokenizer_texts=None):
        from sklearn.ensemble import GradientBoostingRegressor
        if self.da: pairs, y = augment(pairs, y, self.seed)
        X = np.array([features(o, s)[0] for o, s in pairs]); self.m = GradientBoostingRegressor(random_state=self.seed, n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8).fit(X, y); return self
    def predict(self, pairs):
        X = np.array([features(o, s)[0] for o, s in pairs]); return np.clip(self.m.predict(X), 1, 10)
