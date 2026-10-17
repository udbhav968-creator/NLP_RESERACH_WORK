# Legal Meaning Checker (web demo)

`legal-meaning-checker.html` is the deployed checker: LegalDiff features, the rule explainer and LegalDiff-GBR
(200 trees, trained on all 640 EnHi-LMP pairs) ported to JavaScript (`lmp.js`) and run entirely in the browser.

Rebuild from the repository root:

    python web/export_model.py      # train GBR on data/enhi_lmp.jsonl, write web/model.json and web/tests.json
    node web/test.js                # JS vs Python: features, scores and explanations must match exactly
    python web/gbr_quick.py         # model-card numbers (same protocol as run_experiments.py) -> web/stats640.json
    python web/build_page.py        # writes web/legal-meaning-checker.html
