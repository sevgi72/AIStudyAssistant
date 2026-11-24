"""All settings in one place. Values come from environment variables (.env locally,
Secrets on Streamlit Cloud / Hugging Face). Nothing secret is written in code."""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()  # loads .env if it exists (local development)
except ImportError:  # python-dotenv not installed -> just use real env variables
    pass


def _get_secret(name: str) -> str | None:
    """Read a setting from env first, then from Streamlit secrets (if Streamlit is used)."""
    value = os.getenv(name)
    if value:
        return value.strip()
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:  # Streamlit not installed / no secrets file -> ignore
        pass
    return None


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def get_api_key() -> str | None:
    return _get_secret("GEMINI_API_KEY")


MODEL_NAME = _get_secret("GEMINI_MODEL") or "gemini-3.8-flash"
# Used automatically when the main model is busy / overloaded
FALLBACK_MODEL = _get_secret("GEMINI_FALLBACK_MODEL") or "gemini-3.5-flash"

# Limits that protect the free API quota and keep the app fast
MAX_FILE_MB = _get_int("MAX_FILE_MB", 20)          # biggest PDF we accept
MAX_PAGES = _get_int("MAX_PAGES", 150)             # pages after this are ignored
CHUNK_CHARS = _get_int("CHUNK_CHARS", 6000)        # size of one piece sent to the AI
MAX_EXPLAIN_CHUNKS = _get_int("MAX_EXPLAIN_CHUNKS", 8)  # AI calls for one explanation
EXPLAIN_CHUNK_CHARS = _get_int("EXPLAIN_CHUNK_CHARS", 2500)  # smaller pieces = first answer appears faster
MAX_SLIDES_PER_EXPLAIN = _get_int("MAX_SLIDES_PER_EXPLAIN", 15)  # biggest slide range for one explanation
TOP_K_CHUNKS = _get_int("TOP_K_CHUNKS", 3)         # chunks used for quiz / Q&A

# AI call behaviour
TEMPERATURE = 0.3        # low = more factual, less creative
MAX_RETRIES = 3       # tries per model when the API is busy or rate-limited
REQUEST_TIMEOUT_SECONDS = _get_int("REQUEST_TIMEOUT_SECONDS", 90)  # stop waiting after this
RETRY_BASE_SECONDS = 2   # waits 2s, then 4s between retries
