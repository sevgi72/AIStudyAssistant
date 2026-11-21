"""AI connection (Google Gemini API).

The UI should only use the three public functions at the bottom:
    explain_slides(chunks, on_progress=None) -> ExplainResult
    explain_slides_stream(chunks)            -> yields each part when ready
    make_quiz(chunks, n=5)                   -> str
    answer_question(chunks, question, language="English") -> str

All of them raise AIError with a message that can be shown directly to the user.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from backend import config, prompts
from backend.retrieval import find_relevant_chunks


class AIError(Exception):
    """A user-friendly error: the message can be shown directly in the UI."""


_client = None  # created once, on first use


def _get_client():
    global _client
    if _client is None:
        key = config.get_api_key()
        if not key:
            raise AIError(
                "GEMINI_API_KEY is missing. Add it to the .env file (local) "
                "or to Secrets (Streamlit Cloud / Hugging Face)."
            )
        try:
            from google import genai
        except ImportError as e:
            raise AIError("The 'google-genai' package is not installed. Run: pip install -r requirements.txt") from e
        # timeout is in milliseconds; without it a stuck request can wait forever
        _client = genai.Client(
            api_key=key,
            http_options={"timeout": config.REQUEST_TIMEOUT_SECONDS * 1000},
        )
    return _client


def set_client(client) -> None:
    """Replace the real client (used by tests with a fake client)."""
    global _client
    _client = client


def _error_code(error: Exception) -> int | None:
    code = getattr(error, "code", None) or getattr(error, "status_code", None)
    if isinstance(code, int):
        return code
    text = str(error)
    for c in (429, 500, 503, 401, 403, 400, 404):
        if str(c) in text:
            return c
    return None


def _friendly_message(code: int | None, error: Exception) -> str:
    if code == 429:
        return "The free AI limit was reached. Please wait a minute and try again."
    if code in (401, 403):
        return "The API key is not valid. Check GEMINI_API_KEY."
    if code == 404:
        return f"The model '{config.MODEL_NAME}' was not found. Change GEMINI_MODEL in the settings."
    if code == 400:
        return f"The AI could not process this request: {error}"
    if code in (500, 503):
        return "The AI service is busy right now. Please try again in a moment."
    return f"AI request failed: {error}"


def _models_to_try() -> list[str]:
    models = [config.MODEL_NAME]
    if config.FALLBACK_MODEL and config.FALLBACK_MODEL != config.MODEL_NAME:
        models.append(config.FALLBACK_MODEL)
    return models


def _ask(prompt: str) -> str:
    """Send one prompt and return the text.

    For each model (main, then fallback): try up to MAX_RETRIES times when the API is
    busy, rate-limited or times out. Wrong key / bad request errors stop immediately.
    """
    client = _get_client()
    last_error: Exception | None = None

    for model in _models_to_try():
        for attempt in range(config.MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": config.TEMPERATURE},
                )
                text = (getattr(response, "text", None) or "").strip()
                if not text:
                    raise AIError("The AI returned an empty answer (it may have been blocked). Try again.")
                return text
            except AIError:
                raise
            except Exception as e:  # network / API errors
                last_error = e
                code = _error_code(e)
                if code in (400, 401, 403):
                    raise AIError(_friendly_message(code, e)) from e  # retrying won't help
                if code == 404:
                    break  # this model is not available -> try the fallback model
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BASE_SECONDS * (2 ** attempt))

    raise AIError(_friendly_message(_error_code(last_error), last_error)) from last_error


def _check_chunks(chunks: list[str]) -> None:
    if not chunks or not any(c.strip() for c in chunks):
        raise AIError("There is no text to send to the AI. Upload a PDF first.")


# ---------- Public functions used by the UI ----------

@dataclass
class ExplainResult:
    text: str              # the full explanation (Markdown)
    chunks_used: int       # how many chunks were explained
    chunks_total: int      # how many chunks the PDF had
    was_cut: bool          # True if the PDF was longer than the limit


def explain_slides(
    chunks: list[str],
    on_progress: Callable[[int, int], None] | None = None,
) -> ExplainResult:
    """Bilingual (English + Azerbaijani) slide-by-slide explanation.

    Sends each chunk as a separate request (max MAX_EXPLAIN_CHUNKS, to protect the
    free quota). `on_progress(done, total)` is called after each chunk so the UI can
    show a progress bar.
    """
    _check_chunks(chunks)
    selected = chunks[: config.MAX_EXPLAIN_CHUNKS]
    parts = []
    for i, chunk in enumerate(selected, start=1):
        parts.append(_ask(prompts.EXPLAIN_PROMPT.format(text=chunk)))
        if on_progress:
            on_progress(i, len(selected))
    return ExplainResult(
        text="\n\n---\n\n".join(parts),
        chunks_used=len(selected),
        chunks_total=len(chunks),
        was_cut=len(chunks) > len(selected),
    )


def explain_slides_stream(chunks: list[str]):
    """Same as explain_slides, but gives back each part AS SOON AS it is ready
    (a generator). The UI can show part 1 while part 2 is still being written:

        for part in explain_slides_stream(chunks):
            st.markdown(part)
    """
    _check_chunks(chunks)
    for chunk in chunks[: config.MAX_EXPLAIN_CHUNKS]:
        yield _ask(prompts.EXPLAIN_PROMPT.format(text=chunk))


def make_quiz(chunks: list[str], n: int = 5) -> str:
    """Likely exam questions with answers (English). Uses chunks spread across the
    whole PDF (start, middle, end) so the quiz is not only about the first slides."""
    _check_chunks(chunks)
    n = max(1, min(int(n), 20))
    k = config.TOP_K_CHUNKS
    if len(chunks) <= k:
        picked = chunks
    else:
        step = (len(chunks) - 1) / (k - 1) if k > 1 else 0
        picked = [chunks[round(i * step)] for i in range(k)]
    return _ask(prompts.QUIZ_PROMPT.format(n=n, text="\n\n".join(picked)))


def answer_question(chunks: list[str], question: str, language: str = "English") -> str:
    """Answer a question about the PDF using only the most relevant chunks."""
    _check_chunks(chunks)
    question = (question or "").strip()
    if not question:
        raise AIError("Please write a question.")
    if len(question) > 1000:
        raise AIError("The question is too long (max 1000 characters).")
    if language not in ("English", "Azerbaijani"):
        language = "English"
    relevant = find_relevant_chunks(chunks, question, top_k=config.TOP_K_CHUNKS)
    return _ask(prompts.QUESTION_PROMPT.format(
        language=language, question=question, text="\n\n".join(relevant)
    ))
