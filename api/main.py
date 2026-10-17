"""EnHi-LMP Legal Meaning Checker — REST API + web app.

Run locally:   uvicorn api.main:app --reload --port 8000     (from the repository root)
Docs:          http://localhost:8000/docs
"""
from __future__ import annotations
import csv, io, math, os, time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from .lmp_service import LMPService, TYPE_LABELS
from .storage import Store

VERSION = "2.0.0"
MAX_TEXT, MAX_BATCH = 5000, 500
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="EnHi-LMP Legal Meaning Checker API", version=VERSION,
              description="Scores whether a plain-language rewrite of an English or Hindi legal clause keeps its legal meaning "
                          "(1–10, JUDGEBERT scale), decides Preserved / Partially / Not preserved, and explains the legal change. "
                          "Model: LegalDiff-GBR trained on 640 EnHi-LMP pairs (rubric-based silver labels).")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("LMP_CORS", "*").split(","), allow_methods=["*"], allow_headers=["*"])
svc = LMPService()
store = Store(os.environ.get("LMP_DB", Path(__file__).resolve().parent / "data" / "lmp.sqlite3"))
STARTED = time.time()


# ------------------------------------------------------------------ schemas
class Pair(BaseModel):
    original: str = Field(..., min_length=1, max_length=MAX_TEXT, description="The legal clause as written")
    simplification: str = Field(..., min_length=1, max_length=MAX_TEXT, description="The plain-language rewrite")


class ScoreRequest(Pair):
    save: bool = Field(True, description="Store the check in the history")


class ScoreResponse(BaseModel):
    id: Optional[int] = None
    score: float
    decision: str
    error_type: str
    error_label: str
    explanation: str
    lang: str
    features: dict[str, float]


class BatchRequest(BaseModel):
    pairs: list[Pair] = Field(..., min_length=1, max_length=MAX_BATCH)
    save: bool = False


class FeedbackRequest(BaseModel):
    check_id: int
    human_score: int = Field(..., ge=1, le=10, description="Your own LMP score for the pair, 1–10")
    comment: Optional[str] = Field(None, max_length=500)


# ------------------------------------------------------------------ routes
@app.get("/api/health", tags=["meta"])
def health():
    return dict(status="ok", version=VERSION, model=svc.meta["model"], n_train=svc.meta["n_train"],
                uptime_s=round(time.time() - STARTED, 1), checks_stored=store.counts()["total"])


@app.get("/api/model", tags=["meta"])
def model_card():
    return dict(svc.meta, labels="rubric-based silver LMP scores (1–10)", error_types=TYPE_LABELS,
                decision_thresholds={"Preserved": ">= 7.5", "Partially preserved": "4.5 – 7.5", "Not preserved": "< 4.5"})


@app.post("/api/score", response_model=ScoreResponse, tags=["scoring"])
def score(req: ScoreRequest):
    r = svc.score(req.original, req.simplification)
    if req.save:
        r["id"] = store.add_check(req.original, req.simplification, r, source="api")
    return r


@app.post("/api/batch", tags=["scoring"])
def batch(req: BatchRequest):
    pairs = [(p.original, p.simplification) for p in req.pairs]
    results = svc.score_many(pairs)
    if req.save:
        for (o, s), r in zip(pairs, results): r["id"] = store.add_check(o, s, r, source="batch")
    return dict(n=len(results), results=results)


@app.post("/api/batch/csv", response_class=PlainTextResponse, tags=["scoring"],
          description="Upload a CSV with columns `original,simplification` (header row required). Returns the same CSV with "
                      "score, decision, error_type and explanation columns added.")
async def batch_csv(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or not {"original", "simplification"} <= set(rows[0].keys()):
        raise HTTPException(422, "CSV needs a header row with columns: original, simplification")
    if len(rows) > MAX_BATCH:
        raise HTTPException(413, f"At most {MAX_BATCH} rows per upload")
    results = svc.score_many([(r["original"], r["simplification"]) for r in rows])
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["original", "simplification", "score", "decision", "error_type", "explanation"])
    for r, res in zip(rows, results):
        w.writerow([r["original"], r["simplification"], f'{res["score"]:.2f}', res["decision"], res["error_type"], res["explanation"]])
    return out.getvalue()


@app.post("/api/feedback", tags=["feedback"])
def feedback(req: FeedbackRequest):
    if not store.get_check(req.check_id):
        raise HTTPException(404, "No check with that id")
    return dict(id=store.add_feedback(req.check_id, req.human_score, req.comment), check_id=req.check_id)


@app.get("/api/history", tags=["history"])
def history(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    return dict(items=store.history(limit, offset))


@app.get("/api/checks/{check_id}", tags=["history"])
def get_check(check_id: int):
    c = store.get_check(check_id)
    if not c: raise HTTPException(404, "No check with that id")
    return c


def _pearson(a, b):
    n = len(a)
    if n < 3: return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0: return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


@app.get("/api/stats", tags=["history"])
def stats():
    c = store.counts(); fb = store.pairs_with_feedback()
    dec = lambda s: 2 if s >= 7.5 else (1 if s >= 4.5 else 0)
    human = dict(n=len(fb))
    if fb:
        m, h = [x for x, _ in fb], [y for _, y in fb]
        human.update(mae=sum(abs(x - y) for x, y in fb) / len(fb), pearson=_pearson(m, h),
                     decision_agreement=sum(dec(x) == dec(y) for x, y in fb) / len(fb))
    return dict(checks=c, human_feedback=human, model_cv=svc.meta.get("cv"))


# ------------------------------------------------------------------ web app
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
