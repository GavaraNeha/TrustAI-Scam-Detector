"""
Thin wrapper around two free LLM APIs: Groq (primary, fast, generous
rate limits) and Gemini (fallback if Groq errors or rate-limits).

Both are called with a system prompt that forces JSON-only output,
and the response is parsed as JSON. If both fail, chat_json returns
None and the caller must handle that (usually: mark that stage as
"couldn't verify" rather than crashing).

Model names are read from .env (GROQ_MODEL / GEMINI_MODEL) rather
than hardcoded, since providers retire model names over time --
check your provider's current model list if a call starts failing
with a "model not found" error.
"""
import json
import re
import requests

import config


def _extract_json(text):
    """LLMs sometimes wrap JSON in prose or code fences. Pull the
    first {...} or [...] block out before parsing."""
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _groq_chat(system_prompt, user_prompt):
    if not config.GROQ_API_KEY:
        raise RuntimeError("No GROQ_API_KEY set")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={
            "model": config.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _gemini_chat(system_prompt, user_prompt):
    if not config.GEMINI_API_KEY:
        raise RuntimeError("No GEMINI_API_KEY set")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    resp = requests.post(
        url,
        json={
            "contents": [
                {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
            ]
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def chat_json(system_prompt, user_prompt):
    """
    Calls Groq first, falls back to Gemini on any error (network,
    rate limit, bad key). Returns a parsed dict/list, or None if
    both providers failed or returned unparseable output.
    """
    forced_system = (
        system_prompt
        + "\n\nRespond with ONLY valid JSON. No prose, no markdown code fences, no explanation."
    )

    for call in (_groq_chat, _gemini_chat):
        try:
            raw = call(forced_system, user_prompt)
            parsed = _extract_json(raw)
            if parsed is not None:
                return parsed
        except Exception:
            continue

    return None
