"""Transparent heuristic rubric. It scores answer *form*, not technical correctness."""

from __future__ import annotations

import re

STRUCTURE = ("because", "therefore", "for example", "for instance", "trade-off", "tradeoff",
             "however", "so that", "as a result", "instead")
HEDGES = ("i don't know", "not sure", "no idea", "maybe", "i guess")


def score_answer(answer: str, skill: str) -> dict[str, float]:
    words = re.findall(r"[A-Za-z0-9']+", answer)
    n = len(words)
    low = answer.lower()
    depth = min(n / 80, 1.0)  # ~80 words treated as a full answer
    structure = min(sum(m in low for m in STRUCTURE) / 3, 1.0)
    specifics = min(len(re.findall(r"\b\d+(?:\.\d+)?%?\b", answer)) / 2, 1.0)
    relevance = 1.0 if skill.lower() in low else 0.5 if n else 0.0
    hedge_penalty = 0.25 if any(h in low for h in HEDGES) else 0.0
    overall = max(0.0, 0.35 * depth + 0.25 * structure + 0.2 * specifics + 0.2 * relevance
                  - hedge_penalty)
    return {"depth": round(depth, 2), "structure": round(structure, 2),
            "specifics": round(specifics, 2), "relevance": round(relevance, 2),
            "overall": round(overall, 2)}
