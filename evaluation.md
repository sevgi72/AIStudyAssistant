\# Evaluation



Scores 1-5 (5 = best), written as baseline (prompts v1) → final (prompts v2.4).

One run per PDF, 5 DSA lecture PDFs, one rater. Correctness, Azerbaijani quality and quiz

scores are manual and provisional. "–" means no baseline result was recorded.



| PDF | Slides | Correctness | Azerbaijani quality | Format followed | Quiz correct | Q\&A correct + right slide | Longest part (s) | Problems (final) |

|-----|--------|-------------|---------------------|-----------------|--------------|---------------------------|------------------|------------------|

| dsu | 2-5 | 4 → 4 | 3 → 3 | 3 → 5 | 5/5 → 5/5 (verify Q4-Q5) | weak, wrong sources → honest + Slide 5 | 153 → 14 | Over-explains basic terms on slide 5; typos ("Alqoriya"); "disjoint sets" named inconsistently |

| dfs | 2-4 | – → 4 | – → 3 | – → 5 | – → 5/5 (verify Q2) | – → Slide 2, correct | – → 12 | 3 different Azerbaijani names for DFS across slides; Azerbaijani has extra phrases not in English; garbled exercise on slide 3 |

| Dijkstra | 2-4 | 4 → 4 | 3 → 3 | 3 → 5 | 4/5 → 4/5 | OK (English) → Slide 1 (verify) | 40 → 16 | "relaxation" has 3 Azerbaijani names; glossary maps "cost" to "zərər" (wrong here); "bərabərdir ... olur" translation style; Q4 too trivial |

| dp\_linear | 2-3 | 3 → 3 | 3 → 3 | 2 → 4 | 5/5 → 5/5 | out of scope + no source → "not covered", no source (quiz still finds DP steps) | 27 → 16 | Scrambled table: invented/wrong values (6, 8, 16, 166; exercise 6, 1, 7, 6, 7); walls of text |

| dp\_square | 2-4 | 4 → 4 | 3 → 3 | 3 → 4 | 5/5 → 5/5 | Slides 1-8 listed → Slide 3 | 26 → 11 | Quiz format bug in one run (question moved into "A1:" line); Q\&A over-uses English terms in parentheses |



\## Summary of results

\- Fixed by prompt changes: LaTeX in quizzes, greetings, Azerbaijani words inside the English part, heading format, "thinking aloud", Q\&A answer language, source line on out-of-scope answers.

\- Only partly fixed: Azerbaijani terminology (a different word per slide), over-explaining basic words, invented or scrambled numbers from tables.

\- Not fixable with prompts: tables and superscripts scrambled by PDF text extraction (pypdf); Q\&A sometimes cites the wrong slide.



\## Reliability

\- 2 failures in about 12 test runs on the free tier: one "busy" (503) and one 504 timeout.

\- Cause: only one 2-second retry per model. Fix: 504 treated as busy and 3 tries.

\- 0 failures in the final 5 runs.

