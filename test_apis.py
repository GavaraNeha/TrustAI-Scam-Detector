"""
Run this directly to see the REAL error each API gives, instead of
the silent fallback the main app shows. Put this file in your
project root (next to app.py) and run: python test_apis.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

import requests

groq_key = os.getenv("GROQ_API_KEY", "")
gemini_key = os.getenv("GEMINI_API_KEY", "")
tavily_key = os.getenv("TAVILY_API_KEY", "")
vt_key = os.getenv("VIRUSTOTAL_API_KEY", "")

print("Keys loaded:")
print("  GROQ_API_KEY set:", bool(groq_key), "len:", len(groq_key))
print("  GEMINI_API_KEY set:", bool(gemini_key), "len:", len(gemini_key))
print("  TAVILY_API_KEY set:", bool(tavily_key), "len:", len(tavily_key))
print("  VIRUSTOTAL_API_KEY set:", bool(vt_key), "len:", len(vt_key))
print()

print("--- Testing Groq ---")
try:
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}"},
        json={
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [{"role": "user", "content": "Say hello in one word."}],
        },
        timeout=20,
    )
    print("Status:", resp.status_code)
    print("Body:", resp.text[:500])
except Exception as e:
    print("EXCEPTION:", repr(e))

print()
print("--- Testing Gemini ---")
try:
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
    resp = requests.post(
        url,
        json={"contents": [{"role": "user", "parts": [{"text": "Say hello in one word."}]}]},
        timeout=20,
    )
    print("Status:", resp.status_code)
    print("Body:", resp.text[:500])
except Exception as e:
    print("EXCEPTION:", repr(e))

print()
print("--- Testing Tavily ---")
try:
    resp = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": tavily_key, "query": "test", "max_results": 1},
        timeout=20,
    )
    print("Status:", resp.status_code)
    print("Body:", resp.text[:500])
except Exception as e:
    print("EXCEPTION:", repr(e))
