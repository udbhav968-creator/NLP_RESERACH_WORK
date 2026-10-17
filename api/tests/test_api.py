import os, io
os.environ["LMP_DB"] = ":memory:"
from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)
FAITHFUL = ("The Landlord shall bear the cost of all structural repairs to the premises.",
            "The landlord must pay for all structural repairs to the premises.")
PARTY = ("The Landlord shall bear the cost of all structural repairs to the premises.",
         "The tenant must pay for all structural repairs to the premises.")
NUMBER = ("A compulsory deductible of Rs. 2,000 shall apply to each claim under this policy.",
          "You pay the first Rs. 20,000 of each claim under this policy yourself.")
HINDI_NEG = ("किरायेदार मकान मालिक की लिखित अनुमति के बिना परिसर में पालतू जानवर नहीं रखेगा।", "किरायेदार परिसर में पालतू जानवर रख सकता है।")


def post(o, s, save=True):
    r = c.post("/api/score", json={"original": o, "simplification": s, "save": save}); assert r.status_code == 200, r.text
    return r.json()


def test_health_and_model():
    h = c.get("/api/health").json(); assert h["status"] == "ok" and h["n_train"] == 640
    m = c.get("/api/model").json(); assert len(m["features"]) == 19 and "NEGATION" in m["error_types"]


def test_scores_and_explanations():
    f, p, n, h = post(*FAITHFUL), post(*PARTY), post(*NUMBER), post(*HINDI_NEG)
    assert f["decision"] == "Preserved" and f["error_type"] == "NONE"
    assert p["decision"] == "Not preserved" and p["error_type"] == "ENTITY"
    assert n["error_type"] == "NUMBER" and "2000 -> 20000" in n["explanation"]
    assert h["lang"] == "hi" and h["error_type"] == "NEGATION" and h["score"] < 4.5
    assert 1 <= f["score"] <= 10 and len(f["features"]) == 19


def test_identical_and_unrelated_anchor_the_scale():
    assert post(FAITHFUL[0], FAITHFUL[0], save=False)["score"] > 9.5
    assert post(FAITHFUL[0], HINDI_NEG[1], save=False)["score"] < 3


def test_validation():
    assert c.post("/api/score", json={"original": "", "simplification": "x"}).status_code == 422
    assert c.post("/api/feedback", json={"check_id": 1, "human_score": 11}).status_code == 422
    assert c.post("/api/feedback", json={"check_id": 999999, "human_score": 5}).status_code == 404


def test_history_feedback_stats():
    r = post(*PARTY)
    assert c.post("/api/feedback", json={"check_id": r["id"], "human_score": 2, "comment": "party swapped"}).status_code == 200
    items = c.get("/api/history?limit=5").json()["items"]
    assert items[0]["id"] == r["id"] and items[0]["n_feedback"] == 1
    s = c.get("/api/stats").json()
    assert s["checks"]["total"] >= 1 and s["human_feedback"]["n"] >= 1 and s["model_cv"] is not None


def test_batch_json_and_csv():
    b = c.post("/api/batch", json={"pairs": [{"original": o, "simplification": s} for o, s in (FAITHFUL, PARTY)]}).json()
    assert b["n"] == 2 and b["results"][1]["error_type"] == "ENTITY"
    csv_text = "original,simplification\n" + "\n".join(f'"{o}","{s}"' for o, s in (FAITHFUL, NUMBER))
    r = c.post("/api/batch/csv", files={"file": ("pairs.csv", io.BytesIO(csv_text.encode()), "text/csv")})
    assert r.status_code == 200 and r.text.count("\n") == 3 and "NUMBER" in r.text
    bad = c.post("/api/batch/csv", files={"file": ("x.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")})
    assert bad.status_code == 422


def test_web_app_served():
    assert c.get("/").status_code == 200
