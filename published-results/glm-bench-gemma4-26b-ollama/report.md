| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | exact | 24 | 19/24 | 24/24 | 1.1 | 0.2 | 65.8 | 65.69 |
| normal | native | 24 | 24/24 | 8/24 | 8.0 | 0.1 | 473.1 | 66.66 |
| terse | exact | 24 | 24/24 | 24/24 | 0.5 | 0.3 | 11.8 | 42.72 |
| terse | native | 24 | 23/24 | 18/24 | 9.3 | 0.2 | 540.5 | 62.53 |

Incorrect answers:
- code-factorial / normal / exact
- code-fib / normal / exact
- code-reverse-words / normal / exact
- code-vowels / normal / exact
- logic-feathers / terse / native
- math-pct / normal / exact
