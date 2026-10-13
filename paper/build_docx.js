const fs = require("fs");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, BorderStyle, ShadingType,
  SectionType, ImageRun, TabStopType, LevelFormat, VerticalAlign } = D;

const doc = JSON.parse(fs.readFileSync("paper_blocks.json"));
const T = JSON.parse(fs.readFileSync("tables.json"));
const FONT = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Nirmala UI", eastAsia: "Times New Roman" };
const COLW = 5021, FULLW = 10282;
const roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
const letters = "ABCDEFGHIJ";

const run = (r, extra = {}) => new TextRun(Object.assign({
  text: r.t, bold: !!r.b, italics: !!r.i, smallCaps: !!r.sc,
  font: r.mono ? "Courier New" : r.dev ? { ascii: "Nirmala UI", hAnsi: "Nirmala UI", cs: "Nirmala UI" } : FONT,
}, extra));
const para = (runs, opt = {}) => new Paragraph(Object.assign({ children: runs, alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 202 }, spacing: { after: 0, line: 240 } }, opt));

// ---------- tables
const thin = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function makeTable(header, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const align = opts.align || widths.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  const fs = opts.size || 15;
  const mkRow = (cells, { top = false, bottom = false, headerRow = false, mid = false } = {}) => new TableRow({
    tableHeader: headerRow, cantSplit: true,
    children: cells.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      margins: { top: 20, bottom: 20, left: 50, right: 50 },
      verticalAlign: VerticalAlign.CENTER,
      borders: { top: top ? { style: BorderStyle.SINGLE, size: 8, color: "000000" } : mid ? thin : none,
                 bottom: bottom ? { style: BorderStyle.SINGLE, size: headerRow ? 4 : 8, color: "000000" } : none, left: none, right: none },
      children: [new Paragraph({ keepNext: true, keepLines: true, alignment: align[i], spacing: { after: 0 }, children: [new TextRun({ text: c.t, bold: !!c.b, size: fs, font: FONT })] })],
    })),
  });
  const out = [mkRow(header.map((t) => ({ t, b: false })), { top: true, bottom: true, headerRow: true })];
  let pendingMid = false;
  rows.forEach((r, k) => {
    if (r === "MID") { pendingMid = true; return; }
    out.push(mkRow(r, { mid: pendingMid, bottom: k === rows.length - 1 }));
    pendingMid = false;
  });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: out, alignment: AlignmentType.CENTER });
}
const capTable = (num, text) => [
  new Paragraph({ keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 120, after: 0 }, children: [new TextRun({ text: "TABLE " + num, size: 16, font: FONT })] }),
  new Paragraph({ keepNext: true, alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text, size: 16, smallCaps: true, font: FONT })] }),
];
const note = (text) => new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 40, after: 120 }, children: [new TextRun({ text, size: 14, italics: true, font: FONT })] });

const FLOATS = {
  "tab:data": () => [...capTable("I", "EnHi-LMP dataset statistics"),
    makeTable(["", "Insurance", "Tenancy", "Total"], [
      [{ t: "English pairs" }, { t: "80" }, { t: "80" }, { t: "160" }],
      [{ t: "Hindi pairs" }, { t: "80" }, { t: "80" }, { t: "160" }],
      [{ t: "Faithful / single-error" }, { t: "80 / 80" }, { t: "80 / 80" }, { t: "160 / 160" }],
      [{ t: "Preserved / Partial / Not (gold)" }, { t: "–" }, { t: "–" }, { t: "160 / 20 / 140" }],
      [{ t: "Sanity: identical / unrelated" }, { t: "–" }, { t: "–" }, { t: "160 / 160" }],
    ], [2121, 900, 900, 1100]),
    note("Error types (EN+HI): scope 22, omitted condition 20, date 20, modality 16, minor 16, hallucination 16, party 16, negation 14, exception 12, number 8.")],
  "tab:lang": () => [...capTable("III", "Pearson r by language and domain (E1/E2)"),
    makeTable(["System", "EN", "HI", "Insurance", "Tenancy"], T.lang_dom, [1921, 700, 700, 850, 850]), note("")],
  "tab:sanity": () => [...capTable("V", "E4: Sanity checks (mean ŷ; share within tolerance)"),
    makeTable(["System", "Ident.", "≥ 9", "Unrel.", "≤ 2"], T.sanity, [2221, 700, 700, 700, 700]), note("")],
  "tab:explain": () => [...capTable("VI", "E5: Error-type explanation quality (LegalDiff-GBR scores)"),
    makeTable(["Type", "n", "P", "R", "F1"], T.explain, [1821, 800, 800, 800, 800]), note("")],
  "fig:err": () => [
    new Paragraph({ keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: "png", data: fs.readFileSync("fig_errtype.png"), transformation: { width: 330, height: Math.round(330 * 550 / 1109) } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: "Fig. 1. E5: mean LMP by gold error type (out-of-fold predictions, EN+HI).", size: 16, font: FONT })] })],
};
const WIDE = {
  "tab:e1": () => [...capTable("II", "E1: 5-fold grouped CV on EnHi-LMP (n = 320)"),
    makeTable(["System", "r ↑", "ρ ↑", "RMSE ↓", "MAE ↓", "Dec.F1 ↑", "NP-F1 ↑"], T.e1, [2882, 1300, 1100, 1200, 1200, 1300, 1300], { size: 16 }),
    note("Learned models: mean ± s.d. over 3 seeds; bold = best.")],
  "tab:transfer": () => [...capTable("IV", "E2/E3: Transfer across language, domain and to human-labelled FrJUDGE (Pearson r)"),
    makeTable(["Train → test", "chrF", "Emb. cosine", "Token-align. F1", "LegalDiff-GBR", "ML-JudgeBERT (text)", "ML-JudgeBERT+LegalDiff"], T.transfer,
      [2082, 1000, 1200, 1400, 1400, 1500, 1700], { size: 16 }), note("Bold = best per row.")],
  "tab:cases": () => [...capTable("VII", "E5: Qualitative analysis of 18 legally difficult cases (1–10 LMP scale; × = wrong predicted type)"),
    makeTable(["#", "Lang", "Gold type", "Legal change (original → simplification)", "Gold", "chrF", "Emb.", "GBR", "Hybrid", "Predicted type"], T.cases,
      [330, 450, 1200, 4300, 500, 500, 500, 500, 600, 1402], { size: 14, align: [AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.LEFT] }),
    note("")],
};

// ---------- body
let sec = 0, sub = 0;
const sections = [];
let cur = [];
const pageProps = { page: { size: { width: 11906, height: 16838 }, margin: { top: 1077, bottom: 2438, left: 812, right: 812 } } };
const flushTwoCol = () => { if (cur.length) sections.push({ properties: Object.assign({ type: SectionType.CONTINUOUS, column: { count: 2, space: 239 } }, pageProps), children: cur }); cur = []; };

// title (single column)
const titleKids = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: "Explainable Multilingual Legal Meaning Preservation Using JUDGEBERT", size: 48, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "Student Name 1, Student Name 2, Student Name 3", size: 22, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "School of Computer Science Engineering and Technology, Bennett University, Greater Noida, India", size: 20, italics: true, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 280 }, children: [new TextRun({ text: "CSET 346 – Natural Language Processing  ·  Project Instructor: Dr. Surabhi Solanki", size: 18, font: FONT })] }),
];
sections.push({ properties: Object.assign({}, pageProps), children: titleKids });

cur.push(para([new TextRun({ text: "Abstract", bold: true, italics: true, size: 18, font: FONT }), new TextRun({ text: "—", bold: true, size: 18, font: FONT }),
  ...doc.abstract.map((r) => run(r, { bold: true, size: 18 }))], { indent: { firstLine: 0 } }));
cur.push(para([new TextRun({ text: "Index Terms", bold: true, italics: true, size: 18, font: FONT }), new TextRun({ text: "—legal meaning preservation, text simplification, JUDGEBERT, Hindi NLP, explainable evaluation, cross-lingual transfer.", bold: true, size: 18, font: FONT })], { indent: { firstLine: 0 }, spacing: { before: 80, after: 120 } }));

let eqn = 0;
doc.body.forEach((b) => {
  if (b.type === "h1") {
    const label = b.numbered ? roman[++sec] + ". " : ""; sub = 0;
    cur.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: label + b.text, smallCaps: true, size: 20, font: FONT })] }));
  } else if (b.type === "h2") {
    const kids = b.runs ? b.runs.map((r) => run(r, { italics: true })) : [new TextRun({ text: b.text, italics: true, font: FONT })];
    cur.push(new Paragraph({ spacing: { before: 120, after: 60 }, children: [new TextRun({ text: letters[sub++] + ". ", italics: true, font: FONT }), ...kids] }));
  } else if (b.type === "p") {
    cur.push(para(b.runs.map((r) => run(r))));
  } else if (b.type === "enum") {
    b.items.forEach((it) => cur.push(new Paragraph({ numbering: { reference: "contrib", level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 0 }, children: it.map((r) => run(r)) })));
  } else if (b.type === "eq") {
    eqn++;
    const tabs = [{ type: TabStopType.CENTER, position: 2510 }, { type: TabStopType.RIGHT, position: COLW }];
    if (eqn === 1) {
      cur.push(new Paragraph({ tabStops: tabs, spacing: { before: 80, after: 80 }, children: [new TextRun({ text: "\tf(o, s; θ) → ŷ ∈ [1, 10]\t(1)", italics: false, font: FONT })] }));
    } else {
      const lines = [["Preserved", "if ŷ ≥ 7.5"], ["Partially preserved", "if 4.5 ≤ ŷ < 7.5"], ["Not preserved", "if ŷ < 4.5"]];
      lines.forEach((l, i) => cur.push(new Paragraph({ tabStops: [{ type: TabStopType.LEFT, position: 700 }, { type: TabStopType.LEFT, position: 1500 }, { type: TabStopType.LEFT, position: 3300 }, { type: TabStopType.RIGHT, position: COLW }],
        spacing: { before: i === 0 ? 60 : 0, after: i === 2 ? 80 : 0 },
        children: [new TextRun({ text: (i === 0 ? "\tδ(ŷ) =" : "\t") + "\t" + l[0] + "\t" + l[1] + (i === 1 ? "\t(2)" : ""), font: FONT })] })));
    }
  } else if (b.type === "float") {
    if (WIDE[b.id]) {
      flushTwoCol();
      sections.push({ properties: Object.assign({ type: SectionType.CONTINUOUS, column: { count: 1 } }, pageProps), children: WIDE[b.id]() });
    } else if (FLOATS[b.id]) cur.push(...FLOATS[b.id]());
  }
});
// references
const refs = [
  "D. Beauchemin, M. Albert-Rochette, R. Khoury, and P.-L. Déziel, “JUDGEBERT: Assessing legal meaning preservation between sentences,” in Proc. EMNLP, 2025, pp. 92–118.",
  "K. Papineni, S. Roukos, T. Ward, and W.-J. Zhu, “BLEU: A method for automatic evaluation of machine translation,” in Proc. ACL, 2002, pp. 311–318.",
  "M. Popović, “chrF: Character n-gram F-score for automatic MT evaluation,” in Proc. WMT, 2015, pp. 392–395.",
  "W. Xu, C. Napoles, E. Pavlick, Q. Chen, and C. Callison-Burch, “Optimizing statistical machine translation for text simplification,” TACL, vol. 4, pp. 401–415, 2016.",
  "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese BERT-networks,” in Proc. EMNLP-IJCNLP, 2019, pp. 3982–3992.",
  "T. Zhang, V. Kishore, F. Wu, K. Q. Weinberger, and Y. Artzi, “BERTScore: Evaluating text generation with BERT,” in Proc. ICLR, 2020.",
  "D. Beauchemin, H. Saggion, and R. Khoury, “MeaningBERT: Assessing meaning preservation between sentences,” Frontiers in Artificial Intelligence, vol. 6, 2023.",
  "Y. Liu, D. Iter, Y. Xu, S. Wang, R. Xu, and C. Zhu, “G-Eval: NLG evaluation using GPT-4 with better human alignment,” in Proc. EMNLP, 2023, pp. 2511–2522.",
  "A. Conneau et al., “Unsupervised cross-lingual representation learning at scale,” in Proc. ACL, 2020, pp. 8440–8451.",
  "S. Khanuja et al., “MuRIL: Multilingual representations for Indian languages,” arXiv:2103.10730, 2021.",
  "K. Krippendorff, Content Analysis: An Introduction to Its Methodology, 4th ed. Thousand Oaks, CA: SAGE, 2018.",
];
cur.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: "References", smallCaps: true, size: 20, font: FONT })] }));
refs.forEach((r, i) => cur.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 360, hanging: 360 }, spacing: { after: 30 },
  tabStops: [{ type: TabStopType.LEFT, position: 360 }], children: [new TextRun({ text: `[${i + 1}]\t${r}`, size: 16, font: FONT })] })));
flushTwoCol();

const d = new Document({
  creator: "CSET 346 Project Team", title: "Explainable Multilingual Legal Meaning Preservation Using JUDGEBERT",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: { config: [{ reference: "contrib", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1)", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 260 } } } }] }] },
  sections,
});
Packer.toBuffer(d).then((buf) => { fs.writeFileSync("LMP_IEEE_Paper.docx", buf); console.log("docx written", sections.length, "sections"); });
