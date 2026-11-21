# How the UI uses the backend

Copy this into `app.py` as a starting point:

```python
import streamlit as st
from backend.pdf_reader import read_pdf, make_chunks, chunks_for_range, PdfError
from backend.ai_client import explain_slides_stream, make_quiz, answer_question, AIError
from backend import config

st.title("AI Study Assistant")
uploaded = st.file_uploader("Upload lecture slides (PDF)", type="pdf")
if not uploaded:
    st.stop()

try:
    pages = read_pdf(uploaded)              # Streamlit UploadedFile works directly
    chunks = make_chunks(pages)             # whole PDF: used by quiz and Q&A
except PdfError as e:
    st.error(str(e))                        # messages are already user-friendly
    st.stop()
st.success(f"{len(pages)} slides loaded")

# ---- 1. Explain a slide range (fast: each part appears as soon as it is ready) ----
st.subheader("Explain slides")
col1, col2 = st.columns(2)
start = col1.number_input("From slide", 1, len(pages), 1)
end = col2.number_input("To slide", 1, len(pages), min(5, len(pages)))
st.caption(f"Up to {config.MAX_SLIDES_PER_EXPLAIN} slides at a time.")

if st.button("Explain"):
    try:
        range_chunks = chunks_for_range(pages, start, end)
        for part in explain_slides_stream(range_chunks):
            st.markdown(part)               # shown immediately, no waiting for all parts
        st.success("Done")
    except (PdfError, AIError) as e:
        st.error(str(e))

# ---- 2. Exam questions ----
st.subheader("Exam questions")
if st.button("Generate exam questions"):
    with st.spinner("Writing questions..."):
        try:
            st.markdown(make_quiz(chunks, n=5))
        except AIError as e:
            st.error(str(e))

# ---- 3. Ask a question ----
st.subheader("Ask about the slides")
lang = st.radio("Answer language", ["English", "Azerbaijani"], horizontal=True)
q = st.text_input("Your question")
if st.button("Ask") and q:
    with st.spinner("Thinking..."):
        try:
            st.markdown(answer_question(chunks, q, lang))
        except AIError as e:
            st.error(str(e))
```

## Functions

| Function | Returns | Errors |
|---|---|---|
| `read_pdf(file)` | `list[str]`, one item per slide | `PdfError` |
| `make_chunks(pages)` | `list[str]` for the whole PDF | none |
| `chunks_for_range(pages, start, end)` | `list[str]` for slides start..end (max 15 slides) | `PdfError` |
| `explain_slides_stream(chunks)` | generator: one Markdown part at a time | `AIError` |
| `explain_slides(chunks, on_progress=None)` | `ExplainResult` (all parts at once) | `AIError` |
| `make_quiz(chunks, n=5)` | `str` (Markdown) | `AIError` |
| `answer_question(chunks, question, language)` | `str`, language = `"English"` or `"Azerbaijani"` | `AIError` |

Note: one explanation part takes about 30–60 seconds. Always use `explain_slides_stream`
so the user sees results while waiting.
