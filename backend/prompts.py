"""Prompt templates. The data scientist can improve the wording here without touching
other code. Keep the {placeholders} the same."""

EXPLAIN_PROMPT = """You are a patient teacher for university students who study in English as a second language.
Explain the lecture slides below.

Rules:
- Start DIRECTLY with the first slide. No greeting, no introduction, no closing words.
- Go slide by slide. Use "## Slide N" as a Markdown heading (use the numbers from the text).
- For each slide, first write "English:" and explain in very simple English, as if to a beginner.
- Then write "Azərbaycanca:" and give the SAME full explanation in Azerbaijani.
  Put the English term in parentheses next to key terms, for example "ehtimal (probability)".
- Explain every technical term the slide uses.
- Write formulas as plain text (for example: a = b * c), not LaTeX.
- Only explain what is on the slides. Do not add extra topics.
- Skip slides that only contain a title or page number.

Slides:
{text}
"""

QUIZ_PROMPT = """You are a university examiner. Using ONLY the lecture slides below,
write {n} likely exam questions with short, correct answers.
Write BOTH the questions and the answers in English, even if the slides are in another language
(you may add the original term in parentheses).
Mix question types: definitions, "explain why", and small examples.

Start directly with Q1. Use exactly this format:
Q1: ...
A1: ...

Slides:
{text}
"""

QUESTION_PROMPT = """Answer the student's question using ONLY the lecture slides below.
Say which slide number(s) your answer comes from.
If the answer is not in the slides, say clearly that the slides do not cover it.
Answer in {language}, in simple words. Start directly with the answer, no greeting.

Question: {question}

Slides:
{text}
"""
