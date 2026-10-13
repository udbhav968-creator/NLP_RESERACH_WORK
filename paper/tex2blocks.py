"""Convert the paper's restricted LaTeX into JSON blocks for the Word (docx-js) build."""
import re, json
LAB = {"sec:motivation": "III", "sec:limits": "IX", "tab:data": "I", "tab:e1": "II", "tab:lang": "III", "tab:transfer": "IV",
       "tab:sanity": "V", "tab:explain": "VI", "tab:cases": "VII", "fig:err": "1"}
CITE = {k: i + 1 for i, k in enumerate(["judgebert", "bleu", "chrf", "sari", "sbert", "bertscore", "meaningbert", "geval", "xlmr", "muril", "kripp"])}
MATH = [(r"\hat{y}", "ŷ"), (r"\hat{y", "ŷ"), (r"\rightarrow", "→"), (r"\leftrightarrow", "↔"), (r"\le", "≤"), (r"\ge", "≥"), (r"\approx", "≈"),
        (r"\in", "∈"), (r"\ell", "ℓ"), (r"\theta", "θ"), (r"\sigma", "σ"), (r"\rho", "ρ"), (r"\alpha", "α"), (r"\delta", "δ"), (r"\odot", "⊙"),
        (r"\cdot", "·"), (r"\times", "×"), (r"\uparrow", "↑"), (r"\downarrow", "↓"), (r"\mathcal{E}", "ℰ"), (r"\pm", "±"), (r"\{", "⦃"), (r"\}", "⦄"),
        (r"\,", " "), (r"\;", " ")]

def math(m):
    for a, b in MATH: m = m.replace(a, b)
    m = re.sub(r"\\(?:text|mathrm|textsc)\{([^{}]*)\}", r"\1", m)
    m = re.sub(r"_\{\\text\{([^{}]*)\}\}", r"_\1", m)
    m = m.replace("{", "").replace("}", "").replace("^×", "×").replace("⦃", "{").replace("⦄", "}")
    return m

def text_clean(t):
    t = t.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "–").replace("~", "\u00a0").replace(r"\ldots", "…")
    t = t.replace(r"\%", "%").replace(r"\&", "&").replace("\\ ", " ").replace(r"\_", "_").replace("\\\\", " ")
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = re.sub(r"\\ref\{([^}]*)\}", lambda m: LAB[m.group(1)], t)
    t = re.sub(r"\\cite\{([^}]*)\}", lambda m: "[" + ", ".join(str(CITE[c.strip()]) for c in m.group(1).split(",")) + "]", t)
    t = re.sub(r"\s+", " ", t)
    return t

def runs(t):
    """Parse inline formatting into runs."""
    out = []
    i = 0; buf = ""
    def flush(style=None):
        nonlocal buf
        if buf: out.append(dict(t=text_clean(buf), **(style or {}))); buf = ""
    while i < len(t):
        if t[i] == "$":
            j = t.index("$", i + 1); flush(); out.append(dict(t=text_clean(math(t[i + 1:j])))); i = j + 1; continue
        m = re.match(r"\\(textbf|emph|textsc|texttt|hi|textit)\{", t[i:])
        if m:
            flush(); depth = 1; k = i + len(m.group(0)); start = k
            while depth:
                if t[k] == "{": depth += 1
                elif t[k] == "}": depth -= 1
                k += 1
            inner = t[start:k - 1]; cmd = m.group(1)
            for r in runs(inner):
                if cmd == "textbf": r["b"] = True
                if cmd in ("emph", "textit"): r["i"] = True
                if cmd == "textsc": r["sc"] = True
                if cmd == "texttt": r["mono"] = True
                if cmd == "hi": r["dev"] = True
                out.append(r)
            i = k; continue
        buf += t[i]; i += 1
    flush()
    return [r for r in out if r["t"]]

def blocks(src):
    src = re.sub(r"(?m)^%.*$", "", src)
    B = []
    # replace floats by markers
    def float_marker(m):
        lab = re.search(r"\\label\{([^}]*)\}", m.group(0))
        return f"\n\n@@FLOAT {lab.group(1)}@@\n\n"
    src = re.sub(r"\\begin\{(table\*?|figure)\}.*?\\end\{\1\}", float_marker, src, flags=re.S)
    src = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", lambda m: "\n\n@@EQ " + m.group(1).replace("\n", " ") + "@@\n\n", src, flags=re.S)
    src = re.sub(r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}", lambda m: "\n\n@@ENUM " + m.group(1).replace("\n", " ") + "@@\n\n", src, flags=re.S)
    for para in re.split(r"\n\s*\n", src):
        p = para.strip()
        if not p: continue
        m = re.match(r"\\section\*?\{([^}]*)\}(\\label\{[^}]*\})?\s*(.*)", p, re.S)
        if m:
            B.append(dict(type="h1", text=text_clean(m.group(1)), numbered=not p.startswith("\\section*")))
            p = m.group(3).strip()
            if not p: continue
        m = re.match(r"\\subsection\{([^}]*)\}(\\label\{[^}]*\})?\s*(.*)", p, re.S)
        if m:
            B.append(dict(type="h2", text=text_clean(runs(m.group(1))[0]["t"] if "$" in m.group(1) else m.group(1)))); p = m.group(3).strip()
            if "$" in m.group(1) or "\\" in m.group(1): B[-1]["runs"] = runs(m.group(1))
            if not p: continue
        if p.startswith("@@FLOAT"):
            B.append(dict(type="float", id=p[8:-2].strip())); continue
        if p.startswith("@@EQ"):
            B.append(dict(type="eq", body=p[5:-2])); continue
        if p.startswith("@@ENUM"):
            items = [x.strip() for x in p[7:-2].split("\\item") if x.strip()]
            B.append(dict(type="enum", items=[runs(x) for x in items])); continue
        B.append(dict(type="p", runs=runs(p)))
    return B

doc = dict(abstract=runs(open("abstract.tex").read().strip()),
           body=blocks(open("sections_static.tex").read()) + blocks(open("sections_results.tex").read()))
json.dump(doc, open("paper_blocks.json", "w"), ensure_ascii=False, indent=1)
print(len(doc["body"]), [b["type"] + ":" + b.get("text", b.get("id", ""))[:25] for b in doc["body"] if b["type"] in ("h1", "float", "eq")])
