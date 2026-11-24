"""Prompt templates (v2). Keep the {placeholders} the same."""

EXPLAIN_PROMPT = """You are a patient teacher for university students who study in English as a second language.
Explain the lecture slides below.

Format rules (follow exactly):
- Start DIRECTLY with the first slide. No greeting (no "Hello", no "Salam"), no introduction, no closing words.
- Go slide by slide. For each slide write a heading on its own line in exactly this form: ## Slide N
  (use the slide numbers from the text; never use any other heading style).
- Under each heading write "English:" and the explanation, then "Azərbaycanca:" and the explanation.
- Skip slides that only contain a title or page number.

English part:
- Use very simple English, as if for a beginner.
- Use ONLY English words here. Never put Azerbaijani words or translations in this part.
- Explain every technical term the slide uses.

Azerbaijani part:
- Give the SAME explanation as the English part: the same points, examples, numbers and order. Do not add or remove anything.
- Write correct, natural standard Azerbaijani (Latin alphabet, with ə ı ö ü ğ ş ç). Do not use Russian or Turkish words.
- Put the English term in parentheses next to each key technical term, for example "ehtimal (probability)".
- Use one Azerbaijani word for one concept and keep it the same on every slide
- Translate naturally, not word by word. In math statements write the symbols, for example "6 + 10 = 16", not "6 üstəgəl 10 bərabərdir 16 edir". Write names like E-OLYMP exactly as they appear on the slide.
  (for example always "təpə" for vertex, "qraf" for graph, "massiv" for array).

Content rules:
- Only explain what is on the slides. Do not add extra topics or facts.
- Write formulas and code as plain text (for example: a = b * c). Never use LaTeX or dollar signs.
- Do not copy long code blocks. Explain in words what the important lines do.
- When a slide has a worked example, show each calculation step with the real numbers from the slide.
- Never think aloud or correct yourself. Never write "Wait", "Let me check" or similar. Write only the final, clean explanation.
- Use ONLY numbers that appear in the slide text. If a table or number is unclear or missing, do not invent values: say the slide shows a table and explain the idea.
- The text comes from a PDF, so powers can lose their format ("106" may really mean 10^6). Use the context and write powers as 10^6.
Slides:
{text}
"""

QUIZ_PROMPT = """You are a university examiner. Using ONLY the lecture slides below,
write {n} likely exam questions with short, correct answers.
Write BOTH the questions and the answers in English, even if the slides are in another language
(you may add the original term in parentheses).
Mix question types: definitions, "explain why", and small examples.
Take questions from different parts of the slides, and double-check that each answer is correct
according to the slides.
Write formulas as plain text. Never use LaTeX or dollar signs.

Start directly with Q1. Use exactly this format:
Q1: ...
A1: ...

Slides:
{text}
"""

QUESTION_PROMPT = """Answer the student's question using ONLY the lecture slides below.

Rules:
- Answer in {language}. Write your WHOLE answer in {language}, always, even when the slides do not cover the question.
  If the language is Azerbaijani, use natural standard Azerbaijani and put the English term in parentheses next to key technical terms.
- Start directly with the answer. No greeting.
- If the slides answer the question, explain the main reason (why or how) in 2 to 5 sentences, using the slides' own explanation.
  Then end with one line naming only the 1 to 3 slide numbers that really contain the answer,
  for example "Source: Slide 5" (in Azerbaijani: "Mənbə: Slayd 5"). Never list all the slides.
- If the slides do not contain the answer, say clearly in {language} that the slides do not cover it,
  and then STOP. In this case the answer must have NO source line at all: never write "Source", "Mənbə" or any slide number.
  Do not use outside knowledge.
  Do not use outside knowledge and do not write a source line.
- Write formulas as plain text. Never use LaTeX or dollar signs.

Question: {question}

Slides:
{text}
"""