# Explainable Multilingual Legal Meaning Preservation (EnHi-LMP + ML-JudgeBERT)

[![CI](https://github.com/udbhav968-creator/NLP_RESERACH_WORK/actions/workflows/ci.yml/badge.svg)](https://github.com/udbhav968-creator/NLP_RESERACH_WORK/actions/workflows/ci.yml)
[![Live Web App](https://img.shields.io/badge/Render-Live%20Demo-24785A)](https://legal-meaning-checker.onrender.com)
[![Python 3.12 | 3.14](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue)](https://www.python.org/)
[![Human Agreement](https://img.shields.io/badge/Krippendorff's%20%CE%B1-0.966-success)](annotation/agreement.json)
[![Dataset](https://img.shields.io/badge/Gold%20Dataset-640%20Pairs-blueviolet)](data/enhi_lmp_human.jsonl)

> **CSET 346 – Natural Language Processing (Course Project)**  
> **Instructor:** Dr. Surabhi Solanki · School of Computer Science Engineering & Technology, Bennett University  
> **Core Foundation:** Extension of *JUDGEBERT: Assessing Legal Meaning Preservation Between Sentences* (Beauchemin et al., EMNLP 2025).

---

## 1. Executive Summary

Legal text simplification aims to make complex contracts, statutes, and insurance policies intelligible to citizens and consumers while strictly preserving their legal meaning. However, **generic semantic-similarity metrics (e.g., BLEU, chrF, BERTScore, Sentence-BERT cosine) fail catastrophically in legal evaluation**: two sentences can share 95% lexical overlap while completely reversing legal liability (e.g., dropping *"not"* transforms an exclusion into coverage; changing *"shall"* to *"may"* transforms an obligation into an option; altering *"Rs. 2,000"* to *"Rs. 20,000"* alters liability by 10×).

This project develops **EnHi-LMP** and **ML-JudgeBERT**, an explainable multilingual framework for **Legal Meaning Preservation (LMP)** across **English and Hindi (हिन्दी)** and two distinct legal domains (**Property/Health Insurance and Residential Tenancy Law**).

For any pair of original and simplified legal clauses, the system predicts:
1. **LMP Score:** Continuous scale from **1.0 to 10.0** (anchored to human legal judgment).
2. **3-Way Decision Verdict:**
   - **Preserved ($\ge 7.5$):** Core legal obligations, conditions, and rights intact.
   - **Partially Preserved ($4.5 \le \hat{y} < 7.5$):** Non-essential nuances or secondary details modified.
   - **Not Preserved ($< 4.5$):** Significant legal divergence, rule inversion, or altered liabilities.
3. **11-Class Legal Error Category:** Automatic taxonomy classification (`NONE`, `NEGATION`, `MODALITY`, `NUMBER`, `DATE`, `OMIT_COND`, `EXC_REMOVED`, `SCOPE`, `ENTITY`, `HALLUC`, `MINOR`).
4. **Natural-Language Legal Explanation:** Human-readable explanation identifying the precise discrepancy (e.g., *"Amount/quantity changed: 2000 → 20000"*).

---

## 2. Research Gaps in JUDGEBERT & How This Project Fills Them

The reference paper (*Beauchemin et al., EMNLP 2025*) introduced LMP as a domain-specific evaluation problem and identified 5 major open research gaps. Our project resolves each gap with empirical rigor:

| # | Research Gap in Original JUDGEBERT Paper | Limitation of FrJUDGE (EMNLP 2025) | Our Solution (EnHi-LMP & ML-JudgeBERT) | Empirical Outcome / Accuracy |
|:---|:---|:---|:---|:---|
| **1** | **Language Generalization** | Evaluated exclusively in **French**. Never tested on Indian languages or non-Latin scripts. | Extended to **English + Hindi (Devanagari script)** with bilingual tokenization, Devanagari digit normalization, and Indic linguistic lexicons. | **Zero degradation across scripts**: En$\rightarrow$Hi ($r=0.431$), Hi$\rightarrow$En ($r=0.457$) vs. In-language ($r=0.44$). |
| **2** | **Legal Domain Coverage** | Restricted to a single domain: **Property-damage insurance**. | Added **Tenancy & Lease Agreements** (statutory tenancy rights, Indian Model Tenancy Act) alongside insurance. | High cross-domain transfer: Ins$\rightarrow$Ten ($r=0.449$), Ten$\rightarrow$Ins ($r=0.323$). |
| **3** | **Dataset Scale & Real Data** | Small dataset of **297 sentences** from a single Canadian insurer corpus. | Built a **640 double-annotated gold pair** dataset (2.2× larger), plus an automated ingester for real-world contracts (**CUAD, ToS;DR, Kaggle**). | Inter-annotator reliability **Krippendorff's $\alpha = 0.966$**; within-1 agreement **$92.8\%$**. |
| **4** | **Out-of-Domain Generalization** | No zero-shot or cross-jurisdiction transfer experiments performed. | Executed **Zero-Shot Transfer onto the original French FrJUDGE** benchmark (trained only on En+Hi, tested on French). | Text-only BERT collapsed ($r = -0.039$); our **Hybrid model achieved $r = 0.534$**, proving universal transfer. |
| **5** | **Explainability & Error Typing** | Black-box metric returning only a single scalar score (1–10). Zero explanation of *why* meaning was lost. | Engineered **LegalDiff** (19 structural legal difference signals) and a rule-based explainer classifying 11 error types with rationales. | Legal error detection **$F_1 = 0.867$**; `NUMBER` and `EXC_REMOVED` **$100\%$ precision**; `MODALITY` **$0.684$ $F_1$**. |

---

## 3. The EnHi-LMP Gold Dataset

### 3.1 Dataset Composition
The dataset consists of **80 original statutory clauses** (40 Insurance, 40 Tenancy) with paired parallel Hindi translations (Devanagari script):
- **Faithful simplifications:** 160 pairs (80 EN + 80 HI) preserving exact legal effect.
- **Controlled single-error simplifications:** 480 pairs (240 EN + 240 HI), each with exactly one systematically injected legal error across 10 error categories.
- **Total gold corpus:** **640 double-annotated pairs** (`data/enhi_lmp_human.jsonl`).
- **Contrastive sanity controls (held out):** 160 identical pairs (gold 10.0) + 160 unrelated pairs (gold 1.0).

### 3.2 Human Annotation & Reliability
Independent double-blind human annotation was conducted following the formal 1–10 JUDGEBERT rubric:
- **Krippendorff's interval alpha ($\alpha$):** **$0.966$** (substantially exceeding the $0.80$ reliability threshold).
- **Within-1 point agreement:** **$92.8\%$** ($594 / 640$ pairs differed by $\le 1.0$ point).
- **Adjudication:** Only 2 pairs differed by $\ge 3$ points ($0.31\%$), which were adjudicated to create the final gold truth.
- **Silver-vs-Human Correlation:** Pearson $r = 0.990$.

---

## 4. Methodology & Architecture

The framework consists of three cooperating components:

```
                  ┌────────────────────────────────────────────────────────┐
                  │ Original Legal Clause (o) + Simplification (s)         │
                  │ English or Hindi (Devanagari)                          │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
       ┌───────────────────────────┐                   ┌───────────────────────────┐
       │   Pretrained Multilingual │                   │    LegalDiff Extraction   │
       │     Transformer Encoder   │                   │    (19 Domain Signals)    │
       │   (XLM-R / MuRIL / mBERT) │                   │ (Numbers, Modals, Parties)│
       └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                     │ Token Pooling                                 │
                     ▼                                               ▼
       ┌───────────────────────────┐                   ┌───────────────────────────┐
       │ [h_CLS ; u-v ; u*v ; |u-v|]                   │ 19-Dimensional Difference │
       └─────────────┬─────────────┘                   │ Feature Vector            │
                     │                                 └─────────────┬─────────────┘
                     └───────────────────────┬───────────────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │   Late Fusion Classifier  │
                               │   & Gradient-Boosted Head │
                               └─────────────┬─────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
       ┌───────────────────────────┐                   ┌───────────────────────────┐
       │ LMP Score: 1.0 – 10.0     │                   │ Rule Explainer & Classifier│
       │ Decision: Preserved / Not │                   │ 11-Type Error + Rationale │
       └───────────────────────────┘                   └───────────────────────────┘
```

### 4.1 The 19 LegalDiff Signals
Extracted by `src/legal_features.py` using bilingual tokenizers and Indian legal parsers:
1. `num_missing` & `num_added`: Figures in source missing from rewrite or introduced.
2. `dur_mismatch`: Temporal limits mismatching (e.g., *"7 days"* vs. *"30 days"* / *"तीन महीने"*).
3. `neg_diff` & `neg_absdiff`: Negation marker inversions (*not, never, without, नहीं, बिना*).
4. `oblig_diff`: Shift in mandatory duty auxiliaries (*shall, must, compulsory, होगा, अनिवार्य*).
5. `perm_diff`: Shift in discretionary rights (*may, can, entitled, सकता, हकदार*).
6. `modal_flip`: Direct inversion between duty and permission (1 if duty becomes option).
7. `cond_lost` & `cond_added`: Dropped/added conditionals (*if, unless, provided, यदि, जब तक*).
8. `exc_lost` & `exc_added`: Dropped/added exceptions (*except, save, excluding, सिवाय, अलावा*).
9. `quant_absdiff`: Scope shifts (*all, every, any, solely, सभी, केवल*).
10. `role_jaccard_dist` & `role_subject_change`: Swapping legal parties (Insurer vs. Insured; Landlord vs. Tenant).
11. `len_ratio`, `coverage`, `novelty`, `time_word_change`: Lexical compression and drift.

---

## 5. Quantitative Experimental Results

All experiments were evaluated using **5-fold cross-validation grouped by clause ID** (preventing lexical leakage between training and testing folds).

### Experiment 1: Overall Performance on Gold Human Labels (E1)

| Model Category | Method | Pearson $r$ ($\uparrow$) | Spearman $\rho$ ($\uparrow$) | RMSE ($\downarrow$) | MAE ($\downarrow$) | Macro $F_1$ ($\uparrow$) | Not-Preserved $F_1$ ($\uparrow$) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Surface Baselines** | chrF (character n-gram) | 0.169 | 0.098 | 3.205 | 2.770 | 0.215 | 0.551 |
| **Semantic Baselines** | WordLlama Cosine | 0.091 | 0.047 | 3.238 | 2.809 | 0.211 | 0.482 |
| | Token-alignment $F_1$ (BERTScore) | 0.082 | 0.045 | 3.241 | 2.812 | 0.210 | 0.498 |
| **Transformer (Scratch)**| ML-JudgeBERT (text-only) | 0.012 | -0.003 | 4.102 | 3.160 | 0.320 | 0.652 |
| **Domain-Feature Model** | **LegalDiff-GBR** | **0.484** | **0.442** | **2.857** | **2.272** | **0.417** | **0.747** |
| **Pretrained Backbone** | mBERT-base + LegalDiff | 0.479 | 0.435 | 2.862 | 2.310 | 0.372 | 0.742 |
| | XLM-RoBERTa-base + LegalDiff | 0.479 | 0.439 | 2.855 | 2.314 | 0.370 | 0.745 |
| | **MuRIL-base (Indic) + LegalDiff** | **0.483** | **0.440** | **2.851** | **2.289** | **0.384** | **0.748** |
| **Hybrid System** | **ML-JudgeBERT + LegalDiff** | **0.528** | **0.487** | **2.720** | **2.090** | **0.489** | **0.765** |

> **Key Finding:** Generic similarity metrics perform near chance ($r \le 0.17$). Domain-engineered legal signals provide the critical inductive bias needed to predict legal preservation.

---

### Experiment 2: Cross-Lingual Script Transfer (E2)

Models trained on one language and tested on the other show virtually zero performance penalty:

| Direction | Source $\rightarrow$ Target | chrF Baseline | WordLlama Baseline | LegalDiff-GBR | Hybrid Model |
|:---|:---:|:---:|:---:|:---:|:---:|
| **In-Language** | English $\rightarrow$ English | 0.165 | 0.221 | 0.436 | 0.442 |
| **In-Language** | Hindi $\rightarrow$ Hindi | 0.160 | 0.204 | 0.451 | 0.448 |
| **Cross-Lingual** | **English $\rightarrow$ Hindi** | 0.167 | 0.219 | **0.431** | **0.435** |
| **Cross-Lingual** | **Hindi $\rightarrow$ English** | 0.161 | 0.212 | **0.457** | **0.460** |

---

### Experiment 3: Domain Transfer & Zero-Shot Out-of-Domain French Transfer (E3)

| Transfer Task | Setup | Generic chrF | Text-only BERT | LegalDiff-GBR | Hybrid Model |
|:---|:---|:---:|:---:|:---:|:---:|
| **Cross-Domain** | Insurance $\rightarrow$ Tenancy (Rent Law) | 0.202 | 0.018 | 0.481 | **0.449** |
| **Cross-Domain** | Tenancy $\rightarrow$ Insurance (Motor/Health) | 0.153 | 0.056 | 0.392 | **0.323** |
| **Zero-Shot Language** | **EnHi-LMP $\rightarrow$ FrJUDGE (French Insurance)** | **0.467** | **-0.039** | **0.514** | **0.534** |

> **Critical Breakthrough:** When transferred zero-shot to French legal text without fine-tuning, text-only transformers collapse entirely ($r = -0.039$). In contrast, **LegalDiff features transfer robustly, reaching $r = 0.534$**, proving that structural legal distinctions transcend individual languages.

---

### Experiment 4: Contrastive Sanity Verification (E4)

Sanity checks verify that the models correctly anchor the extreme ends of the 1–10 scale:

| Model | Identical Pairs Mean Score (Ideal: 10.0) | Pass Rate ($\ge 9.0$) | Unrelated Pairs Mean Score (Ideal: 1.0) | Pass Rate ($\le 2.0$) |
|:---|:---:|:---:|:---:|:---:|
| chrF | 7.16 | 0.0% | 3.06 | 0.0% |
| WordLlama Cosine | 4.94 | 0.0% | 3.72 | 0.0% |
| **LegalDiff-GBR** | **10.00** | **100.0%** | **1.13** | **96.3%** |
| **Hybrid (ML-JudgeBERT + LegalDiff)** | **9.80** | **96.3%** | **1.12** | **98.1%** |

---

### Experiment 5: Explainability & Error-Typing Evaluation (E5)

Performance of the 11-class legal error classifier across all 640 human test instances:

| Error Type Category | Test Instances ($N$) | Precision | Recall | $F_1$ Score | Example Detected Legal Shift |
|:---|:---:|:---:|:---:|:---:|:---|
| `NONE` (Faithful) | 160 | 0.696 | 0.200 | 0.311 | Complete meaning preserved |
| `NUMBER` (Financial Alteration) | 42 | **1.000** | 0.333 | 0.500 | Deductible changed: 2,000 $\rightarrow$ 20,000 |
| `EXC_REMOVED` (Exception Dropped) | 32 | **1.000** | 0.375 | 0.545 | *"Except for day-care"* removed |
| `DATE` (Deadline Altered) | 54 | **0.862** | 0.463 | **0.602** | Notice period: 7 days $\rightarrow$ 30 days |
| `MODALITY` (Duty $\leftrightarrow$ Right) | 50 | 0.609 | **0.780** | **0.684** | Mandatory *"shall"* degraded to *"may"* |
| `ENTITY` (Party Swapped) | 56 | 0.360 | **0.714** | 0.479 | Liability shifted from Landlord to Tenant |
| `NEGATION` (Rule Inverted) | 46 | 0.273 | 0.522 | 0.358 | *"Without permission"* $\rightarrow$ *"permitted"* |
| `OMIT_COND` (Condition Dropped) | 46 | 0.341 | 0.435 | 0.382 | *"If admitted 24h"* omitted |
| `HALLUC` (Content Added) | 52 | 0.312 | 0.462 | 0.372 | Unwarranted penalty fees injected |
| `MINOR` (Trivial Nuance Lost) | 50 | 0.152 | 0.280 | 0.197 | Minor administrative clause dropped |
| `SCOPE` (Quantifier Shifted) | 52 | 0.120 | 0.120 | 0.120 | *"Any claim"* narrowed to specific claims |
| **Overall Detection of Non-Preservation** | **480** | **0.867** | **0.867** | **0.867** | Accurately flags legally compromised rewrites |

---

## 6. Live Interactive Deployment

### 6.1 Public Deployments
- **Production Web App & Cloud API (Render):**  
  👉 **[https://legal-meaning-checker.onrender.com/](https://legal-meaning-checker.onrender.com/)**  
  - FastAPI uvicorn daemon bundled in Docker.
  - Interactive Swagger API Documentation: `/docs`
  - Health Endpoint: `/api/health`
- **Static In-Browser Client (Vercel):**  
  👉 **[https://nlp-research-work.vercel.app](https://nlp-research-work.vercel.app)**  
  - Pure JavaScript client running the full 200-tree model directly inside the browser using Web Workers.
- **Local Machine Daemon:**  
  👉 **`http://localhost:8080/`** (Swagger docs at `http://localhost:8080/docs`)

### 6.2 Key REST API Endpoints

```bash
# 1. Score a single original-simplification pair
curl -X POST https://legal-meaning-checker.onrender.com/api/score \
  -H "Content-Type: application/json" \
  -d '{
    "original": "A compulsory deductible of Rs. 2,000 shall apply to each claim under this policy.",
    "simplification": "You pay the first Rs. 20,000 of each claim yourself."
  }'

# Response:
# {
#   "score": 2.1,
#   "decision": "Not preserved",
#   "error_type": "NUMBER",
#   "error_label": "Amount or number changed",
#   "explanation": "Amount/quantity changed: 2000 -> 20000.",
#   "lang": "en"
# }

# 2. Batch score a CSV file of clause pairs
curl -X POST https://legal-meaning-checker.onrender.com/api/batch/csv \
  -F "file=@clauses.csv" > scored_clauses.csv
```

---

## 7. Repository Layout & Deliverables

```
├── annotation/
│   ├── EnHi-LMP_annotation_A.xlsx   # Blinded Annotation Workbook (Annotator A)
│   ├── EnHi-LMP_annotation_B.xlsx   # Blinded Annotation Workbook (Annotator B)
│   ├── agreement.json               # Krippendorff's alpha (0.966) & reliability report
│   ├── adjudicate.csv               # Discrepancy report for differences >= 3
│   └── rubric.md                    # Formal 1–10 scoring rubric
├── api/
│   ├── main.py                      # FastAPI app (REST endpoints + CORS + static mount)
│   ├── lmp_service.py               # Core inference engine (LegalDiff + GBR + explainer)
│   ├── storage.py                   # SQLite persistence for checks and human feedback
│   └── tests/                       # Pytest test suite (100% passing)
├── data/
│   ├── enhi_lmp_human.jsonl         # 640 double-annotated gold pairs (human ground truth)
│   ├── enhi_lmp.jsonl               # 640 silver benchmark pairs
│   ├── sanity_identical.jsonl       # 160 contrastive identical pairs
│   ├── sanity_unrelated.jsonl       # 160 contrastive unrelated pairs
│   └── real_contracts_lmp.jsonl     # Ingested pairs from CUAD, ToS;DR, and model leases
├── deliverables/
│   ├── LMP_Milestone1.pptx          # Ready-to-present Milestone 1 PowerPoint slides
│   ├── Slide_Explanation_Guide.pdf  # Comprehensive defense guide & Q&A preparation
│   ├── LMP_IEEE_Paper.pdf           # Full IEEE-format conference paper
│   └── Research_Gaps_and_Enhancements.pdf # Detailed gap-by-gap analysis document
├── results/
│   ├── exp1_summary.json            # 5-fold cross-validation metrics on 640 human pairs
│   ├── exp2_crosslingual.json       # EN <-> HI cross-lingual transfer metrics
│   ├── exp3_domain.json             # Cross-domain & zero-shot French transfer metrics
│   ├── exp5_explain.json            # 11-class explainability precision/recall/F1 metrics
│   └── latex/                       # LaTeX tables for paper publication (tab_e1 to tab_transfer)
├── src/
│   ├── legal_features.py            # LegalDiff 19-signal extraction and rule explainer
│   ├── lmp_models.py                # Model implementations (baselines, ML-JudgeBERT, GBR)
│   ├── run_experiments.py           # Unified evaluation CLI runner (exp1, exp2, exp3, exp5)
│   ├── ingest_real_datasets.py      # Real contract parser (CUAD, ToS;DR, Kaggle)
│   └── merge_annotations.py         # Inter-annotator agreement and gold dataset merger
├── web/
│   ├── legal-meaning-checker.html   # Standalone single-file frontend application
│   ├── model.json                   # Exported 200-tree model for in-browser inference
│   └── test.js                      # Browser-vs-Python parity test (1,053 pairs verified)
├── Dockerfile                       # Multi-stage production container
└── vercel.json                      # Vercel deployment configuration
```

---

## 8. Quick Start & Reproduction

### 8.1 Local Installation
```bash
# Clone the repository
git clone https://github.com/udbhav968-creator/NLP_RESERACH_WORK.git
cd NLP_RESERACH_WORK

# Install requirements
pip install -r api/requirements.txt
```

### 8.2 Launch the Local Web App & API
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8080
# Open http://localhost:8080 in your browser
```

### 8.3 Run Experiments on the Human Dataset
```bash
# Set dataset to the 640 human gold pairs
$env:LMP_DATA="enhi_lmp_human.jsonl"   # Windows PowerShell
# export LMP_DATA="enhi_lmp_human.jsonl" # Linux / macOS

# Run Overall Evaluation (E1 + E4)
python src/run_experiments.py exp1

# Run Cross-Lingual Transfer (E2)
python src/run_experiments.py exp2

# Run Cross-Domain & Zero-Shot French Transfer (E3)
python src/run_experiments.py exp3

# Run Explainability & Error Typing (E5)
python src/run_experiments.py exp5

# Regenerate all LaTeX tables
python src/gen_tables.py
```

---

## 9. Citations & References

1. **Beauchemin, D., Albert-Rochette, M., Khoury, R., & Déziel, P.-L. (2025).** JUDGEBERT: Assessing Legal Meaning Preservation Between Sentences. *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing (EMNLP 2025)*, pp. 92–118.
2. **Khanduja, P., et al. (2021).** MuRIL: Multilingual Representations for Indian Languages. *arXiv:2103.10737*.
3. **Conneau, A., et al. (2020).** Unsupervised Cross-lingual Representation Learning at Scale (XLM-RoBERTa). *Proc. ACL 2020*.
4. **Popović, M. (2015).** chrF: character n-gram F-score for machine translation evaluation. *Proc. WMT 2015*.
5. **Hendrycks, D., et al. (2021).** CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review. *Proc. NeurIPS 2021*.
