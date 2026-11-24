import glob
from pypdf import PdfReader

for f in sorted(glob.glob("test_pdfs/*.pdf")):
    r = PdfReader(f)
    n = len(r.pages)
    chars = sum(len(p.extract_text() or "") for p in r.pages)
    print(f"{f}: {n} pages, {chars} chars, {chars // max(n, 1)} chars/page")