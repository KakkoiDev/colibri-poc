# Quality bench v1: manual review of "incorrect" answers

The automatic grader takes the **last number** for maths/logic and runs tests on the
**first code block**. Normal-style answers were capped at 128 tokens. Both under-count
long answers, so every answer graded incorrect was read by hand (2026-10-18). The
automatic numbers in `report.md` are unchanged; this file adds the reviewed view.

| Run | Automatic | Reviewed | Why |
|---|---|---|---|
| code-factorial / normal / exact | wrong | cut off | correct start, ran out of 128 tokens before the function body finished |
| logic-sisters / normal / exact | wrong | correct | says "Sally has 1 sister"; a later "2 girls" sentence confused the grader |
| math-pow / normal / exact | wrong | correct | re-run (first attempt refused: 7.8 GB free); says 1024, ends with "powers of 2" |
| code-palindrome / normal / d030 | wrong | cut off | long docstring used all 128 tokens |
| math-pct / normal / d030 | wrong | correct | says **36**, then explains a second method |
| math-pow / normal / d030 | wrong | correct | says **1024**, then counts up by doubling |
| code-fib / normal / d050 | wrong | cut off | explanation still running at 128 tokens |
| code-palindrome / normal / d050 | wrong | cut off | long docstring used all 128 tokens |
| explain-sky / normal / d050 | wrong | **wrong** | degenerates into repetition ("the sky, and the sky colour, ...") |
| logic-sisters / normal / d050 | wrong | **wrong** | rambles through candidate answers without settling |
| math-pct / normal / d050 | wrong | correct | says **36**, cut off mid-explanation |
| math-pow / normal / d050 | wrong | correct, with an error | says **1024** but also "2 squared (2^5), cubed (2^5)" |
| math-train / normal / d050 | wrong | cut off | spent all 128 tokens setting up the formula, no answer yet |

Reviewed totals (correct / cut off / wrong):

| Style | Config | Automatic | Reviewed |
|---|---|---:|---|
| normal | exact | 21/23 (+1 refused) | 23 correct, 1 cut off, 0 wrong |
| normal | skip 0.3 | 21/24 | 23 correct, 1 cut off, 0 wrong |
| normal | skip 0.5 | 17/24 | 19 correct (1 with an error), 3 cut off, 2 wrong |
| terse | all three | 24/24 each | not needed |

Takeaways: terse prompting made every configuration 24/24 and avoided the long-answer
failures. Skip 0.5's problems show up in long free-form answers (repetition, rambling,
longer outputs), which is where its quality cost lives.
