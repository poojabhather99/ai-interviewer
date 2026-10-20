"""SQLite session store: sessions survive restarts (the original kept them in memory)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, skill TEXT, designation TEXT, experience TEXT, depth TEXT,
  job_description TEXT, resume_text TEXT, max_questions INTEGER, closed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS turns (
  session_id TEXT, idx INTEGER, question TEXT, answer TEXT, scores TEXT,
  PRIMARY KEY (session_id, idx));
CREATE TABLE IF NOT EXISTS resumes (id TEXT PRIMARY KEY, text TEXT);
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def save_resume(self, text: str) -> str:
        rid = uuid.uuid4().hex
        self.db.execute("INSERT INTO resumes VALUES (?, ?)", (rid, text))
        self.db.commit()
        return rid

    def get_resume(self, rid: str) -> str | None:
        r = self.db.execute("SELECT text FROM resumes WHERE id=?", (rid,)).fetchone()
        return r["text"] if r else None

    def create_session(self, **f: Any) -> str:
        sid = uuid.uuid4().hex
        self.db.execute(
            "INSERT INTO sessions (id, skill, designation, experience, depth, job_description,"
            " resume_text, max_questions) VALUES (?,?,?,?,?,?,?,?)",
            (sid, f["skill"], f["designation"], f["experience"], f["depth"],
             f["job_description"], f["resume_text"], f["max_questions"]),
        )
        self.db.commit()
        return sid

    def session(self, sid: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()

    def turns(self, sid: str) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM turns WHERE session_id=? ORDER BY idx", (sid,)
        ).fetchall()

    def add_question(self, sid: str, question: str) -> int:
        idx = len(self.turns(sid))
        self.db.execute("INSERT INTO turns VALUES (?,?,?,?,?)", (sid, idx, question, None, None))
        self.db.commit()
        return idx

    def set_answer(self, sid: str, idx: int, answer: str, scores: dict) -> None:
        self.db.execute(
            "UPDATE turns SET answer=?, scores=? WHERE session_id=? AND idx=?",
            (answer, json.dumps(scores), sid, idx),
        )
        self.db.commit()

    def close(self, sid: str) -> None:
        self.db.execute("UPDATE sessions SET closed=1 WHERE id=?", (sid,))
        self.db.commit()
