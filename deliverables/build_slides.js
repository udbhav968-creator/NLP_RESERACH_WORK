const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/root/.claude/skills/synced/fca057c5-4ddc-4fc8-b8b3-46ddd9c4e49e_5ec7c671-af93-47e4-b04c-4ba01768dd7b/pptx/scripts/apply_theme.js");

const THEME = {
  name: "LegalInk",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A41", lt1: "FFFFFF", dk2: "2E4057", lt2: "EEF2F6",
    accent1: "C8892B", accent2: "2A7F7A", accent3: "B5452F", accent4: "5B7DB1", accent5: "8E9AAF", accent6: "4F8A3C",
    hlink: "2A7F7A", folHlink: "5B7DB1",
  },
};
const HEX = THEME.colors;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.title = "Explainable Multilingual Legal Meaning Preservation Using JUDGEBERT";
  pres.author = "CSET 346 Project Team";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ---------- layouts
  pres.defineSlideMaster({
    title: "TITLE_DARK",
    background: { color: C.text1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 1.05, w: 6.2, h: 1.9, fontSize: 32, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: C.background1 },
    margin: [0.5, 0.5, 0.45, 0.5],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.6, fontSize: 28, bold: true, color: C.text1, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
      { text: { text: "CSET 346 · NLP · Milestone 1", options: { x: 0.5, y: 5.25, w: 4, h: 0.25, fontSize: 9, color: C.accent5, margin: 0 } } },
    ],
    slideNumber: { x: 9.0, y: 5.25, w: 0.5, h: 0.25, fontSize: 9, color: HEX.accent5, align: "right" },
  });

  const I = {
    scale: await icon(fa.FaBalanceScale, HEX.accent1),
    scaleW: await icon(fa.FaBalanceScale, "FFFFFF"),
    gavel: await icon(fa.FaGavel, "FFFFFF"),
    ban: await icon(fa.FaBan, "FFFFFF"),
    filter: await icon(fa.FaFilter, "FFFFFF"),
    cut: await icon(fa.FaCut, "FFFFFF"),
    expand: await icon(fa.FaExpandArrowsAlt, "FFFFFF"),
    calc: await icon(fa.FaCalendarAlt, "FFFFFF"),
    users: await icon(fa.FaUserFriends, "FFFFFF"),
    plus: await icon(fa.FaPlusCircle, "FFFFFF"),
    db: await icon(fa.FaDatabase, "FFFFFF"),
    pen: await icon(fa.FaPenNib, "FFFFFF"),
    ruler: await icon(fa.FaRulerHorizontal, "FFFFFF"),
    brain: await icon(fa.FaBrain, "FFFFFF"),
    comment: await icon(fa.FaCommentDots, "FFFFFF"),
    chart: await icon(fa.FaChartBar, "FFFFFF"),
    lang: await icon(fa.FaLanguage, "FFFFFF"),
    check: await icon(fa.FaCheckCircle, HEX.accent6),
  };

  const circleIcon = (slide, img, x, y, d, fill, name) => {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name + "-circle" });
    const p = d * 0.25;
    slide.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + "-icon" });
  };
  const card = (slide, x, y, w, h, fill, name) =>
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" }, objectName: name });

  // =====================================================================  1. TITLE
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  s.addText("CSET 346 · NATURAL LANGUAGE PROCESSING · MILESTONE 1 REVIEW", { x: 0.5, y: 0.55, w: 7, h: 0.3, fontSize: 11, bold: true, color: C.accent1, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Explainable Multilingual Legal Meaning Preservation Using JUDGEBERT", { placeholder: "title" });
  s.addText("Does a simplified legal sentence still say the same thing in law? An English + Hindi extension of JUDGEBERT, with full experimental results (E1–E5)", {
    x: 0.5, y: 3.0, w: 6.2, h: 0.65, fontSize: 15, italic: true, color: "CADCEB", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.OVAL, { x: 7.35, y: 1.15, w: 1.9, h: 1.9, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "title-icon-circle" });
  s.addImage({ data: I.scaleW, x: 7.8, y: 1.6, w: 1.0, h: 1.0, objectName: "title-icon" });
  card(s, 0.5, 3.95, 9.0, 1.2, "24364F", "title-info-card");
  s.addText([
    { text: "Team (PID-__): ", options: { bold: true, color: HEX.accent1 } },
    { text: "Student Name 1 · Student Name 2 · Student Name 3", options: { color: "FFFFFF", breakLine: true } },
    { text: "Evaluators: ", options: { bold: true, color: HEX.accent1 } },
    { text: "Dr. Surabhi Solanki · Dr. Ankur", options: { color: "FFFFFF", breakLine: true } },
    { text: "Venue: ", options: { bold: true, color: HEX.accent1 } },
    { text: "Lab BLA-211-B · 14 October 2026 · 10:00 AM – 12:00 PM", options: { color: "FFFFFF" } },
  ], { x: 0.75, y: 4.02, w: 8.6, h: 1.05, fontSize: 13, valign: "middle", margin: 0, paraSpaceAfter: 2, isTextBox: true });
  s.addNotes("Good morning. Our project asks a simple question with legal consequences: when a legal sentence is simplified, is its legal meaning still the same? We extend the JUDGEBERT metric (EMNLP 2025), which was built for French insurance text, to English and Hindi and to a new legal domain, and we add explanations of what changed.");

  // =====================================================================  2. PROBLEM DOMAIN
  pres.addSection({ title: "Problem" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
  s.addText("Problem domain: plain-language law", { placeholder: "title" });
  s.addText([
    { text: "Legal simplification", options: { bold: true, color: HEX.dk1, breakLine: true } },
    { text: "Insurance policies and rent agreements are rewritten in plain language so citizens can read them.", options: { breakLine: true } },
    { text: "The risk", options: { bold: true, color: HEX.dk1, breakLine: true } },
    { text: "A one-word edit can flip a duty, drop a condition or change a deadline, while the text still looks almost the same.", options: { breakLine: true } },
    { text: "The gap", options: { bold: true, color: HEX.dk1, breakLine: true } },
    { text: "Generic similarity scores reward surface overlap, not legal effect, and none exist for Hindi legal text.", options: {} },
  ], { x: 0.5, y: 1.05, w: 3.9, h: 3.9, fontSize: 14, color: C.text2, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });

  card(s, 4.7, 1.05, 4.8, 3.95, C.background2, "example-card");
  s.addText("Original (insurance policy)", { x: 4.9, y: 1.15, w: 4.4, h: 0.28, fontSize: 11, bold: true, color: C.accent5, margin: 0, isTextBox: true });
  s.addText("“The policy does not cover damage … caused by wear and tear, gradual deterioration, or inherent defect.”", { x: 4.9, y: 1.43, w: 4.4, h: 0.6, fontSize: 12, italic: true, color: C.text1, margin: 0, isTextBox: true });
  // two simplifications
  const rowY = [2.15, 3.2];
  const rows2 = [
    { lab: "A · Faithful", txt: "“The policy does not pay for damage … caused by normal wear and tear …”", cos: "0.85", lmp: "10", col: HEX.accent6 },
    { lab: "B · Contradiction", txt: "“The policy pays for damage … caused by normal wear and tear …”", cos: "0.84", lmp: "1", col: HEX.accent3 },
  ];
  rows2.forEach((r, i) => {
    card(s, 4.9, rowY[i], 4.4, 0.92, "FFFFFF", "simp-" + i);
    s.addText(r.lab, { x: 5.05, y: rowY[i] + 0.06, w: 2.6, h: 0.26, fontSize: 11, bold: true, color: r.col, margin: 0, isTextBox: true });
    s.addText(r.txt, { x: 5.05, y: rowY[i] + 0.32, w: 2.75, h: 0.55, fontSize: 11, color: C.text1, margin: 0, valign: "top", isTextBox: true });
    s.addText([{ text: "cosine ", options: { fontSize: 10, color: HEX.accent5 } }, { text: r.cos, options: { fontSize: 18, bold: true, color: HEX.dk2 } }],
      { x: 7.85, y: rowY[i] + 0.1, w: 1.35, h: 0.36, align: "right", margin: 0, isTextBox: true });
    s.addText([{ text: "LMP label ", options: { fontSize: 10, color: HEX.accent5 } }, { text: r.lmp, options: { fontSize: 18, bold: true, color: r.col } }],
      { x: 7.85, y: rowY[i] + 0.5, w: 1.35, h: 0.36, align: "right", margin: 0, isTextBox: true });
  });
  s.addText("Sentence-embedding cosine separates them by 0.01; the legal meaning is opposite. Same pattern in Hindi (0.92 vs 0.92).", {
    x: 4.9, y: 4.22, w: 4.4, h: 0.7, fontSize: 11, color: C.accent3, bold: true, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Plain-language rewriting of contracts and policies is now common, often done by LLMs. Here is a real pair from our dataset. Version B removes a single word, 'not', and turns an exclusion into coverage. A generic sentence-embedding similarity (WordLlama static embeddings) gives 0.85 and 0.84 — practically identical — while a lawyer would score A as 10 and B as 1. This is the problem we target.");

  // extra icons
  I.cogs = await icon(fa.FaCogs, "FFFFFF");
  I.flask = await icon(fa.FaFlask, "FFFFFF");
  I.warn = await icon(fa.FaExclamationTriangle, "FFFFFF");
  I.sigma = await icon(fa.FaSuperscript, "FFFFFF");
  const line = (slide, x1, y1, x2, y2, name, color = HEX.accent5) =>
    slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
      flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 1.5, endArrowType: "triangle" }, objectName: name });
  const lineNA = (slide, x1, y1, x2, y2, name, color = HEX.accent5) =>
    slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
      line: { color, width: 1.5 }, objectName: name });

  // =====================================================================  3. PROBLEM ANALYSIS + FORMULATION
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
  s.addText("Problem analysis and task formulation", { placeholder: "title" });
  s.addText("Error taxonomy: small edits, large legal effect", { x: 0.5, y: 1.0, w: 5.2, h: 0.3, fontSize: 13, bold: true, color: C.text1, margin: 0, isTextBox: true });
  const cats = [
    [I.gavel, "Modality", "must → may"],
    [I.ban, "Negation", "not cover → cover"],
    [I.filter, "Condition", "“if licensed” cut"],
    [I.cut, "Exception", "“except …” cut"],
    [I.expand, "Scope", "others → anyone"],
    [I.calc, "Number / date", "7 days → 30 days"],
    [I.users, "Party swap", "tenant → landlord"],
    [I.plus, "Hallucination", "adds a penalty"],
  ];
  cats.forEach((c, i) => {
    const x = 0.5 + (i % 4) * 1.32, y = 1.38 + Math.floor(i / 4) * 1.22;
    card(s, x, y, 1.22, 1.12, C.background2, "cat-card-" + i);
    circleIcon(s, c[0], x + 0.1, y + 0.1, 0.38, i < 2 ? HEX.accent3 : HEX.accent2, "cat-" + i);
    s.addText(c[1], { x: x + 0.1, y: y + 0.5, w: 1.05, h: 0.26, fontSize: 11, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText(c[2], { x: x + 0.1, y: y + 0.76, w: 1.08, h: 0.26, fontSize: 10, italic: true, color: C.text2, margin: 0, isTextBox: true });
  });
  s.addText([
    { text: "Analysis. ", options: { bold: true, color: HEX.accent1 } },
    { text: "Every category preserves most tokens, so overlap and embedding scores remain high. The signal is local, legally typed and language-specific, so it must be learned from legal judgements and made explicit.", options: { color: HEX.dk2 } },
  ], { x: 0.5, y: 3.95, w: 5.2, h: 1.1, fontSize: 12, margin: 0, valign: "top", isTextBox: true });

  card(s, 5.95, 1.0, 3.55, 4.05, C.text1, "formal-card");
  s.addText("Formal task definition", { x: 6.15, y: 1.1, w: 3.2, h: 0.35, fontSize: 14, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  const fdef = [
    ["Input", "original o, simplification s; language ℓ ∈ {en, hi}; domain d ∈ {insurance, tenancy}"],
    ["Score", "f(o, s; θ) → ŷ ∈ [1, 10], the LMP score"],
    ["Decide", "δ(ŷ): Preserved if ŷ ≥ 7.5; Partial if 4.5 ≤ ŷ < 7.5; else Not preserved"],
    ["Explain", "g(o, s) → error type e ∈ E (|E| = 10) and rationale r"],
    ["Goal", "maximise r(ŷ, y), minimise RMSE(ŷ, y) against human LMP y"],
  ];
  fdef.forEach((f, i) => {
    const y = 1.55 + i * 0.68;
    s.addText(f[0], { x: 6.15, y, w: 0.8, h: 0.6, fontSize: 11, bold: true, color: "9FB3C8", margin: 0, valign: "top", isTextBox: true });
    s.addText(f[1], { x: 6.95, y, w: 2.45, h: 0.62, fontSize: 11, color: "FFFFFF", margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("We analysed where legal meaning is lost and derived an eight-category taxonomy from the project brief. Each is a small surface edit with a large legal effect, which is why generic similarity fails. We then formalise the task: a scoring function f-theta maps an original and a simplification to an LMP score between 1 and 10; a decision rule turns the score into Preserved, Partially or Not preserved; and an explanation function returns the error type and a short rationale. Success is measured by correlation and RMSE against human LMP scores.");

  // =====================================================================  4. LITERATURE REVIEW
  pres.addSection({ title: "Review" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Review" });
  s.addText("Review of existing systems", { placeholder: "title" });
  const hd = (t, al = "left") => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk1 }, valign: "middle", align: al } });
  const tx = (t, o = {}) => ({ text: t, options: Object.assign({ color: HEX.dk1, valign: "middle" }, o) });
  const yes = () => tx("Yes", { color: HEX.accent6, bold: true, align: "center" });
  const no = () => tx("No", { color: HEX.accent3, bold: true, align: "center" });
  const part = (t = "Part") => tx(t, { color: HEX.accent1, bold: true, align: "center" });
  const lit = [
    [hd("Year"), hd("System"), hd("Core idea"), hd("Limitation for legal meaning"), hd("Legal", "center"), hd("Hindi", "center"), hd("Explains", "center")],
    [tx("2002"), tx("BLEU", { bold: true }), tx("n-gram precision vs reference"), tx("Rewards copying; ignores a lost “not”"), no(), part(), no()],
    [tx("2015"), tx("chrF", { bold: true }), tx("character n-gram F-score"), tx("Morphology-robust but surface-only"), no(), part(), no()],
    [tx("2016"), tx("SARI", { bold: true }), tx("add / keep / delete vs references"), tx("Scores simplicity, needs references"), no(), no(), no()],
    [tx("2019–20"), tx("SBERT, BERTScore", { bold: true }), tx("contextual embedding similarity"), tx("“covers” ≈ “does not cover” (slide 2)"), no(), part(), no()],
    [tx("2023"), tx("MeaningBERT", { bold: true }), tx("learned meaning regressor"), tx("General domain; no legal categories"), no(), no(), no()],
    [tx("2023"), tx("LLM-as-judge (G-Eval)", { bold: true }), tx("prompted LLM rating + reasoning"), tx("Costly, uncalibrated, not reproducible"), part(), part(), yes()],
    [tx("2025", { color: HEX.accent2, bold: true }), tx("JUDGEBERT", { bold: true, color: HEX.accent2 }), tx("BERT regressor on FrJUDGE"), tx("French insurance only; no reasons"), yes(), no(), no()],
  ];
  s.addTable(lit, { x: 0.5, y: 0.98, w: 9.0, colW: [0.68, 1.62, 2.12, 2.6, 0.6, 0.6, 0.78], fontSize: 10.5, rowH: 0.37,
    border: { type: "solid", pt: 0.75, color: "D5DCE5" }, fill: { color: "FFFFFF" }, margin: 0.04, objectName: "lit-table" });
  card(s, 0.5, 4.15, 9.0, 0.5, "E3F0EE", "gap-callout");
  s.addText([{ text: "Research gap  ", options: { bold: true, color: HEX.accent2 } },
    { text: "No calibrated, explainable legal-meaning metric exists for Hindi, or beyond French insurance text.", options: { color: HEX.dk1 } }],
    { x: 0.65, y: 4.15, w: 8.7, h: 0.5, fontSize: 13, margin: 0, valign: "middle", isTextBox: true });
  s.addText("Papineni+ 2002 · Popović 2015 · Xu+ 2016 · Reimers & Gurevych 2019 · Zhang+ 2020 · Beauchemin+ 2023 · Liu+ 2023 · Beauchemin+ 2025 (EMNLP)", {
    x: 0.5, y: 4.82, w: 9.0, h: 0.3, fontSize: 10, color: C.accent5, margin: 0, isTextBox: true });
  s.addNotes("This table reviews eight representative systems in chronological order. Lexical metrics — BLEU, chrF, SARI — measure surface overlap. Embedding metrics like SBERT and BERTScore measure general semantic closeness, and we showed on slide 2 they cannot separate 'covers' from 'does not cover'. MeaningBERT learns meaning preservation but is not legal. LLM judges explain, but are costly and not reproducible. JUDGEBERT is the only legal-aware metric, but it is limited to French insurance and gives no reasons. That defines our research gap.");
  const GLOBAL_TITLES = {
    e1: "E1: legal-aware models beat generic metrics",
    e1verdict: "H1 partly supported. LegalDiff-GBR is best on every metric (r 0.60, RMSE 2.94, Not-preserved F1 0.61) and is stable across languages (EN 0.60, HI 0.59). The best generic metric, chrF, reaches only r 0.37; embedding similarity drops from 0.38 (EN) to 0.21 (HI). The text-only encoder trained from scratch fails (r 0.12); fusing LegalDiff lifts it to 0.44, so pretraining is the missing piece.",
    e1notes: "Experiment 1 compares three generic similarity baselines with three learned LMP models under 5-fold cross-validation grouped by clause, so the English and Hindi versions of a clause never sit in different folds. The legal-difference model LegalDiff-GBR is best on every metric: Pearson 0.60 against 0.37 for chrF, the strongest generic metric, and it is the only system that detects 'Not preserved' pairs reliably (F1 0.61). Generic baselines are calibrated to the 1–10 scale but cluster in the middle, so their decision F1 is near zero. The chart is Experiment 2's per-language view: embedding-based similarity loses almost half its correlation on Hindi, while LegalDiff stays at about 0.6 in both languages. Our JUDGEBERT-style encoder trained from scratch, without pretrained weights, does not learn on its own — r 0.12 — but fusing LegalDiff lifts it to 0.44. This tells us the architecture works when it has legal signal and that a pretrained multilingual encoder is the key next step.",
    e2: "E2–E4: transfer and sanity checks",
    e2verdict: "H2 supported for LegalDiff: zero-shot EN→HI r 0.48, HI→EN 0.54; domain transfer costs ≤ 0.06. On human-labelled FrJUDGE, models trained only on EnHi reach r 0.56–0.59 while embedding cosine is negative. H3 supported: augmented models score identical ≈ 10, unrelated ≈ 1.2–1.7; embedding cosine rates unrelated Hindi pairs 6.6 / 10.",
    e2notes: "Left, Experiment 2: models trained on English only and tested on Hindi, and the reverse, on held-out clauses. LegalDiff transfers almost without loss — 0.48 and 0.54 — because its features are defined for both languages, while embedding cosine collapses to 0.04 on Hindi. Right, Experiment 3: training on insurance and testing on tenancy, or the reverse, costs at most 0.06 in correlation. The FrJUDGE rows are the strongest evidence: these are real human LMP judgements from the base paper, in French. Models trained only on our English–Hindi data reach 0.56 to 0.59, above every generic metric, and embedding cosine is negatively correlated. Bottom, Experiment 4: the sanity checks from JUDGEBERT. Our augmented models give identical pairs about 10 and unrelated pairs between 1.2 and 1.7, whereas generic embeddings give unrelated Hindi sentences 6.6 out of 10 — a clear failure.",
    e5: "E5: error analysis, explanations, conclusion",
    bestModel: "LegalDiff-GBR",
    examples: [
      "Correct · HI · Negation (gold 1). “…आपूर्ति… नहीं काटेगा” → “…काट सकता है”. Emb. cos 7.0 | ours 4.5 → NEGATION: “negation removed, reversing the rule”.",
      "Correct · EN · Number (gold 2). Deductible Rs 5,000 → Rs 50,000. Emb. cos 6.6 | ours 5.3 → NUMBER: “Amount changed: 5000 → 50000”.",
      "Missed · EN · Negation (gold 1). “does not cover” → “pays for”. Emb. cos 6.1 | ours 8.9 → missed: polarity flipped by a verb change, not by “not”.",
    ],
    conclusion: [
      { text: "Conclusion", options: { bold: true, color: HEX.accent1, breakLine: true } },
      { text: "Generic similarity is not a legal-meaning metric: r ≤ 0.37; fails on Hindi and sanity checks.", options: { bullet: { indent: 10 }, breakLine: true } },
      { text: "Legal-difference modelling is the strongest, language-stable signal: r 0.60; FrJUDGE 0.56.", options: { bullet: { indent: 10 }, breakLine: true } },
      { text: "The JUDGEBERT-style encoder needs pretraining: r 0.12 alone, 0.44 with LegalDiff.", options: { bullet: { indent: 10 }, breakLine: true } },
      { text: "Caveat: silver rubric labels; human double annotation is next.", options: { bullet: { indent: 10 }, italic: true } },
    ],
    next: "Next (M2–M3): human annotation + α → XLM-R / MuRIL fine-tune → IEEE paper + GitHub",
    e5notes: "Experiment 5 looks inside the errors. The chart shows the mean predicted score for each gold error type. The gold scores, in dark, are low for every error type. The generic embedding score, in grey, stays around 6 to 7 for every type — it cannot tell a faithful rewrite from a negation or a changed number. Our LegalDiff model follows the gold pattern much more closely. The explanation module detects that a legal error exists with F1 0.79 and names the exact error type in 40 percent of error cases, across eleven classes. The cards show two correct explanations, one in Hindi, and one honest failure: when 'does not cover' becomes 'pays for', the negation is removed by changing the verb, which our lexicon does not capture. That points to the need for a pretrained encoder. In conclusion: generic similarity is not a legal-meaning metric, explicit legal-difference modelling is the strongest signal in both languages and even transfers to the French human-labelled data, and the JUDGEBERT-style encoder needs pretraining. The main caveat is that our labels are rubric-based silver labels; human double annotation is the next milestone. Thank you.",
  };
  // =====================================================================  5. BASE PAPER, GAPS, OBJECTIVES
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Review" });
  s.addText("Base paper, research gaps and objectives", { placeholder: "title" });
  card(s, 0.5, 0.98, 4.5, 0.82, C.text1, "jb-strip");
  s.addImage({ data: I.scale, x: 0.65, y: 1.13, w: 0.5, h: 0.5, objectName: "jb-icon" });
  s.addText([
    { text: "JUDGEBERT (EMNLP 2025): ", options: { bold: true, color: HEX.accent1 } },
    { text: "297 French insurance pairs, 5 annotators each, LMP 1–10; BERT regressor + identical / unrelated augmentation", options: { color: "FFFFFF" } },
  ], { x: 1.28, y: 1.0, w: 3.65, h: 0.78, fontSize: 10.5, margin: 0, valign: "middle", isTextBox: true });
  const gaps = [
    ["French only", "English + Hindi (Devanagari)"],
    ["Insurance only", "+ tenancy / rent-agreement law"],
    ["297 pairs", "320 new pairs + 320 sanity pairs"],
    ["No out-of-domain test", "cross-lingual, cross-domain, FrJUDGE"],
    ["Score only", "decision + error type + rationale"],
  ];
  gaps.forEach((g, i) => {
    const y = 1.95 + i * 0.62;
    card(s, 0.5, y, 1.8, 0.52, "F7E6E1", "gap-" + i);
    s.addText(g[0], { x: 0.6, y, w: 1.65, h: 0.52, fontSize: 11, bold: true, color: C.accent3, margin: 0, valign: "middle", isTextBox: true });
    s.addShape(pres.shapes.RIGHT_ARROW, { x: 2.37, y: y + 0.16, w: 0.22, h: 0.2, fill: { color: HEX.accent5 }, line: { type: "none" }, objectName: "gap-arrow-" + i });
    card(s, 2.66, y, 2.34, 0.52, "E3F0EE", "ext-" + i);
    s.addText(g[1], { x: 2.76, y, w: 2.2, h: 0.52, fontSize: 11, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
  });
  card(s, 5.25, 0.98, 4.25, 1.5, "FBF3E6", "rq-card");
  s.addText([
    { text: "Research question  ", options: { bold: true, color: HEX.accent1 } },
    { text: "How well can a JUDGEBERT-based model assess legal meaning preservation in Hindi and a new legal domain, and does it beat generic semantic similarity?", options: { color: HEX.dk1, breakLine: true } },
    { text: "Hypotheses  ", options: { bold: true, color: HEX.accent2, fontSize: 10 } },
    { text: "H1 legal-aware models beat generic similarity · H2 they transfer across language and domain · H3 augmentation anchors the 1–10 scale", options: { color: HEX.dk2, fontSize: 10 } },
  ], { x: 5.4, y: 1.02, w: 3.98, h: 1.42, fontSize: 11, margin: 0, valign: "middle", paraSpaceAfter: 4, isTextBox: true });
  const objs = [
    ["O1", "Build EnHi-LMP: ≥300 EN/HI pairs, 2 domains, rubric + double annotation"],
    ["O2", "Benchmark ≥2 generic similarity baselines, calibrated to 1–10"],
    ["O3", "Train a multilingual JUDGEBERT-style regressor with LegalDiff fusion"],
    ["O4", "Test transfer: EN↔HI, insurance↔tenancy, EnHi→FrJUDGE; sanity checks"],
    ["O5", "Explain each score: decision, legal error type, rationale (P / R / F1)"],
  ];
  objs.forEach((o, i) => {
    const y = 2.58 + i * 0.5;
    s.addShape(pres.shapes.OVAL, { x: 5.25, y: y + 0.04, w: 0.4, h: 0.4, fill: { color: i === 2 ? HEX.accent1 : HEX.accent2 }, line: { type: "none" }, objectName: "obj-dot-" + i });
    s.addText(o[0], { x: 5.25, y: y + 0.04, w: 0.4, h: 0.4, fontSize: 10.5, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(o[1], { x: 5.75, y, w: 3.75, h: 0.48, fontSize: 11, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
  });
  s.addNotes("Our base paper, JUDGEBERT, defines Legal Meaning Preservation and releases FrJUDGE: 297 French insurance pairs, each scored 1 to 10 by five annotators — we verified this in the released data. Its model is a BERT regressor trained with identical and unrelated pairs as augmentation. The paper's own limitations — one language, one domain, small data, no out-of-domain test, no explanation — become our five extensions. The research question asks whether the approach transfers to Hindi and a new domain and beats generic similarity, and five objectives operationalise it.");

  // =====================================================================  6. METHODOLOGY
  pres.addSection({ title: "Proposal" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Proposal" });
  s.addText("Methodology: data, model and training", { placeholder: "title" });
  const box = (x, y, w, h, head, body, fill, headCol, name) => {
    card(s, x, y, w, h, fill, name);
    s.addText(head, { x: x + 0.06, y: y + 0.05, w: w - 0.12, h: 0.25, fontSize: 10.5, bold: true, color: headCol, margin: 0, align: "center", isTextBox: true });
    s.addText(body, { x: x + 0.06, y: y + 0.3, w: w - 0.12, h: h - 0.33, fontSize: 9.5, color: HEX.dk2, margin: 0, align: "center", valign: "top", isTextBox: true });
  };
  box(0.5, 0.98, 1.4, 0.8, "Input pair", "original o\nsimplification s", C.background2, HEX.dk1, "a-in");
  box(2.15, 0.98, 1.6, 0.8, "Cross-encoding", "[CLS] o [SEP] s [SEP]\nshared EN/HI BPE", C.background2, HEX.dk1, "a-tok");
  box(4.0, 0.98, 1.75, 0.8, "Transformer encoder", "self-attention across o and s", "FBF3E6", HEX.accent1, "a-enc");
  box(6.0, 0.98, 1.4, 0.8, "Pooling", "h_CLS, u−v, u⊙v, |u−v|", C.background2, HEX.dk1, "a-pool");
  box(2.15, 2.0, 5.25, 0.62, "LegalDiff extractor (EN / HI lexicons) → 19 features", "modality · negation · numbers · durations · parties · conditions · exceptions · scope", "E3F0EE", HEX.accent2, "a-ld");
  card(s, 7.65, 0.98, 1.85, 1.64, C.text1, "a-fuse");
  s.addText([
    { text: "Fusion head", options: { bold: true, color: HEX.accent1, breakLine: true } },
    { text: "MLP → ŷ = 1 + 9·σ(z)", options: { bold: true, breakLine: true } },
    { text: "δ(ŷ) → decision", options: { breakLine: true } },
    { text: "explainer → type + reason", options: {} },
  ], { x: 7.72, y: 1.03, w: 1.72, h: 1.55, fontSize: 10, color: "FFFFFF", align: "center", valign: "middle", margin: 0, paraSpaceAfter: 3, isTextBox: true });
  line(s, 1.9, 1.38, 2.15, 1.38, "ar1"); line(s, 3.75, 1.38, 4.0, 1.38, "ar2"); line(s, 5.75, 1.38, 6.0, 1.38, "ar3"); line(s, 7.4, 1.38, 7.65, 1.38, "ar4");
  lineNA(s, 1.2, 1.78, 1.2, 2.31, "ar5a"); line(s, 1.2, 2.31, 2.15, 2.31, "ar5b"); line(s, 7.4, 2.31, 7.65, 2.31, "ar6");

  const cols = [
    ["EnHi-LMP dataset", [
      "80 clauses: 40 insurance, 40 tenancy",
      "× EN + parallel HI × (faithful, 1-error)",
      "= 320 pairs; 10 error types",
      "+160 identical, +160 unrelated (held out)",
      "Labels: rubric LMP 1–10 (silver)"]],
    ["Annotation protocol", [
      "Written 1–10 rubric with anchors",
      "2 annotators score independently",
      "Adjudicate gaps ≥ 3 points",
      "Report Krippendorff’s α",
      "Decision: ≥7.5 / 4.5–7.5 / <4.5"]],
    ["Training set-up (run)", [
      "MSE loss, AdamW + one-cycle, 40 epochs",
      "Augment: identical→10, unrelated→1",
      "5-fold CV grouped by clause, 3 seeds",
      "Encoder: 2-layer, from scratch (CPU)",
      "Next: fine-tune XLM-R / MuRIL on GPU"]],
  ];
  cols.forEach((c, i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 2.85, 2.9, 2.22, i === 2 ? "FBF3E6" : C.background2, "mcol-" + i);
    s.addText(c[0], { x: x + 0.14, y: 2.92, w: 2.65, h: 0.3, fontSize: 12, bold: true, color: i === 2 ? HEX.accent1 : HEX.accent2, margin: 0, isTextBox: true });
    s.addText(c[1].map((t, k) => ({ text: t, options: { bullet: { indent: 10 }, breakLine: k < c[1].length - 1 } })),
      { x: x + 0.14, y: 3.3, w: 2.7, h: 1.72, fontSize: 11.5, color: HEX.dk1, margin: 0, valign: "top", paraSpaceAfter: 6, isTextBox: true });
  });
  s.addNotes("Methodology. Like JUDGEBERT, the model reads the original and the simplification together as one cross-encoded sequence, so attention can compare them token by token. We pool the CLS vector together with difference and product features of the two sentences. In parallel the LegalDiff extractor computes 19 interpretable legal-difference features in English and Hindi. A fusion head regresses the score on the 1–10 scale; a threshold rule gives the decision and the explainer the error type and reason. The dataset has 320 pairs plus 320 held-out sanity pairs. For this milestone the encoder is a 2-layer transformer trained from scratch on CPU, because pretrained-model downloads were unavailable; the GPU fine-tune of XLM-R or MuRIL is the next step.");
  // =====================================================================  9. ALGORITHMS + METRICS
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Proposal" });
  s.addText("Relevance of algorithms and evaluation metrics", { placeholder: "title" });
  const th = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk1 }, valign: "middle" } });
  const tc = (t, b) => ({ text: t, options: { color: HEX.dk1, bold: !!b, valign: "middle" } });
  const alg = [
    [th("Technique"), th("Role"), th("Why it is the right choice here")],
    [tc("chrF", 1), tc("Lexical baseline"), tc("Character level, so robust to Hindi inflection and spelling variants")],
    [tc("Embedding cosine, BERTScore-style F1", 1), tc("Semantic baselines"), tc("Standard ‘generic similarity’ the brief requires us to beat")],
    [tc("Gradient-boosted trees on LegalDiff", 1), tc("Best LMP regressor"), tc("Learns non-linear interactions of 19 sparse legal features from little data")],
    [tc("Cross-encoder Transformer", 1), tc("JUDGEBERT-style model"), tc("Attention aligns o and s token by token; next: XLM-R / MuRIL")],
    [tc("Regression head, MSE, σ-scaling", 1), tc("LMP in [1, 10]"), tc("Same formulation as JUDGEBERT, so results are directly comparable")],
    [tc("Identical / unrelated augmentation", 1), tc("Scale anchoring"), tc("Teaches both ends of the scale; enables the E4 sanity test")],
    [tc("LegalDiff features + rule explainer", 1), tc("Explainability"), tc("Typed, auditable signal for each error category in EN and HI")],
  ];
  s.addTable(alg, { x: 0.5, y: 0.98, w: 9.0, colW: [2.75, 1.6, 4.65], fontSize: 10.5, rowH: 0.34,
    border: { type: "solid", pt: 0.75, color: "D5DCE5" }, fill: { color: "FFFFFF" }, margin: 0.05, objectName: "algo-table" });
  const mets = [
    ["Pearson r / Spearman ρ", "r = cov(ŷ, y) / (σŷ σy)\nρ = r on ranks", "agreement with human LMP"],
    ["RMSE / MAE", "RMSE = √(Σ(ŷᵢ − yᵢ)² / n)\nMAE = Σ|ŷᵢ − yᵢ| / n", "error on the 1–10 scale"],
    ["Macro-F1", "F1 = 2PR / (P + R)\naveraged over classes", "decision and error-type quality"],
    ["Sanity rates", "% identical with ŷ ≥ 9\n% unrelated with ŷ ≤ 2", "scale calibration (E4)"],
  ];
  mets.forEach((m, i) => {
    const x = 0.5 + i * 2.28;
    card(s, x, 3.9, 2.16, 1.17, C.text1, "met-" + i);
    s.addText(m[0], { x: x + 0.1, y: 3.96, w: 1.96, h: 0.26, fontSize: 11, bold: true, color: HEX.accent1, margin: 0, isTextBox: true });
    s.addText(m[1], { x: x + 0.1, y: 4.24, w: 1.98, h: 0.52, fontSize: 11, color: "FFFFFF", margin: 0, valign: "top", isTextBox: true });
    s.addText(m[2], { x: x + 0.1, y: 4.78, w: 1.96, h: 0.25, fontSize: 9.5, italic: true, color: "9FB3C8", margin: 0, isTextBox: true });
  });
  s.addNotes("Each technique is justified by the problem. chrF works at character level, which suits Hindi morphology. Embedding cosine and BERTScore-style alignment are the generic similarity the brief asks us to beat. Gradient-boosted trees learn non-linear combinations of the sparse LegalDiff features from only a few hundred pairs, which is why that model is strongest today. The cross-encoder lets attention compare the two sentences token by token; its pretrained version will use XLM-R, which covers 100 languages, or MuRIL, trained on 17 Indian languages. The regression formulation matches JUDGEBERT, so our numbers are comparable. Augmentation anchors the scale, and LegalDiff makes predictions auditable. The bottom row defines the evaluation metrics we report: correlation, error, F1 and sanity rates.");

  // =====================================================================  RESULTS (data-driven)
  const fs = require("fs");
  const RD = "/home/claude/lmp/results/";
  const E1 = JSON.parse(fs.readFileSync(RD + "exp1_summary.json"));
  const E2 = JSON.parse(fs.readFileSync(RD + "exp2_crosslingual.json"));
  const E3 = JSON.parse(fs.readFileSync(RD + "exp3_domain.json"));
  const E5 = JSON.parse(fs.readFileSync(RD + "exp5_explain.json"));
  const ROWS5 = JSON.parse(fs.readFileSync(RD + "exp5_rows.json"));
  const NAMES = {
    "chrF (lexical)": "chrF", "WordLlama cosine (semantic)": "Embedding cosine", "Token-alignment F1 (BERTScore-style)": "Token-align F1",
    "LegalDiff-GBR": "LegalDiff-GBR", "ML-JudgeBERT": "ML-JudgeBERT (text)", "ML-JudgeBERT+LegalDiff": "ML-JudgeBERT + LegalDiff",
  };
  const ORDER = Object.keys(NAMES);
  const BASE = ORDER.slice(0, 3), LEARN = ORDER.slice(3);
  const f2 = (v) => (v === undefined || v === null || isNaN(v)) ? "–" : Number(v).toFixed(2);
  const mean = (o) => Array.isArray(o) ? o[0] : o;
  const sd = (o) => Array.isArray(o) ? o[1] : 0;
  const thR = (t, al = "center") => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk1 }, valign: "middle", align: al } });
  const tdR = (t, o = {}) => ({ text: t, options: Object.assign({ color: HEX.dk1, valign: "middle", align: "center" }, o) });

  // ---------------- 8. E1 + E2 per-language
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(GLOBAL_TITLES.e1, { placeholder: "title" });
  const mcols = [["pearson", "r ↑", 1], ["spearman", "ρ ↑", 1], ["rmse", "RMSE ↓", -1], ["mae", "MAE ↓", -1], ["f1_decision", "Dec. F1 ↑", 1], ["f1_notpreserved", "NP-F1 ↑", 1]];
  const best = {};
  mcols.forEach(([k, , dir]) => { best[k] = ORDER.map((m) => mean(E1.overall[m].all[k])).reduce((a, b) => dir > 0 ? Math.max(a, b) : Math.min(a, b)); });
  const t1 = [[thR("System (5-fold grouped CV, n = 320)", "left"), ...mcols.map((c) => thR(c[1]))]];
  ORDER.forEach((m, i) => {
    const row = [tdR(NAMES[m], { align: "left", bold: i >= 3, color: i >= 3 ? HEX.accent2 : HEX.dk1, fill: { color: i === 3 ? "E3F0EE" : "FFFFFF" } })];
    mcols.forEach(([k]) => {
      const v = mean(E1.overall[m].all[k]); const isB = Math.abs(v - best[k]) < 1e-9;
      const txt = f2(v) + (i >= 3 && k === "pearson" ? " ±" + f2(sd(E1.overall[m].all[k])).replace(/^0/, "") : "");
      row.push(tdR(txt, { bold: isB, color: isB ? HEX.accent2 : HEX.dk1, fill: { color: i === 3 ? "E3F0EE" : "FFFFFF" } }));
    });
    t1.push(row);
  });
  s.addTable(t1, { x: 0.5, y: 0.98, w: 5.55, colW: [1.95, 0.62, 0.55, 0.62, 0.55, 0.66, 0.6], fontSize: 10, rowH: 0.36,
    border: { type: "solid", pt: 0.75, color: "D5DCE5" }, margin: 0.04, objectName: "e1-table" });
  s.addText("Learned models: mean ± s.d. over 3 seeds. Baselines calibrated to 1–10 on training folds. Dec. F1 = macro-F1 of the 3-way decision; NP-F1 = F1 for ‘Not preserved’.", {
    x: 0.5, y: 3.58, w: 5.55, h: 0.42, fontSize: 9.5, italic: true, color: C.accent5, margin: 0, isTextBox: true });
  // per-language chart
  const shortN = ["chrF", "Emb. cos", "Tok-F1", "LD-GBR", "MLJB text", "MLJB+LD"];
  s.addChart(pres.charts.BAR, [
    { name: "English", labels: shortN, values: ORDER.map((m) => mean(E1.by_lang[m].en.pearson)) },
    { name: "Hindi", labels: shortN, values: ORDER.map((m) => mean(E1.by_lang[m].hi.pearson)) },
  ], { x: 6.2, y: 0.95, w: 3.35, h: 3.1, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent4, HEX.accent1],
    showTitle: true, title: "E2: Pearson r by language", titleFontSize: 11, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 7, dataLabelColor: HEX.dk2, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 8, catAxisLabelFontFace: "+mn-lt", catAxisLabelRotate: 0,
    valAxisHidden: true, valAxisMinVal: Math.min(0, ...ORDER.map((m) => Math.min(mean(E1.by_lang[m].en.pearson), mean(E1.by_lang[m].hi.pearson)))) , valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 9, legendFontFace: "+mn-lt", legendColor: HEX.dk2, barGapWidthPct: 60, objectName: "e2-lang-chart" });
  card(s, 0.5, 4.12, 9.0, 0.95, C.text1, "e1-verdict");
  s.addText(GLOBAL_TITLES.e1verdict, { x: 0.68, y: 4.15, w: 8.65, h: 0.89, fontSize: 11.5, color: "FFFFFF", margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(GLOBAL_TITLES.e1notes);

  // ---------------- 9. E2 transfer, E3 domain/FrJUDGE, E4 sanity
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(GLOBAL_TITLES.e2, { placeholder: "title" });
  const tcols = ["chrF (lexical)", "WordLlama cosine (semantic)", "LegalDiff-GBR", "ML-JudgeBERT+LegalDiff"];
  const tnames = ["chrF", "Emb. cos", "LD-GBR", "MLJB+LD"];
  const mkTable = (title, keys, labels, obj, x, y, w, name) => {
    s.addText(title, { x, y, w, h: 0.28, fontSize: 11.5, bold: true, color: C.text1, margin: 0, isTextBox: true });
    const t = [[thR("Train → test", "left"), ...tnames.map((n) => thR(n))]];
    keys.forEach((k, i) => {
      const vals = tcols.map((m) => obj[k] && obj[k][m] ? mean(obj[k][m].pearson) : NaN);
      const bv = Math.max(...vals.filter((v) => !isNaN(v)));
      t.push([tdR(labels[i], { align: "left", bold: true }), ...vals.map((v) => tdR(f2(v), { bold: v === bv, color: v === bv ? HEX.accent2 : HEX.dk1 }))]);
    });
    s.addTable(t, { x, y: y + 0.32, w, colW: [w - 2.6, 0.65, 0.65, 0.65, 0.65], fontSize: 10, rowH: 0.33,
      border: { type: "solid", pt: 0.75, color: "D5DCE5" }, margin: 0.04, objectName: name });
  };
  mkTable("E2 · Cross-lingual transfer (Pearson r)", ["en->en", "hi->hi", "en->hi", "hi->en"], ["EN → EN", "HI → HI", "EN → HI (0-shot)", "HI → EN (0-shot)"], E2, 0.5, 0.95, 4.35, "e2-table");
  mkTable("E3 · Domain and out-of-language transfer (Pearson r)", ["insurance->tenancy", "tenancy->insurance", "EnHi->FrJUDGE (zero-shot)", "FrJUDGE->FrJUDGE (in-language)"],
    ["Insurance → tenancy", "Tenancy → insurance", "EnHi → FrJUDGE (human)", "FrJUDGE → FrJUDGE"], E3, 5.15, 0.95, 4.35, "e3-table");
  // sanity
  s.addText("E4 · Sanity checks on 160 identical (gold 10) and 160 unrelated (gold 1) held-out pairs", { x: 0.5, y: 3.0, w: 9.0, h: 0.28, fontSize: 11.5, bold: true, color: C.text1, margin: 0, isTextBox: true });
  const sanM = ["WordLlama cosine (semantic)", "chrF (lexical)", "LegalDiff-GBR", "ML-JudgeBERT+LegalDiff", "ML-JudgeBERT+LegalDiff (no DA)"];
  const sanN = ["Embedding cosine", "chrF", "LegalDiff-GBR", "MLJB + LD (with DA)", "MLJB + LD (no DA)"];
  sanM.forEach((m, i) => {
    const x = 0.5 + i * 1.82, S = E1.sanity[m];
    card(s, x, 3.34, 1.72, 1.0, i === 3 ? "E3F0EE" : C.background2, "san-" + i);
    s.addText(sanN[i], { x: x + 0.08, y: 3.37, w: 1.6, h: 0.25, fontSize: 10, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText([{ text: "identical ", options: { fontSize: 9.5, color: HEX.accent5 } }, { text: f2(S.identical_mean), options: { fontSize: 15, bold: true, color: S.identical_mean >= 9 ? HEX.accent6 : HEX.accent3 } }],
      { x: x + 0.08, y: 3.63, w: 1.6, h: 0.3, margin: 0, isTextBox: true });
    s.addText([{ text: "unrelated ", options: { fontSize: 9.5, color: HEX.accent5 } }, { text: f2(S.unrelated_mean), options: { fontSize: 15, bold: true, color: S.unrelated_mean <= 2 ? HEX.accent6 : HEX.accent3 } }],
      { x: x + 0.08, y: 3.95, w: 1.6, h: 0.3, margin: 0, isTextBox: true });
  });
  card(s, 0.5, 4.45, 9.0, 0.62, C.text1, "e2-verdict");
  s.addText(GLOBAL_TITLES.e2verdict, { x: 0.68, y: 4.46, w: 8.65, h: 0.6, fontSize: 11, color: "FFFFFF", margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(GLOBAL_TITLES.e2notes);

  // ---------------- 10. E5 + conclusion
  pres.addSection({ title: "Conclusion" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusion" });
  s.addText(GLOBAL_TITLES.e5, { placeholder: "title" });
  const etypes = ["NONE", "NEGATION", "MODALITY", "NUMBER", "DATE", "ENTITY", "EXC_REMOVED", "OMIT_COND", "SCOPE", "HALLUC", "MINOR"];
  const etn = ["Faithful", "Negation", "Modality", "Number", "Date", "Party", "Exception", "Condition", "Scope", "Halluc.", "Minor"];
  const BEST = GLOBAL_TITLES.bestModel;
  s.addChart(pres.charts.BAR, [
    { name: "Gold LMP", labels: etn, values: etypes.map((e) => E1.by_error_type["LegalDiff-GBR"][e].gold) },
    { name: "Embedding cosine", labels: etn, values: etypes.map((e) => E1.by_error_type["WordLlama cosine (semantic)"][e].pred) },
    { name: NAMES[BEST], labels: etn, values: etypes.map((e) => E1.by_error_type[BEST][e].pred) },
  ], { x: 0.4, y: 0.92, w: 5.4, h: 2.6, barDir: "col", barGrouping: "clustered", chartColors: [HEX.dk1, HEX.accent5, HEX.accent2],
    showTitle: true, title: "E5: mean predicted LMP by gold error type", titleFontSize: 11, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 8, catAxisLabelFontFace: "+mn-lt", catAxisLabelRotate: -45,
    valAxisLabelColor: HEX.dk2, valAxisLabelFontSize: 8, valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 10, valAxisMajorUnit: 2,
    valGridLine: { color: "E3E8EE", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 8.5, legendFontFace: "+mn-lt", legendColor: HEX.dk2, barGapWidthPct: 50, objectName: "e5-chart" });
  const tilesE5 = [
    [f2(E5.binary.f1), "error-detection F1"],
    [Math.round(100 * E5.type_acc_on_errors) + "%", "error type correct"],
    [f2(E5.macro_f1), "type macro-F1 (11)"],
  ];
  tilesE5.forEach((t, i) => {
    const x = 6.0 + i * 1.18;
    card(s, x, 0.98, 1.1, 0.9, C.background2, "e5-tile-" + i);
    s.addText(t[0], { x: x + 0.06, y: 1.0, w: 1.0, h: 0.45, fontSize: 20, bold: true, color: C.accent2, fontFace: "Cambria", margin: 0, align: "center", isTextBox: true });
    s.addText(t[1], { x: x + 0.04, y: 1.45, w: 1.02, h: 0.38, fontSize: 9, color: C.text2, margin: 0, align: "center", isTextBox: true });
  });
  GLOBAL_TITLES.examples.forEach((ex, i) => {
    const y = 2.0 + i * 0.86;
    card(s, 6.0, y, 3.5, 0.78, "FFFFFF", "ex-" + i);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.0, y, w: 3.5, h: 0.78, rectRadius: 0.08, fill: { type: "none" }, line: { color: "C9D3DE", width: 1 }, objectName: "ex-border-" + i });
    s.addText(ex, { x: 6.1, y: y + 0.03, w: 3.32, h: 0.72, fontSize: 9, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
  });
  card(s, 0.5, 3.57, 5.3, 1.5, C.text1, "concl-card");
  s.addText(GLOBAL_TITLES.conclusion, { x: 0.65, y: 3.62, w: 5.05, h: 1.4, fontSize: 10, color: "FFFFFF", margin: 0, valign: "middle", paraSpaceAfter: 2, isTextBox: true });
  s.addText(GLOBAL_TITLES.next, { x: 6.0, y: 4.62, w: 3.5, h: 0.45, fontSize: 9.5, color: C.accent1, bold: true, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(GLOBAL_TITLES.e5notes);

  await pres.writeFile({ fileName: "/home/claude/deck/LMP_Milestone1.pptx" });
  await applyTheme("/home/claude/deck/LMP_Milestone1.pptx", THEME);
  console.log("written");
})();
