# ai-interviewer

[![CI](https://github.com/poojabhather99/ai-interviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/poojabhather99/ai-interviewer/actions/workflows/ci.yml)

**Live demo (runs in your browser):** https://poojabhather99.github.io/ai-interviewer/

An API that runs an adaptive technical interview: it generates one question at a time from the candidate's skill, role, job description and (optionally) resume, scores each answer, and produces a report.

This is a clean rewrite of an earlier prototype that used AWS Bedrock with in-memory sessions. The rewrite changes the parts that matter for running it for real:

| Prototype | This version |
|---|---|
| Sessions lived in memory and vanished on restart | SQLite store; sessions survive restarts (tested) |
| The question endpoint opened whatever file path the client sent | Resumes are uploaded once and referenced by an opaque id; no client-supplied paths are ever read |
| Resume and job description pasted straight into the prompt | Inputs are length-bounded, common "ignore previous instructions" phrasing is stripped, and untrusted text is fenced in `<data>` tags the prompt tells the model to treat as data |
| One LLM hard-wired | `LLM` interface with an offline default and a Groq backend |
| No scoring | Transparent rubric per answer plus a session report |

## API

| Endpoint | Purpose |
|---|---|
| `POST /resume` | Upload a PDF (needs the `pdf` extra) or UTF-8 text file, max 5 MB; returns `resume_id` |
| `POST /sessions` | Start with skill, designation, experience, depth, job description, optional `resume_id`, `max_questions` (1 to 15); returns the first question |
| `POST /sessions/{id}/answer` | Submit an answer; returns scores and the next question, or `done` |
| `GET /sessions/{id}/report` | Transcript, per-answer scores, averages |

## Run

```bash
pip install -e ".[dev]"
pytest -q                                   # 11 tests
uvicorn interviewer.api:app --reload        # docs at /docs
pip install -e ".[llm]" && GROQ_API_KEY=... uvicorn interviewer.api:app   # real model
INTERVIEW_DB=interviews.db uvicorn interviewer.api:app                     # persistent sessions
```

## Scoring, and what it can't do

Each answer is scored 0 to 1 on depth (length, capped near 80 words), structure (reasoning words such as "because" and "trade-off"), specifics (numbers), relevance (mentions the skill) and a hedging penalty. This measures the **form** of an answer. It cannot tell whether the answer is technically correct, so it should not be used to make hiring decisions. The report says so.

## Limitations

- Without `GROQ_API_KEY` the questions come from a fixed five-step ladder, which is only there so the app and tests run offline. The Groq path is implemented but not covered by automated tests.
- Prompt-injection handling is mitigation, not a guarantee.
- No authentication or rate limiting; put it behind a gateway before exposing it.
- The React frontend from the prototype is not included.
