# Results before (v1) and after (v2) the code-review fixes

Same data (silver labels), same protocol (grouped 5-fold CV by clause, 3 seeds). v1 files are kept in `results/v1_silver/`.
Only LegalDiff and the models that use it change; chrF, embedding cosine and token-F1 are identical in v1 and v2.

## E1 — overall (Pearson r)

| Model | v1 r | v2 r | v2 r English | v2 r Hindi | v2 RMSE |
|---|---|---|---|---|---|
| chrF | 0.37 | 0.37 | 0.36 | 0.38 | 3.38 |
| Embedding cosine | 0.18 | 0.18 | 0.38 | 0.21 | 3.58 |
| Token-alignment F1 | 0.18 | 0.18 | 0.42 | 0.28 | 3.58 |
| **LegalDiff-GBR** | 0.60 | **0.60** | 0.63 | 0.56 | 2.96 |
| ML-JudgeBERT (text only) | 0.12 | 0.12 | 0.11 | 0.14 | 4.48 |
| **ML-JudgeBERT + LegalDiff** | 0.44 | **0.49** | 0.48 | 0.50 | 3.66 |
| ML-JudgeBERT + LegalDiff (no augmentation) | 0.42 | 0.48 | 0.46 | 0.51 | 3.65 |

## E2 — cross-lingual transfer, LegalDiff-GBR (r)

| Train → test | v1 | v2 |
|---|---|---|
| EN → EN | 0.55 | 0.59 |
| EN → HI | 0.48 | 0.52 |
| HI → EN | 0.54 | 0.60 |
| HI → HI | 0.50 | 0.49 |

## E3 — domain and FrJUDGE (human labels) transfer (r)

| Setting | GBR v1 | GBR v2 | Hybrid v1 | Hybrid v2 |
|---|---|---|---|---|
| Insurance → tenancy | 0.55 | 0.57 | 0.51 | 0.57 |
| Tenancy → insurance | 0.57 | 0.51 | 0.38 | 0.40 |
| EnHi → FrJUDGE (zero-shot) | 0.56 | 0.61 | 0.59 | 0.60 |
| FrJUDGE → FrJUDGE | 0.60 | 0.56 | 0.48 | 0.56 |

## E5 — explanations (LegalDiff-GBR scores)

| Measure | v1 | v2 |
|---|---|---|
| Error detection P / R / F1 | 0.74 / 0.85 / 0.79 | 0.75 / 0.84 / 0.79 |
| Exact error type (all errors) | 40 % | 42 % |
| Exact error type (detected errors) | 47 % | 50 % |
| Macro-F1 over 11 types | 0.41 | 0.44 |
| DATE / NUMBER / MODALITY F1 | 0.58 / 0.50 / 0.49 | 0.67 / 0.67 / 0.55 |
| NEGATION / SCOPE F1 | 0.29 / 0.00 | 0.21 / 0.00 |
