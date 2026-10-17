"""Build the single-file web app (frontend/app_template.html + web/lmp.js + web/model.json + web/stats640.json).
Writes web/legal-meaning-checker.html (claude.ai / any static host) and api/static/index.html (served by the API).
Run from the repository root:  python frontend/build.py"""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
Q = json.load(open(R / "web" / "stats640.json")); a = Q["all"]
cv = dict(r=f'{a["pearson"]:.2f}', r_lang=f'{Q["en"]["pearson"]:.2f} / {Q["hi"]["pearson"]:.2f}', rmse=f'{a["rmse"]:.2f}', npf1=f'{a["f1_notpreserved"]:.2f}',
          fr=f'r = {Q["fr_zero_shot"]:.2f}', det=f'{Q["detect_f1"]:.2f}', sanity=f'{Q["sanity"]["identical"]:.1f} / {Q["sanity"]["unrelated"]:.1f}',
          chrf=f'r = {Q["chrf"]["pearson"]:.2f}')
model = json.load(open(R / "web" / "model.json", encoding="utf-8"))
page = (R / "frontend" / "app_template.html").read_text(encoding="utf-8")
page = page.replace("__LMPJS__", (R / "web" / "lmp.js").read_text(encoding="utf-8"))
page = page.replace("__MODEL__", json.dumps(model, ensure_ascii=False, separators=(",", ":")))
page = page.replace("__STATS__", json.dumps(cv, ensure_ascii=False)).replace("__NTRAIN__", str(model["model"]["n_train"]))
(R / "web" / "legal-meaning-checker.html").write_text(page, encoding="utf-8")
# The API serves a complete HTML document (the claude.ai publisher adds the skeleton itself).
doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
       '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui}'
       'img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + page + '</body></html>')
(R / "api" / "static" / "index.html").write_text(doc, encoding="utf-8")
print("built", len(page), "bytes")
