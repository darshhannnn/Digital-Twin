"""
llm.py
------
Shared Ollama client for all LLM calls.
Provides JSON-aware prompting with retry + repair logic.
"""

import json
import re
import ollama
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ollama.Client(host=config.OLLAMA_BASE_URL)
    return _client


def call_llm(prompt: str, temperature: float = 0.3, retries: int = 2) -> str | None:
    """
    Send a prompt to Ollama and return the raw text response.
    Strips <think> tags if present.
    """
    client = _get_client()

    for attempt in range(retries + 1):
        try:
            response = client.generate(
                model=config.OLLAMA_MODEL,
                prompt=prompt,
                options={"temperature": temperature}
            )
            raw = (response.response or "").strip()
            if not raw:
                continue

            if "<think>" in raw:
                end = raw.find("</think>")
                if end != -1:
                    raw = raw[end + 8:].strip()
                else:
                    raw = raw.split("<think>")[-1].strip()

            return raw
        except Exception as e:
            print(f"  [LLM] Attempt {attempt + 1} failed: {e}")
    return None


def call_llm_json(prompt: str, temperature: float = 0.3, retries: int = 3) -> dict | None:
    """
    Call Ollama and parse the response as JSON.
    Retries with increasingly explicit JSON instructions on failure.
    """
    client = _get_client()

    for attempt in range(retries):
        extra = ""
        if attempt > 0:
            extra = (
                "\n\nIMPORTANT: Respond ONLY with valid JSON. "
                "No markdown fences, no explanation, no <think> tags. "
                "Just the raw JSON object or array."
            )

        full_prompt = prompt + extra

        try:
            response = client.generate(
                model=config.OLLAMA_MODEL,
                prompt=full_prompt,
                options={"temperature": temperature}
            )
            raw = (response.response or "").strip()
            if not raw:
                continue

            if "<think>" in raw:
                end = raw.find("</think>")
                if end != -1:
                    raw = raw[end + 8:].strip()
                else:
                    raw = raw.split("<think>")[-1].strip()

            raw = _extract_json(raw)
            if raw:
                return json.loads(raw)
        except json.JSONDecodeError:
            if attempt < retries - 1:
                print(f"  [LLM] JSON parse failed (attempt {attempt + 1}), retrying...")
            continue
        except Exception as e:
            print(f"  [LLM] Attempt {attempt + 1} failed: {e}")
            continue

    print("  [LLM] All attempts failed to produce valid JSON.")
    return None


def _extract_json(text: str) -> str | None:
    """Try to extract a JSON object or array from text that may contain markdown fences."""
    text = text.strip()

    if text.startswith("{") or text.startswith("["):
        return text

    patterns = [
        (r"```json\s*\n?(.*?)\n?\s*```", re.DOTALL),
        (r"```\s*\n?(.*?)\n?\s*```", re.DOTALL),
    ]
    for pattern, flags in patterns:
        match = re.search(pattern, text, flags)
        if match:
            candidate = match.group(1).strip()
            if candidate.startswith("{") or candidate.startswith("["):
                return candidate

    start = -1
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            break
    if start == -1:
        return None

    depth = 0
    close = "}" if text[start] == "{" else "]"
    for i in range(start, len(text)):
        if text[i] in "{[":
            depth += 1
        elif text[i] in "}]":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None
