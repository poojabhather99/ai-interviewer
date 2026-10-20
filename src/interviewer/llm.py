"""LLM interface. `complete(prompt) -> str`. A deterministic offline model is the default."""

from __future__ import annotations

import os
from typing import Protocol


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


class OfflineLLM:
    """Deterministic stand-in so the app and tests run without credentials or network.

    It returns a templated follow-up question. It is not a model of interviewing quality.
    """

    def complete(self, prompt: str) -> str:
        if "TASK: QUESTION" in prompt:
            skill = _field(prompt, "SKILL")
            n = int(_field(prompt, "ASKED") or 0)
            ladder = [
                f"Explain the core concepts of {skill} in your own words.",
                f"Describe a project where you used {skill}. What was your specific role?",
                f"What trade-offs did you face when using {skill}, and how did you decide?",
                f"How would you test and monitor a production system built with {skill}?",
                f"Tell me about a failure involving {skill} and what you changed afterwards.",
            ]
            return ladder[min(n, len(ladder) - 1)]
        return "{}"


class GroqLLM:  # pragma: no cover - needs network and a key
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq

        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = model

    def complete(self, prompt: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0.3
        )
        return r.choices[0].message.content.strip()


class HFLLM:  # pragma: no cover - needs network and a token
    """Hugging Face Inference Providers via huggingface_hub (token read from HF_TOKEN)."""

    def __init__(self, model: str | None = None):
        from huggingface_hub import InferenceClient

        self.client = InferenceClient(token=os.environ["HF_TOKEN"])
        self.model = model or os.environ.get("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

    def complete(self, prompt: str) -> str:
        r = self.client.chat_completion(
            model=self.model, messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=400,
        )
        return r.choices[0].message.content.strip()


def _field(prompt: str, name: str) -> str:
    for line in prompt.splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip()
    return ""


def get_llm() -> LLM:
    if os.environ.get("GROQ_API_KEY"):
        return GroqLLM()
    if os.environ.get("HF_TOKEN"):
        return HFLLM()
    return OfflineLLM()
