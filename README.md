# AI Study Assistant 

> Built for **Build Your First AI App 2026** (Devpost, Yasir Insights)

## Problem
Many students in Azerbaijan study in English-taught programs. Lecture slides are often short,
full of technical terms, and written in a second language, so they are hard to understand
and hard to prepare for exams from.

## Solution
Upload your lecture slides (PDF) and the app:
1. **Explains the slides you choose** (for example slides 1–10), and shows each part as soon as it is ready: first in simple English, then the same explanation in Azerbaijani,
   with English terms in parentheses.
2. **Generates likely exam questions** with answers.
3. **Answers your questions** about the slides, in English or Azerbaijani, and says which slide the answer comes from.

**Who benefits:** university students who study in English as a second language.

## Live demo
🔗 _add the deployed link here_

## Screenshots
_add 3–4 screenshots here_

## How it works

```
PDF upload ──► text extraction (pypdf) ──► chunks with slide numbers
                                              │
              ┌───────────────────────────────┼─────────────────────────┐
              ▼                               ▼                         ▼
      Explain (each chunk)        Quiz (chunks from start,     Q&A (keyword retrieval
                                   middle and end)              picks relevant chunks)
              └───────────────► Google Gemini API ◄────────────────────┘
                                      │
                                      ▼
                              Streamlit web UI
```

## AI implementation
- **Model:** Google Gemini (`gemini-3.8-flash` by default, free tier via Google AI Studio).
- **Prompting:** separate prompts for explanation, quiz and Q&A (`backend/prompts.py`).
  The prompts tell the model to use only the slide content, to reduce made-up answers (hallucinations).
- **Chunking:** long PDFs are split into pieces of about 6000 characters, and each piece keeps its slide numbers.
- **Retrieval (light RAG):** for Q&A, the chunks that share the most keywords with the question are sent to the model.
- **Reliability:** automatic retries with waiting (exponential backoff) when the API is busy or rate-limited,
  and clear error messages for wrong keys, empty or scanned PDFs, and files that are too big.

## Tech stack
Python · Streamlit · Google Gemini API (`google-genai`) · pypdf · pytest · GitHub Actions

## Project structure
```
backend/
  config.py       settings and limits (read from .env / Secrets)
  pdf_reader.py   PDF to text, chunking
  retrieval.py    picks relevant chunks for Q&A
  prompts.py      prompt templates
  ai_client.py    Gemini connection: explain_slides, make_quiz, answer_question
tests/            automatic tests (fake AI, no key needed)
test_backend.py   manual test with the real AI
app.py            Streamlit UI
```

## Run it locally
```bash
git clone <repo-url>
cd ai-study-assistant
python -m venv venv
# Windows: venv\Scripts\activate     Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
# open .env and paste your free key from https://aistudio.google.com/apikey
streamlit run app.py
```

Test the backend without the UI:
```bash
python test_backend.py path/to/lecture.pdf
```

Run the automatic tests (free, no API key needed):
```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Limits
- PDFs must contain selectable text (scanned images are not supported yet).
- One explanation covers up to 15 slides, so answers come fast and stay inside the free API quota.
  You can change this in `backend/config.py`.

## Team and contributions
| Member | Role | Contribution |
|---|---|---|
| Sevgi Farajli | Backend developer | PDF processing, chunking, Gemini integration, retrieval, error handling, tests, CI |
| _name_ | Frontend developer | Streamlit UI, deployment |
| _name_ | Data scientist | Prompt design, quality evaluation |

**AI-assisted development:** we used Claude (Anthropic) as a coding assistant for parts of the backend code
and tests. All code was reviewed, tested and integrated by the team.

## Credits
- [Google Gemini API](https://ai.google.dev/)
- [pypdf](https://github.com/py-pdf/pypdf)
- [Streamlit](https://streamlit.io/)
