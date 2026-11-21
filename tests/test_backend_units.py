"""Automatic tests for the backend. They do NOT call the real AI (a fake client is used),
so they are free and work without an API key.

Run:  python -m pytest -q
"""
import io

import pytest
from reportlab.pdfgen import canvas

from backend import ai_client, config
from backend.ai_client import AIError
from backend.pdf_reader import PdfError, chunks_for_range, make_chunks, read_pdf
from backend.retrieval import find_relevant_chunks


# ---------- helpers ----------

def make_pdf(pages_text):
    """Create a real PDF in memory with one page per string."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for text in pages_text:
        y = 800
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 15
        c.showPage()
    c.save()
    return buf.getvalue()


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []
        self.models_used = []

    def generate_content(self, model, contents, config=None):
        self.prompts.append(contents)
        self.models_used.append(model)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return FakeResponse(reply)


class FakeClient:
    def __init__(self, replies):
        self.models = FakeModels(replies)


class FakeAPIError(Exception):
    def __init__(self, code):
        super().__init__(f"{code} error")
        self.code = code


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(ai_client.time, "sleep", lambda s: None)
    monkeypatch.setattr(config, "MODEL_NAME", "main-model")
    monkeypatch.setattr(config, "FALLBACK_MODEL", "backup-model")
    monkeypatch.setattr(config, "MAX_RETRIES", 2)
    yield
    ai_client.set_client(None)


# ---------- pdf_reader ----------

def test_read_pdf_from_bytes_and_filelike():
    data = make_pdf(["Slide one: probability basics", "Slide two: random variables"])
    assert read_pdf(data)[1] == "Slide two: random variables"
    assert len(read_pdf(io.BytesIO(data))) == 2


def test_read_pdf_from_path(tmp_path):
    path = tmp_path / "lecture.pdf"
    path.write_bytes(make_pdf(["Hello lecture text here"]))
    assert read_pdf(str(path)) == ["Hello lecture text here"]


@pytest.mark.parametrize("bad, message", [
    (b"", "empty"),
    (b"hello world, not a pdf", "not a PDF"),
    (b"%PDF-1.4 broken", "could not be opened"),
])
def test_read_pdf_bad_files(bad, message):
    with pytest.raises(PdfError, match=message):
        read_pdf(bad)


def test_read_pdf_no_text():
    with pytest.raises(PdfError, match="No text"):
        read_pdf(make_pdf(["", ""]))


def test_read_pdf_too_big(monkeypatch):
    monkeypatch.setattr(config, "MAX_FILE_MB", 0)
    with pytest.raises(PdfError, match="maximum"):
        read_pdf(make_pdf(["some text on the page"]))


def test_read_pdf_page_limit(monkeypatch):
    monkeypatch.setattr(config, "MAX_PAGES", 2)
    pages = read_pdf(make_pdf(["page a text", "page b text", "page c text"]))
    assert len(pages) == 2


def test_missing_file():
    with pytest.raises(PdfError, match="not found"):
        read_pdf("does_not_exist.pdf")


# ---------- chunking ----------

def test_chunks_keep_slide_numbers_and_limit():
    pages = ["a" * 300, "", "b" * 300, "c" * 300]
    chunks = make_chunks(pages, max_chars=700)
    joined = "\n".join(chunks)
    assert "Slide 1" in joined and "Slide 3" in joined and "Slide 4" in joined
    assert "Slide 2 " not in joined  # empty page skipped
    assert all(len(c) <= 700 for c in chunks)


def test_long_page_is_split():
    chunks = make_chunks(["x" * 2000], max_chars=500)
    assert len(chunks) >= 4
    assert "(part 2)" in "\n".join(chunks)
    assert all(len(c) <= 500 for c in chunks)


# ---------- retrieval ----------

def test_retrieval_finds_relevant_chunk():
    chunks = ["--- Slide 1 ---\nIntro", "--- Slide 2 ---\nBayes theorem formula", "--- Slide 3 ---\nVariance"]
    assert find_relevant_chunks(chunks, "What is Bayes theorem?", top_k=1) == [chunks[1]]


def test_retrieval_fallback_when_no_match():
    chunks = ["one", "two", "three", "four"]
    assert find_relevant_chunks(chunks, "zebra", top_k=2) == ["one", "two"]


# ---------- ai_client ----------

def test_explain_slides_with_progress_and_limit(monkeypatch):
    monkeypatch.setattr(config, "MAX_EXPLAIN_CHUNKS", 2)
    fake = FakeClient(["part 1", "part 2"])
    ai_client.set_client(fake)
    progress = []
    result = ai_client.explain_slides(["c1", "c2", "c3"], on_progress=lambda d, t: progress.append((d, t)))
    assert "part 1" in result.text and "part 2" in result.text
    assert result.was_cut and result.chunks_used == 2 and result.chunks_total == 3
    assert progress == [(1, 2), (2, 2)]


def test_quiz_uses_start_and_end_of_pdf():
    fake = FakeClient(["Q1: ...\nA1: ..."])
    ai_client.set_client(fake)
    ai_client.make_quiz([f"chunk{i}" for i in range(10)], n=3)
    prompt = fake.models.prompts[0]
    assert "chunk0" in prompt and "chunk9" in prompt and "3 likely exam questions" in prompt


def test_answer_question_validation():
    ai_client.set_client(FakeClient([]))
    with pytest.raises(AIError, match="write a question"):
        ai_client.answer_question(["text"], "   ")
    with pytest.raises(AIError, match="no text"):
        ai_client.answer_question([], "hello")


def test_answer_question_language():
    fake = FakeClient(["Cavab"])
    ai_client.set_client(fake)
    assert ai_client.answer_question(["--- Slide 1 ---\nentropy"], "entropy?", "Azerbaijani") == "Cavab"
    assert "Answer in Azerbaijani" in fake.models.prompts[0]


def test_retry_then_success():
    fake = FakeClient([FakeAPIError(429), FakeAPIError(503), "ok"])
    ai_client.set_client(fake)
    assert ai_client.make_quiz(["text"]) == "ok"


def test_rate_limit_gives_friendly_error():
    ai_client.set_client(FakeClient([FakeAPIError(429)] * 4))
    with pytest.raises(AIError, match="limit"):
        ai_client.make_quiz(["text"])


def test_bad_key_not_retried():
    fake = FakeClient([FakeAPIError(403), "should not be used"])
    ai_client.set_client(fake)
    with pytest.raises(AIError, match="API key"):
        ai_client.make_quiz(["text"])
    assert len(fake.models.prompts) == 1


def test_empty_ai_answer():
    ai_client.set_client(FakeClient(["   "]))
    with pytest.raises(AIError, match="empty"):
        ai_client.make_quiz(["text"])


def test_missing_api_key(monkeypatch):
    ai_client.set_client(None)
    monkeypatch.setattr(config, "get_api_key", lambda: None)
    with pytest.raises(AIError, match="GEMINI_API_KEY"):
        ai_client.make_quiz(["text"])


def test_busy_main_model_switches_to_fallback():
    fake = FakeClient([FakeAPIError(503), FakeAPIError(503), "from backup"])
    ai_client.set_client(fake)
    assert ai_client.make_quiz(["text"]) == "from backup"
    assert fake.models.models_used == ["main-model", "main-model", "backup-model"]


def test_retired_model_goes_straight_to_fallback():
    fake = FakeClient([FakeAPIError(404), "ok"])
    ai_client.set_client(fake)
    assert ai_client.make_quiz(["text"]) == "ok"
    assert fake.models.models_used == ["main-model", "backup-model"]


def test_timeout_is_retried():
    fake = FakeClient([TimeoutError("read timed out"), "ok"])
    ai_client.set_client(fake)
    assert ai_client.make_quiz(["text"]) == "ok"


def test_both_models_busy_gives_busy_message():
    ai_client.set_client(FakeClient([FakeAPIError(503)] * 4))
    with pytest.raises(AIError, match="busy"):
        ai_client.make_quiz(["text"])


# ---------- slide range + streaming ----------

def test_range_keeps_real_slide_numbers():
    pages = [f"text of slide {i}" for i in range(1, 21)]
    joined = "\n".join(chunks_for_range(pages, 5, 7))
    assert "Slide 5" in joined and "Slide 7" in joined
    assert "Slide 4 " not in joined and "Slide 8 " not in joined
    assert "slide 6" in joined


def test_range_end_bigger_than_pdf_is_cut():
    pages = ["a slide", "b slide", "c slide"]
    assert "Slide 3" in "\n".join(chunks_for_range(pages, 2, 10))


@pytest.mark.parametrize("start, end, message", [
    (0, 3, "between 1 and"),
    (5, 2, "between 1 and"),
    (50, 60, "between 1 and"),
    ("a", 3, "whole numbers"),
    (1, 16, "at most 15"),
])
def test_range_invalid(start, end, message, monkeypatch):
    monkeypatch.setattr(config, "MAX_SLIDES_PER_EXPLAIN", 15)
    with pytest.raises(PdfError, match=message):
        chunks_for_range([f"slide {i}" for i in range(20)], start, end)


def test_range_without_text():
    with pytest.raises(PdfError, match="no text"):
        chunks_for_range(["intro text", "", ""], 2, 3)


def test_stream_gives_parts_one_by_one():
    fake = FakeClient(["part A", "part B"])
    ai_client.set_client(fake)
    stream = ai_client.explain_slides_stream(["c1", "c2"])
    assert next(stream) == "part A"
    assert len(fake.models.prompts) == 1  # part B not requested yet
    assert next(stream) == "part B"
