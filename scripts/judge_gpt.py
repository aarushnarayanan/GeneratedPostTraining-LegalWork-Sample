"""Second judge for bench_core.run_eval --judge-cmd, using GPT-5.5.

Reads the grading prompt on stdin, calls the OpenAI Chat Completions API, and prints the
model's reply on stdout, matching the --judge-cmd contract in bench_core/run_eval.py.

Usage:
    export OPENAI_API_KEY="<API key goes here>"
    python -m bench_core.run_eval --task <id> --output <dir> \
        --judge-cmd "python scripts/judge_gpt.py"

Stdlib only, no new dependency, matching the rest of this benchmark.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

MODEL = "gpt-5.5"
API_URL = "https://api.openai.com/v1/chat/completions"


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set (API key goes here)", file=sys.stderr)
        return 1

    prompt = sys.stdin.read()
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        reply = json.load(resp)
    print(reply["choices"][0]["message"]["content"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
