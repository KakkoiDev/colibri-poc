| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | exact | 24 | 16/24 | 24/24 | 0.6 | 0.0 | 72.1 | 111.92 |
| normal | native | 24 | 23/24 | 7/24 | 4.6 | 0.0 | 504.5 | 111.56 |
| terse | exact | 24 | 24/24 | 24/24 | 0.2 | 0.0 | 11.5 | 52.25 |
| terse | native | 24 | 24/24 | 19/24 | 1.3 | 0.0 | 140.4 | 82.11 |

Incorrect answers:
- code-factorial / normal / exact
- code-factorial / normal / native
- code-fib / normal / exact
- code-palindrome / normal / exact
- code-reverse-words / normal / exact
- math-mul / normal / exact
- math-pct / normal / exact
- math-pow / normal / exact
- math-train / normal / exact
