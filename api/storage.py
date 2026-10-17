"""SQLite persistence for checks and human feedback (stdlib only)."""
from __future__ import annotations
import json, os, sqlite3, threading, time
from pathlib import Path

DB_PATH = Path(os.environ.get("LMP_DB", Path(__file__).resolve().parent / "data" / "lmp.sqlite3"))
SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at REAL NOT NULL,
  original TEXT NOT NULL,
  simplification TEXT NOT NULL,
  lang TEXT NOT NULL,
  score REAL NOT NULL,
  decision TEXT NOT NULL,
  error_type TEXT NOT NULL,
  explanation TEXT NOT NULL,
  features TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'api'
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  check_id INTEGER NOT NULL REFERENCES checks(id) ON DELETE CASCADE,
  created_at REAL NOT NULL,
  human_score INTEGER NOT NULL CHECK (human_score BETWEEN 1 AND 10),
  comment TEXT
);
CREATE INDEX IF NOT EXISTS idx_checks_created ON checks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_check ON feedback(check_id);
"""


class Store:
    def __init__(self, path: Path | str = DB_PATH):
        path = Path(path)
        if str(path) != ":memory:": path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.lock = threading.Lock()

    def add_check(self, original: str, simplification: str, r: dict, source: str = "api") -> int:
        with self.lock, self.conn:
            cur = self.conn.execute(
                "INSERT INTO checks (created_at, original, simplification, lang, score, decision, error_type, explanation, features, source)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (time.time(), original, simplification, r["lang"], r["score"], r["decision"], r["error_type"], r["explanation"],
                 json.dumps(r["features"]), source))
            return int(cur.lastrowid)

    def get_check(self, check_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM checks WHERE id = ?", (check_id,)).fetchone()
        return self._check(row) if row else None

    def add_feedback(self, check_id: int, human_score: int, comment: str | None) -> int:
        with self.lock, self.conn:
            cur = self.conn.execute("INSERT INTO feedback (check_id, created_at, human_score, comment) VALUES (?,?,?,?)",
                                    (check_id, time.time(), human_score, comment))
            return int(cur.lastrowid)

    def history(self, limit: int = 50, offset: int = 0) -> list[dict]:
        rows = self.conn.execute(
            "SELECT c.*, COUNT(f.id) AS n_feedback, AVG(f.human_score) AS human_mean FROM checks c"
            " LEFT JOIN feedback f ON f.check_id = c.id GROUP BY c.id ORDER BY c.created_at DESC, c.id DESC LIMIT ? OFFSET ?",
            (limit, offset)).fetchall()
        return [self._check(r) for r in rows]

    def pairs_with_feedback(self) -> list[tuple[float, float]]:
        return [(r["score"], r["human_score"]) for r in self.conn.execute(
            "SELECT c.score AS score, f.human_score AS human_score FROM feedback f JOIN checks c ON c.id = f.check_id")]

    def counts(self) -> dict:
        q = lambda sql: {r[0]: r[1] for r in self.conn.execute(sql)}
        total = self.conn.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
        return dict(total=total, by_decision=q("SELECT decision, COUNT(*) FROM checks GROUP BY decision"),
                    by_error_type=q("SELECT error_type, COUNT(*) FROM checks GROUP BY error_type"),
                    by_lang=q("SELECT lang, COUNT(*) FROM checks GROUP BY lang"),
                    mean_score=self.conn.execute("SELECT AVG(score) FROM checks").fetchone()[0])

    @staticmethod
    def _check(row) -> dict:
        d = dict(row)
        d["features"] = json.loads(d["features"])
        return d
