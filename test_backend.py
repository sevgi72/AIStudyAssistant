"""Manual test with the REAL AI (uses your API key and a little free quota).

Usage:  python test_backend.py path/to/lecture.pdf
"""
import sys
import time

from backend.ai_client import AIError, answer_question, explain_slides_stream, make_quiz
from backend.pdf_reader import PdfError, chunks_for_range, make_chunks, read_pdf


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_backend.py path/to/lecture.pdf")
        sys.exit(1)
    try:
        pages = read_pdf(sys.argv[1])
        chunks = make_chunks(pages)
        print(f"OK: {len(pages)} pages -> {len(chunks)} chunks\n")

        print("=== EXPLANATION (slides 1-3, each part shown when ready) ===")
        print("Waiting for the AI...", flush=True)
        start = time.time()
        for part in explain_slides_stream(chunks_for_range(pages, 1, 3)):
            print(part[:1500])
            print(f"--- part ready after {time.time() - start:.0f}s ---\n", flush=True)

        print("=== QUIZ ===")
        print("Waiting for the AI...", flush=True)
        print(make_quiz(chunks, n=3), "\n")

        print("=== Q&A ===")
        print("Waiting for the AI...", flush=True)
        print(answer_question(chunks, "What is the main topic of these slides?", "Azerbaijani"))
    except (PdfError, AIError) as e:
        print("ERROR:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
