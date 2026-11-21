"""Simple retrieval: pick the chunks most related to a question (keyword overlap).

This is a light version of RAG (Retrieval-Augmented Generation) with no extra libraries.
The data scientist can replace `find_relevant_chunks` with an embeddings-based version
later; the rest of the code does not need to change.
"""
from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on", "for", "and",
    "or", "what", "how", "why", "which", "who", "does", "do", "it", "this", "that",
    "with", "as", "be", "by", "can", "explain", "about", "me", "i", "you",
    # Azerbaijani
    "nə", "nədir", "necə", "niyə", "hansı", "və", "ilə", "bu", "o", "bir", "üçün",
    "izah", "et", "edin", "mənə", "haqqında",
}


def _words(text: str) -> list[str]:
    tokens = re.findall(r"\w+", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def find_relevant_chunks(chunks: list[str], question: str, top_k: int = 3) -> list[str]:
    """Return up to `top_k` chunks that share the most words with the question,
    kept in their original order. If nothing matches, return the first chunks."""
    if not chunks:
        return []
    q_words = set(_words(question))
    if not q_words:
        return chunks[:top_k]

    scores = []
    for index, chunk in enumerate(chunks):
        counts = Counter(_words(chunk))
        score = sum(counts[w] for w in q_words)
        scores.append((score, index))

    best = [i for s, i in sorted(scores, key=lambda x: (-x[0], x[1])) if s > 0][:top_k]
    if not best:
        return chunks[:top_k]
    return [chunks[i] for i in sorted(best)]
