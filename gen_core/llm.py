"""Minimal Anthropic Messages API client, stdlib only (same pattern as scripts/judge_gpt.py).

Every content agent in gen_core.agents takes a `call: Callable[[str], str]` instead of importing
this module directly, so tests and manual/no-key runs can inject a fake.
"""
from __future__ import annotations

import json
import os
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


def make_caller(model: str = DEFAULT_MODEL, system: str | None = None, max_tokens: int = 4096):
    """Return a `call(prompt) -> text` closure backed by one real model."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    def call(prompt: str) -> str:
        body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(body).encode(),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            reply = json.load(resp)
        return "".join(b["text"] for b in reply["content"] if b.get("type") == "text")

    return call
