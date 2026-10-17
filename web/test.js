const L = require("./lmp.js"); const fs = require("fs"); const path = require("path");
L.init(JSON.parse(fs.readFileSync(path.join(__dirname, "model.json"), "utf8")));
const T = JSON.parse(fs.readFileSync(path.join(__dirname, "tests.json"), "utf8"));
let fx = 0, px = 0, ex = 0, lx = 0, maxd = 0; const bad = [];
for (const t of T) {
  const r = L.features(t.o, t.s);
  if (r.lang !== t.lang) lx++;
  const diffIdx = r.x.map((v, i) => Math.abs(v - t.x[i]) > 1e-9 ? i : -1).filter((i) => i >= 0);
  if (diffIdx.length) { fx++; if (bad.length < 6) bad.push({ o: t.o.slice(0, 80), s: t.s.slice(0, 80), idx: diffIdx, js: diffIdx.map(i => r.x[i]), py: diffIdx.map(i => t.x[i]) }); }
  const p = L.predictX(t.x); const d = Math.abs(p - t.p); maxd = Math.max(maxd, d); if (d > 1e-6) px++;
  const [et, why] = L.explain(t.o, t.s, t.p); if (et !== t.et || why !== t.why) { ex++; if (bad.length < 10) bad.push({ et, why, pyet: t.et, pywhy: t.why }); }
}
console.log({ n: T.length, featureMismatch: fx, predMismatch: px, maxPredDiff: maxd, explainMismatch: ex, langMismatch: lx });
console.log(JSON.stringify(bad, null, 1));
