// LegalDiff features, rule explainer and LegalDiff-GBR scorer — JavaScript port of src/legal_features.py + sklearn GBR.
// Works in the browser (window.LMP) and in Node (module.exports).
(function (root) {
  "use strict";
  let LEXD = null, MODEL = null, ALLNUM = null;
  const W = "\\p{L}\\p{N}_";                        // Python's \w for str patterns (letters, numbers, underscore)
  const RE_NT = new RegExp(`n't(?![${W}])`, "gu");
  const RE_POSS = new RegExp(`(?<=[${W}])'s(?![${W}])`, "gu");
  const RE_ELIS = new RegExp(`(?<![${W}])([${W}]{1,7}')(?=[${W}])`, "gu");
  const RE_TOK = new RegExp(`[${W}\\u0900-\\u0963\\u0966-\\u097F'\\-]+|[%₹]`, "gu");
  const RE_FR = new RegExp(`[éèêàçùâîôû]|(?<![${W}])(le|la|les|des|est|une)(?![${W}])`, "u");
  const DEV = "०१२३४५६७८९";

  function init(data) {
    LEXD = data.lex; MODEL = data.model;
    ALLNUM = new Set(); Object.values(LEXD.NUM_WORDS).forEach((d) => Object.keys(d).forEach((w) => ALLNUM.add(w)));
    LEXD._elis = new Set(LEXD.ELISIONS);
  }
  const devDigits = (s) => s.replace(/[०-९]/g, (c) => String(DEV.indexOf(c)));
  const norm = (s) => devDigits(s.normalize("NFC")).toLowerCase();
  function stripChars(w, ch) { let a = 0, b = w.length; while (a < b && w[a] === ch) a++; while (b > a && w[b - 1] === ch) b--; return w.slice(a, b); }

  function detectLang(text) {
    if (/[ऀ-ॿ]/.test(text)) return "hi";
    if (RE_FR.test(text.toLowerCase())) return "fr";
    return "en";
  }
  function tokens(text) {
    let t = norm(text).replace(/’/g, "'").replace(/‘/g, "'");
    t = t.replace(RE_NT, " not").replace(RE_POSS, "").replace(RE_ELIS, "$1 ");
    const out = [];
    for (const m of t.matchAll(RE_TOK)) {
      let w = m[0];
      if (!LEXD._elis.has(w)) w = stripChars(w, "'");
      w = stripChars(w, "-");
      if (!w) continue;
      if (w.includes("-") && !ALLNUM.has(w)) w.split("-").forEach((p) => { if (p) out.push(p); });
      else out.push(w);
    }
    return out;
  }
  function numbers(text, lang) {
    const t = norm(text), vals = [], MULT = LEXD.MULT;
    for (const m of t.matchAll(/\d[\d,]*(?:\.\d+)?/g)) {
      let v = parseFloat(m[0].replace(/,/g, ""));
      const end = m.index + m[0].length;
      const mm = /^\s*([^\s\d,.;:]+)/u.exec(t.slice(end, end + 12));
      if (mm && Object.prototype.hasOwnProperty.call(MULT, mm[1])) v *= MULT[mm[1]];
      vals.push(v);
    }
    const toks = tokens(text), words = LEXD.NUM_WORDS[lang] || {}, units = new Set(LEXD.TIME_UNITS[lang] || []);
    toks.forEach((w, i) => {
      if (Object.prototype.hasOwnProperty.call(words, w) && !["lakh", "लाख", "first"].includes(w)) {
        const nxt = i + 1 < toks.length ? toks[i + 1] : "";
        const isMult = Object.prototype.hasOwnProperty.call(MULT, nxt);
        if (["one", "एक", "un"].includes(w) && !units.has(nxt) && !isMult) return;
        let v = Number(words[w]); if (isMult) v *= MULT[nxt];
        vals.push(v);
      }
    });
    return vals;
  }
  const unit = (w) => (Object.prototype.hasOwnProperty.call(LEXD.UNIT_CANON, w) ? LEXD.UNIT_CANON[w] : w);
  function durations(text, lang) {
    const toks = tokens(text), units = new Set(LEXD.TIME_UNITS[lang] || []), out = [];
    toks.forEach((w, i) => {
      if (units.has(w)) {
        const nums = numbers(toks.slice(Math.max(0, i - 3), i).join(" "), lang);
        out.push((nums.length ? String(nums[nums.length - 1]) : "None") + "|" + unit(w));
      }
    });
    return out;
  }
  const lexSet = (cat, lang) => new Set((LEXD.LEX[cat] || {})[lang] || []);
  const count = (toks, cat, lang) => { const s = lexSet(cat, lang); return toks.filter((w) => s.has(w)).length; };
  function modalCounts(toks, lang) {
    const ob_ = lexSet("oblig", lang), pe_ = lexSet("perm", lang), neg = lexSet("neg", lang);
    let ob = 0, pe = 0;
    toks.forEach((w, i) => {
      if (ob_.has(w)) ob++;
      else if (lang === "en" && w === "cannot") ob++;
      else if (pe_.has(w)) {
        const before = toks.slice(Math.max(0, i - (lang === "hi" ? 4 : 2)), i), after = toks.slice(i + 1, i + 3);
        const negated = before.some((x) => neg.has(x)) || (lang !== "hi" && after.some((x) => neg.has(x)));
        if (negated) ob++; else pe++;
      }
    });
    return [ob, pe];
  }
  const roles = (toks, lang) => { const r = LEXD.ROLES[lang] || {}; return toks.filter((w) => Object.prototype.hasOwnProperty.call(r, w)).map((w) => r[w]); };
  function multisetMinus(a, b) {        // sum of positive counts of Counter(a) - Counter(b)
    const c = new Map(); a.forEach((x) => c.set(x, (c.get(x) || 0) + 1)); b.forEach((x) => c.set(x, (c.get(x) || 0) - 1));
    let s = 0; c.forEach((v) => { if (v > 0) s += v; }); return s;
  }
  const symDiff = (a, b) => { const A = new Set(a), B = new Set(b); let n = 0; A.forEach((x) => { if (!B.has(x)) n++; }); B.forEach((x) => { if (!A.has(x)) n++; }); return n; };

  function features(original, simplification, lang) {
    lang = lang || detectLang(original);
    const to = tokens(original), ts = tokens(simplification);
    const no = numbers(original, lang), ns = numbers(simplification, lang);
    const f = {};
    f.num_missing = multisetMinus(no, ns); f.num_added = multisetMinus(ns, no);
    const dO = durations(original, lang), dS = durations(simplification, lang);
    f.dur_mismatch = Math.min((dO.length || dS.length) ? symDiff(dO, dS) : 0, 4);
    const negO = count(to, "neg", lang), negS = count(ts, "neg", lang);
    f.neg_diff = negS - negO; f.neg_absdiff = Math.abs(negS - negO);
    const [obO, peO] = modalCounts(to, lang), [obS, peS] = modalCounts(ts, lang);
    f.oblig_diff = obS - obO; f.perm_diff = peS - peO;
    f.modal_flip = ((obO > 0 && obS === 0 && peS > peO) || (peO > 0 && peS === 0 && obS > obO) || (peS > peO && obS < obO)) ? 1 : 0;
    const cO = count(to, "cond", lang), cS = count(ts, "cond", lang), eO = count(to, "exc", lang), eS = count(ts, "exc", lang);
    f.cond_lost = Math.max(cO - cS, 0); f.cond_added = Math.max(cS - cO, 0);
    f.exc_lost = Math.max(eO - eS, 0); f.exc_added = Math.max(eS - eO, 0);
    f.quant_absdiff = Math.abs(count(to, "quant", lang) - count(ts, "quant", lang));
    const ro = roles(to, lang), rs = roles(ts, lang), so = new Set(ro), ss = new Set(rs);
    const uni = new Set([...so, ...ss]), inter = [...so].filter((x) => ss.has(x)).length;
    f.role_jaccard_dist = uni.size ? 1 - inter / uni.size : 0;
    f.role_subject_change = (ro.length && rs.length && ro[0] !== rs[0]) ? 1 : 0;
    f.len_ratio = ts.length / Math.max(to.length, 1);
    const vo = new Set(to), vs = new Set(ts);
    f.coverage = [...vo].filter((x) => vs.has(x)).length / Math.max(vo.size, 1);
    f.novelty = [...vs].filter((x) => !vo.has(x)).length / Math.max(vs.size, 1);
    const tu = new Set(LEXD.TIME_UNITS[lang] || []);
    f.time_word_change = symDiff(to.filter((w) => tu.has(w)).map(unit), ts.filter((w) => tu.has(w)).map(unit));
    return { x: MODEL.features.map((k) => Number(f[k])), f, lang };
  }

  function predictX(x) {
    let raw = MODEL.init;
    for (const t of MODEL.trees) {
      let n = 0;
      while (t.l[n] !== -1) n = Math.fround(x[t.f[n]]) <= t.t[n] ? t.l[n] : t.r[n];
      raw += MODEL.lr * t.v[n];
    }
    return Math.min(10, Math.max(1, raw));
  }
  const fmt = (v) => (Number.isInteger(v) ? String(v) : String(v));
  const uniqSorted = (a) => [...new Set(a)].sort((p, q) => p - q);

  function explain(original, simplification, score, lang) {
    const { f, lang: lg } = features(original, simplification, lang);
    lang = lg;
    const no = numbers(original, lang), ns = numbers(simplification, lang);
    if (score >= 7.5) return ["NONE", "Legal meaning appears preserved; no legally salient difference detected."];
    const to = tokens(original), ts = tokens(simplification);
    const polO = count(to, "neg", lang) > 0, polS = count(ts, "neg", lang) > 0;
    const ro = roles(to, lang), rs = roles(ts, lang);
    if (polO !== polS && !f.modal_flip) return ["NEGATION", `Polarity changed: negation ${polS ? "added" : "removed"} in the simplification, reversing the rule.`];
    if (f.modal_flip || (f.oblig_diff !== 0 && f.perm_diff !== 0 && f.oblig_diff * f.perm_diff < 0)) return ["MODALITY", "Deontic force changed (obligation vs. permission/discretion)."];
    const nsS = new Set(ns), noS = new Set(no);
    const miss = uniqSorted(no.filter((v) => !nsS.has(v))), add = uniqSorted(ns.filter((v) => !noS.has(v)));
    const isTime = f.dur_mismatch > 0 || f.time_word_change > 0;
    if (miss.length && add.length) {
      return [isTime ? "DATE" : "NUMBER", `${isTime ? "Time limit" : "Amount/quantity"} changed: ${miss.map(fmt).join(", ")} -> ${add.map(fmt).join(", ")}.`];
    }
    if (add.length && f.len_ratio > 1.15) return ["HALLUC", `New figure(s) ${add.map(fmt).join(", ")} introduced together with content absent from the original.`];
    const roS = new Set(ro), newRoles = [...new Set(rs)].filter((r) => !roS.has(r)).sort();
    if (newRoles.length || f.role_subject_change) return ["ENTITY", `Rights/duties assigned to a different party (${(newRoles.length ? newRoles : ["subject changed"]).join(", ")}).`];
    if (f.exc_lost > 0) return ["EXC_REMOVED", "An exception/carve-out in the original is missing, widening the rule."];
    if (f.len_ratio > 1.15 || f.cond_added || f.exc_added) return ["HALLUC", "Simplification adds content (new duty, condition or benefit) absent from the original."];
    if (miss.length && isTime) return ["DATE", `Time limit (${miss.map(fmt).join(", ")}) removed or altered.`];
    if (score >= 5.5) return ["MINOR", "Minor detail omitted; core legal effect largely retained."];
    if (miss.length || f.cond_lost > 0 || f.len_ratio < 0.75) return ["OMIT_COND", "A condition or qualifying clause of the original is omitted."];
    if (f.quant_absdiff > 0) return ["SCOPE", "Scope changed (quantifier/coverage such as any/only/all differs)."];
    return ["SCOPE", "Legal scope of the rule differs from the original."];
  }
  const decision = (s) => (s >= 7.5 ? "Preserved" : s >= 4.5 ? "Partially preserved" : "Not preserved");

  function score(original, simplification) {
    const r = features(original, simplification);
    const s = predictX(r.x);
    const [type, why] = explain(original, simplification, s, r.lang);
    return { score: s, decision: decision(s), type, why, lang: r.lang, features: r.f };
  }
  const api = { init, tokens, numbers, features, predictX, explain, score, detectLang, decision };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.LMP = api;
})(typeof window !== "undefined" ? window : globalThis);
