# Legal Meaning Checker (web demo)

`legal-meaning-checker.html` is the built web app (see `frontend/`): LegalDiff features, the rule explainer and LegalDiff-GBR
(200 trees, trained on all 640 EnHi-LMP pairs) ported to JavaScript (`lmp.js`) and run entirely in the browser.

Rebuild from the repository root (the full app is built by `python frontend/build.py`):

    python web/export_model.py      # export the API model (api/lmp_service.py) to web/model.json + web/tests.json
    node web/test.js                # JS vs Python: features, scores and explanations must match exactly
    python web/gbr_quick.py         # model-card numbers (same protocol as run_experiments.py) -> web/stats640.json
    python frontend/build.py        # writes web/legal-meaning-checker.html and api/static/index.html
