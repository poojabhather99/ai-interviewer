from __future__ import annotations

import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .llm import get_llm
from .service import Interviewer, InterviewError
from .store import Store

MAX_UPLOAD = 5 * 1024 * 1024


class StartReq(BaseModel):
    skill: str = Field(min_length=1, max_length=100)
    designation: str = Field(min_length=1, max_length=100)
    experience: str = Field(default="0", max_length=20)
    depth: str = Field(default="medium", max_length=20)
    job_description: str = Field(default="", max_length=6000)
    resume_id: str | None = None
    max_questions: int = 5


class AnswerReq(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


def extract_pdf_text(data: bytes) -> str:  # pragma: no cover - optional dependency
    import io

    from pypdf import PdfReader

    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)


def create_app(store: Store | None = None, llm=None) -> FastAPI:
    store = store or Store(os.environ.get("INTERVIEW_DB", ":memory:"))
    svc = Interviewer(store, llm or get_llm())
    app = FastAPI(title="AI Interviewer")

    def guard(fn, *a, **k):
        try:
            return fn(*a, **k)
        except InterviewError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/resume")
    async def upload_resume(file: UploadFile = File(...)):
        data = await file.read(MAX_UPLOAD + 1)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, "file too large (max 5 MB)")
        if data[:5] == b"%PDF-":
            text = extract_pdf_text(data)
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as e:
                raise HTTPException(415, "upload a PDF or UTF-8 text file") from e
        return {"resume_id": store.save_resume(text[:20000])}

    @app.post("/sessions")
    def start(req: StartReq):
        return guard(svc.start, **req.model_dump())

    @app.post("/sessions/{sid}/answer")
    def answer(sid: str, req: AnswerReq):
        return guard(svc.answer, sid, req.answer)

    @app.get("/sessions/{sid}/report")
    def report(sid: str):
        return guard(svc.report, sid)

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
