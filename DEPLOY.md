# Deploying the Legal Meaning Checker

The app is one Docker image: a FastAPI backend (`api/`) that scores pairs with LegalDiff-GBR, stores checks and human
scores in SQLite, serves the REST API (`/api/*`, docs at `/docs`) and serves the web app (`/`).

| Where | Cost | How | Public URL |
|---|---|---|---|
| claude.ai artifact | free | already live (in-browser model + shared database) | the Legal Meaning Checker link (share it from its Share menu) |
| Hugging Face Spaces | free | `deploy/push_to_hf_space.ps1` (below) | `https://<user>-legal-meaning-checker.hf.space` |
| Render | free | **live** — Blueprint from `render.yaml`, redeploys on every push to `main` | https://legal-meaning-checker.onrender.com |
| Your computer | free | `uvicorn` or Docker (below) | `http://localhost:8000` |

## 1. Run locally

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --port 8000        # http://localhost:8000  ·  http://localhost:8000/docs
python -m pytest -q api/tests           # needs api/requirements-dev.txt
```
With Docker: `docker compose up --build` → http://localhost:7860 (saved checks survive restarts in the `lmp-data` volume).

## 2. Hugging Face Spaces (recommended)

1. https://huggingface.co/new-space → name `legal-meaning-checker`, SDK **Docker**, template **Blank**, **Public** → Create.
2. https://huggingface.co/settings/tokens → New token, type **Write**.
3. In PowerShell, in the project folder:
   ```powershell
   .\deploy\push_to_hf_space.ps1 -Space "<your-hf-username>/legal-meaning-checker"
   ```
   Paste the token when git asks for a password. The Space builds in 2–4 minutes.

## 3. Render

render.com → sign in with GitHub → **New → Blueprint** → pick `NLP_RESERACH_WORK` → **Apply**.
Render builds the `Dockerfile` and health-checks `/api/health`. Free instances sleep when idle (first request ~30 s), and
the SQLite file is reset on each deploy; attach a disk at `/app/api/data` to keep history.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | 7860 | Port the server listens on |
| `LMP_DB` | `api/data/lmp.sqlite3` | SQLite file for checks and human scores |
| `LMP_CORS` | `*` | Comma-separated origins allowed to call the API from a browser |
| `LMP_MODEL` | `api/model.joblib` | Model file; trained automatically from `data/enhi_lmp.jsonl` when missing |

## Continuous integration

`.github/workflows/ci.yml` runs on every push: API tests, the JavaScript-vs-Python parity test (1,053 pairs must give
identical features, scores and explanations), the web build, and a Docker build with a smoke test.
