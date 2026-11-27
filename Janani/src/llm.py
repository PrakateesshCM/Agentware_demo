import json
import os
import re

import ollama
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("LLM_MODEL", "qwen3.5:4b")
OPTIONS = {"temperature": 0}          # add "num_gpu": 0 here if CUDA crashes


def ask_json(system: str, user: str) -> dict:
    """Ask the model for JSON and return it as a dict. Raises ValueError if unusable."""
    kwargs = dict(
        model=MODEL,
        format="json",
        options=OPTIONS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    try:
        res = ollama.chat(think=False, **kwargs)   # skip "thinking" output if supported
    except TypeError:
        res = ollama.chat(**kwargs)

    text = res.message.content or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"model returned invalid JSON: {text[:120]}") from e