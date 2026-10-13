"""Generate LaTeX tables for the paper from results/*.json."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda n: json.load(open(os.path.join(ROOT, "results", n)))
E1, E2, E3, E5 = R("exp1_summary.json"), R("exp2_crosslingual.json"), R("exp3_domain.json"), R("exp5_explain.json")
NAMES = {"chrF (lexical)": "chrF", "WordLlama cosine (semantic)": "Embedding cosine", "Token-alignment F1 (BERTScore-style)": "Token-align.\\ F1",
         "LegalDiff-GBR": "LegalDiff-GBR", "ML-JudgeBERT": "ML-JudgeBERT (text)", "ML-JudgeBERT+LegalDiff": "ML-JudgeBERT+LegalDiff"}
ORDER = list(NAMES)
f2 = lambda v: f"{v:.2f}"
m = lambda o: o[0] if isinstance(o, list) else o
out = {}

# Table: E1 overall
cols = [("pearson", 1), ("spearman", 1), ("rmse", -1), ("mae", -1), ("f1_decision", 1), ("f1_notpreserved", 1)]
best = {k: (max if d > 0 else min)(m(E1["overall"][x]["all"][k]) for x in ORDER) for k, d in cols}
lines = []
for i, x in enumerate(ORDER):
    if i == 3: lines.append("\\midrule")
    cells = []
    for k, _ in cols:
        v = m(E1["overall"][x]["all"][k]); s = f2(v)
        if i >= 3 and k in ("pearson",): s += "\\,{\\scriptsize$\\pm$" + f2(E1["overall"][x]["all"][k][1]) + "}"
        if abs(v - best[k]) < 1e-9: s = "\\textbf{" + s + "}"
        cells.append(s)
    lines.append(NAMES[x] + " & " + " & ".join(cells) + " \\\\")
out["tab_e1"] = "\n".join(lines)

# Table: by language and domain (Pearson / RMSE)
lines = []
for i, x in enumerate(ORDER):
    if i == 3: lines.append("\\midrule")
    c = []
    for key, g in [("by_lang", "en"), ("by_lang", "hi"), ("by_domain", "insurance"), ("by_domain", "tenancy")]:
        c.append(f2(m(E1[key][x][g]["pearson"])))
    lines.append(NAMES[x] + " & " + " & ".join(c) + " \\\\")
out["tab_lang_dom"] = "\n".join(lines)

# Table: transfer (E2 + E3)
T = [("en->hi", E2, "EN$\\rightarrow$HI"), ("hi->en", E2, "HI$\\rightarrow$EN"), ("en->en", E2, "EN$\\rightarrow$EN"), ("hi->hi", E2, "HI$\\rightarrow$HI"),
     ("insurance->tenancy", E3, "Ins.$\\rightarrow$Ten."), ("tenancy->insurance", E3, "Ten.$\\rightarrow$Ins."),
     ("EnHi->FrJUDGE (zero-shot)", E3, "EnHi$\\rightarrow$FrJUDGE"), ("FrJUDGE->FrJUDGE (in-language)", E3, "FrJUDGE$\\rightarrow$FrJUDGE")]
lines = []
for key, src, lab in T:
    if key == "insurance->tenancy" or key == "EnHi->FrJUDGE (zero-shot)": lines.append("\\midrule")
    if key not in src: continue
    vals = [m(src[key][x]["pearson"]) for x in ORDER]
    b = max(vals)
    lines.append(lab + " & " + " & ".join(("\\textbf{%s}" % f2(v)) if v == b else f2(v) for v in vals) + " \\\\")
out["tab_transfer"] = "\n".join(lines)

# Sanity
S = E1["sanity"]
lines = []
for x in ORDER + ["ML-JudgeBERT+LegalDiff (no DA)"]:
    n = NAMES.get(x, "ML-JudgeBERT+LegalDiff, no aug.")
    lines.append(f"{n} & {f2(S[x]['identical_mean'])} & {100*S[x]['identical_ge9']:.0f}\\% & {f2(S[x]['unrelated_mean'])} & {100*S[x]['unrelated_le2']:.0f}\\% \\\\")
out["tab_sanity"] = "\n".join(lines)

# Explanation per type
lines = []
for t, v in sorted(E5["per_type"].items(), key=lambda kv: -kv[1]["n"]):
    lines.append(f"\\textsc{{{t.lower().replace('_', chr(92)+'_')}}} & {v['n']} & {f2(v['p'])} & {f2(v['r'])} & {f2(v['f1'])} \\\\")
out["tab_explain"] = "\n".join(lines)
for k, v in out.items():
    open(os.path.join("/home/claude/paper", k + ".tex"), "w").write(v + "\n")
print("ok", list(out))
