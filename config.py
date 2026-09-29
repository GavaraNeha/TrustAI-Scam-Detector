import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")

# Company research is cached here so repeat lookups don't burn free-tier
# search/LLM quota. Safe to delete this file any time to clear the cache.
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cache.sqlite3")

# How long a cached company lookup stays valid, in hours.
CACHE_TTL_HOURS = 168  # 1 week
