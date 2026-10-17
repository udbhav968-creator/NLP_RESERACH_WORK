import json, sys
Q = json.load(open("web/stats640.json"))
a = Q["all"]
stats = dict(r=f'{a["pearson"]:.2f}', r_lang=f'{Q["en"]["pearson"]:.2f} / {Q["hi"]["pearson"]:.2f}', rmse=f'{a["rmse"]:.2f}', npf1=f'{a["f1_notpreserved"]:.2f}',
             fr=f'r = {Q["fr_zero_shot"]:.2f}', det=f'{Q["detect_f1"]:.2f}', sanity=f'{Q["sanity"]["identical"]:.1f} / {Q["sanity"]["unrelated"]:.1f}',
             chrf=f'r = {Q["chrf"]["pearson"]:.2f}', n=int(a["n"]))
model = json.load(open("web/model.json", encoding="utf-8"))
page = open("web/page_template.html", encoding="utf-8").read()
page = page.replace("__LMPJS__", open("web/lmp.js", encoding="utf-8").read())
page = page.replace("__MODEL__", json.dumps(model, ensure_ascii=False, separators=(",", ":")))
page = page.replace("__STATS__", json.dumps(stats, ensure_ascii=False)).replace("__NTRAIN__", str(model["model"]["n_train"]))
open("web/legal-meaning-checker.html", "w", encoding="utf-8").write(page)
print(stats, len(page))
