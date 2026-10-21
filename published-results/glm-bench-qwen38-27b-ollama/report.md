| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | exact | 24 | 18/24 | 24/24 | 4.5 | 0.3 | 100.2 | 23.66 |
| normal | native | 24 | 24/24 | 0/24 | 12.3 | 0.1 | 282.5 | 24.74 |
| terse | exact | 24 | 24/24 | 24/24 | 0.8 | 0.2 | 11.1 | 15.90 |
| terse | native | 24 | 23/24 | 16/24 | 3.4 | 0.1 | 75.5 | 23.45 |

Incorrect answers:
- code-factorial / normal / exact
- code-factorial / terse / native
- logic-sisters / normal / exact
- math-mul / normal / exact
- math-pct / normal / exact
- math-pow / normal / exact
- math-train / normal / exact
