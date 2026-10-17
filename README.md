# Explainable Multilingual Legal Meaning Preservation (EnHi-LMP + ML-JudgeBERT)

CSET 346 – Natural Language Processing · Course project
Extension of **JUDGEBERT** (Beauchemin et al., EMNLP 2025) from French insurance text to **English + Hindi** and a new legal domain (**tenancy / rent agreements**), with an **explanation module** that names the legal error and gives a short rationale.

For every original–simplified legal sentence pair the system outputs:

| Field | Values |
|---|---|
| LMP score | 1–10 (continuous) |
| Decision | Preserved (≥ 7.5) / Partially Preserved (4.5–7.5) / Not Preserved (< 4.5) |
| Legal error type | NONE, NEGATION, MODALITY, NUMBER, DATE, OMIT_COND, EXC_REMOVED, SCOPE, ENTITY, HALLUC, MINOR |
| Explanation | one-sentence rationale, e.g. "Time limit changed: 7 -> 30." |

## Live demo

The best model (LegalDiff-GBR, trained on all 640 pairs) runs in the browser as the **Legal Meaning Checker**: `web/legal-meaning-checker.html` (open it locally) — see `web/README.md`. Results on 640 pairs (5-fold grouped CV): Pearson r 0.48 vs 0.17 for chrF; Not-preserved F1 0.75; error-detection F1 0.87; zero-shot r 0.52 on human-labelled FrJUDGE.

## Deliverables (in `deliverables/`)

| File | What it is |
|---|---|
| `LMP_Milestone1.pptx` | 10-slide Milestone 1 presentation with speaker notes and E1–E5 results |
| `LMP_IEEE_Paper.pdf` / `.docx` | Research paper (IEEE two-column style), PDF and editable Word |
| `Research_Gaps_and_Enhancements.pdf` | The 9 research gaps in JUDGEBERT and how this project addresses each |
| `build_slides.js` | Script that regenerates the slides from `results/` (pptxgenjs) |

Paper sources (LaTeX, figure, Word builder) are in `paper/`. Windows users can train everything with `train_enhi_lmp.ps1` (see the script header).

## Repository layout

```
data/
  en_insurance.py, en_tenancy.py      # 40 + 40 English source clauses with faithful + perturbed simplifications
  hi_insurance.py, hi_tenancy.py      # parallel Hindi (Devanagari) versions, same IDs
  extra/part_*.py                     # v2: two more single-error EN/HI rewrites per clause
  enhi_lmp.jsonl                      # 640 assembled pairs (built by src/build_dataset.py)
  sanity_identical.jsonl              # 160 identical pairs (gold 10) – never used for training
  sanity_unrelated.jsonl              # 160 unrelated pairs (gold 1)  – never used for training
  frjudge_{train,dev,test}.jsonl      # FrJUDGE official splits (CC BY-NC-SA 4.0) for transfer tests
src/
  build_dataset.py                    # assembles the dataset, sanity sets and FrJUDGE splits
  legal_features.py                   # LegalDiff: EN/HI(/FR) legal-difference features + rule-based explainer
  lmp_models.py                       # baselines, ML-JudgeBERT cross-encoder, LegalDiff-GBR
  run_experiments.py                  # Experiments 1-5 (exp1 | exp2 | exp3 | exp5)
  make_annotation_kit.py              # builds the 2 blinded Excel annotation workbooks
  merge_annotations.py                # Krippendorff's alpha, adjudication list, human-label dataset
  finetune_pretrained.py              # ML-JudgeBERT with XLM-R / MuRIL (GPU)
annotation/
  EnHi-LMP_annotation_A.xlsx, _B.xlsx # give one to each annotator (rubric on sheet 1)
  blind_key.csv                       # code -> pair id (do NOT give to annotators)
results/                              # JSON outputs of every experiment
ML_JudgeBERT_pretrained_Colab.ipynb   # one-click Colab run of the pretrained encoders
```

## Quick start

```bash
pip install -r requirements.txt
python src/build_dataset.py            # needs the JUDGEBERT repo cloned at /tmp/ext/JUDGEBERT for FrJUDGE
python src/run_experiments.py exp1     # E1 + E4 (+ predictions used by E5)
python src/run_experiments.py exp2     # E2 cross-lingual transfer
python src/run_experiments.py exp3     # E3 cross-domain + FrJUDGE transfer
python src/run_experiments.py exp5     # E5 explanations / error typing
python src/finetune_pretrained.py --model xlm-roberta-base   # GPU: pretrained ML-JudgeBERT
```

## Completing the project (remaining steps)

1. **Human annotation.** Give `annotation/EnHi-LMP_annotation_A.xlsx` and `_B.xlsx` to two annotators (each scores all 640 pairs, 1–10, independently).
   Then run `python src/merge_annotations.py annotation/EnHi-LMP_annotation_A.xlsx annotation/EnHi-LMP_annotation_B.xlsx`
   → prints Krippendorff's α, writes `annotation/adjudicate.csv` (pairs differing by ≥ 3 points) and `data/enhi_lmp_human.jsonl`.
2. **Re-run experiments on human labels:** `LMP_DATA=enhi_lmp_human.jsonl python src/run_experiments.py exp1` (then `exp2`, `exp3`, `exp5`).
3. **Pretrained encoder:** open `ML_JudgeBERT_pretrained_Colab.ipynb` in Google Colab (T4 GPU) and run all cells (XLM-R base and MuRIL base).

## Getting the code

```bash
git clone https://github.com/udbhav968-creator/NLP_RESERACH_WORK.git
cd NLP_RESERACH_WORK
python src/demo.py                                   # score three example clauses
python src/demo.py "original sentence" "simplified sentence"
```

## Changelog — v2 (code review fixes)

| Area | Problem in v1 | Fix in v2 |
|---|---|---|
| Hindi tokenisation | Danda (। ॥) stayed attached to the last word, so sentence-final नहीं / करेगा / होगा were missed | Danda treated as punctuation |
| Numbers in compounds | "six-month", "three-month" were single tokens, so number changes were missed | Hyphenated compounds split (number words such as "twenty-four" kept) |
| Possessives | "tenant's", "landlord's" did not match party roles | Possessive 's removed; French elisions (l', n', lorsqu') split |
| Time units | माह vs महीने, वर्ष vs साल, day vs days counted as different units | One canonical unit per word (day/week/month/year/hour/date) |
| Modality | "cannot" / "नहीं … सकता" (prohibition) counted as permission | Negated permission counted as obligation (same force as "shall not") |
| Lexicons | "one"/"एक" asymmetric; no crore/thousand; no "without"/"none"; Hindi infinitives (करना, देना) counted as obligation | Fixed; all lexicons NFC-normalised |
| Pretrained fusion | Late-fusion weight chosen on training predictions (in-sample) | 20 % of training clauses held out to pick the best epoch and the fusion weight |
| Metrics | Constant predictions gave NaN correlations | Guarded (reported as 0) |
| Human labels | Unannotated pairs silently kept silver scores | `enhi_lmp_human.jsonl` contains human-scored pairs only, with `label_source` |
| Colab | Placeholder clone URL and folder name | Points to this repository |

## Models

* **Baselines (generic similarity):** chrF; WordLlama sentence-embedding cosine; BERTScore-style greedy token-alignment F1.
  Each similarity is mapped to the 1–10 scale by a linear calibrator fitted on the training fold only.
* **ML-JudgeBERT:** JUDGEBERT-style cross-encoder `[CLS] original [SEP] simplification [SEP]` → Transformer encoder →
  `[h_CLS ; u−v ; u⊙v ; |u−v|]` → MLP → `ŷ = 1 + 9·σ(z)`, trained with MSE and JUDGEBERT's data augmentation
  (identical → 10, unrelated → 1).
* **ML-JudgeBERT + LegalDiff:** the same model with the 19-dimensional LegalDiff vector fused before the head.
* **LegalDiff-GBR:** ablation — gradient-boosted regressor on LegalDiff features only.

> Compute note: the development sandbox had no access to pretrained-model hubs, so the encoder reported in
> `results/` is a 2-layer Transformer **trained from scratch**. The intended backbone is a pretrained multilingual
> encoder (XLM-R base or MuRIL base) fine-tuned on a GPU; this is the main planned upgrade.

## Data and labels

80 clauses (40 insurance, 40 tenancy) × 2 languages × 4 simplifications (one faithful, three each with a single injected legal error of a different type) = **640 pairs**, plus 160 identical and 160 unrelated sanity pairs. (v1 had one error rewrite per clause, 320 pairs; its results are kept in `results/v2_320/`.)
Current LMP scores are **rubric-based silver labels** (see rubric below). They must be replaced by double human annotation
(2 annotators, adjudication of differences ≥ 3, Krippendorff's α) before final reporting.

| LMP | Meaning |
|---|---|
| 9–10 | Legal effect identical; only wording changed |
| 8 | Preserved; trivial non-legal nuance lost |
| 6–7 | Minor secondary detail omitted (partial) |
| 4–5 | Secondary condition dropped or scope slightly shifted (partial / not) |
| 2–3 | Core condition, exception, number, date, party or modality changed |
| 1 | Rule reversed (contradiction) or unrelated |

## Evaluation

Pearson r, Spearman ρ, RMSE, MAE (regression); macro-F1 of the 3-way decision; F1 for "Not Preserved" detection;
precision / recall / F1 of the error-type classifier; sanity rates (% identical ≥ 9, % unrelated ≤ 2).
All cross-validation is **grouped by clause**, so the English and Hindi versions of a clause are always in the same fold.

## Reference

Beauchemin, D., Albert-Rochette, M., Khoury, R., & Déziel, P.-L. (2025). JUDGEBERT: Assessing Legal Meaning Preservation
Between Sentences. *Proc. EMNLP 2025*, 92–118. Code/data: https://github.com/GRAAL-Research/JUDGEBERT
