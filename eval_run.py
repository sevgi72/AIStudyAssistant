"""Evaluation runner: runs the REAL AI and saves the FULL output to results/<name>.md

Usage:
  python eval_run.py test_pdfs\\dsu.pdf --start 2 --end 5 --n 5 --q "your question"
  python eval_run.py test_pdfs\\dsu.pdf --only qa --q "question 1" --q "question 2"
"""
import argparse
import os
import time

from backend.ai_client import AIError, answer_question, explain_slides_stream, make_quiz
from backend.pdf_reader import PdfError, chunks_for_range, make_chunks, read_pdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--start", type=int, default=2, help="first slide to explain")
    ap.add_argument("--end", type=int, default=5, help="last slide to explain")
    ap.add_argument("--n", type=int, default=5, help="number of quiz questions")
    ap.add_argument("--q", action="append", default=[], help="question (repeat for more)")
    ap.add_argument("--lang", default="Azerbaijani", help="language of the Q&A answers")
    ap.add_argument("--only", choices=["explain", "quiz", "qa"], help="run just one part")
    args = ap.parse_args()

    def run(part):
        return args.only in (None, part)

    name = os.path.splitext(os.path.basename(args.pdf))[0]
    suffix = f"_{args.only}" if args.only else ""
    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", f"{name}{suffix}.md")
    questions = args.q or ["What is the main topic of these slides?"]

    with open(out_path, "w", encoding="utf-8") as f:

        def log(text=""):
            print(text, flush=True)
            f.write(text + "\n")
            f.flush()

        try:
            pages = read_pdf(args.pdf)
            chunks = make_chunks(pages)
            log(f"# {name}")
            log(f"Pages: {len(pages)}, chunks: {len(chunks)}\n")

            if run("explain"):
                log(f"## EXPLANATION (slides {args.start}-{args.end})")
                start = time.time()
                for part in explain_slides_stream(chunks_for_range(pages, args.start, args.end)):
                    log(part)
                    log(f"\n--- part ready after {time.time() - start:.0f}s ---\n")

            if run("quiz"):
                log(f"## QUIZ ({args.n} questions)")
                log(make_quiz(chunks, n=args.n))
                log()

            if run("qa"):
                log(f"## Q&A (answer language: {args.lang})")
                for q in questions:
                    log(f"**Question:** {q}")
                    log(answer_question(chunks, q, args.lang))
                    log()
        except (PdfError, AIError) as e:
            log(f"ERROR: {e}")

    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()