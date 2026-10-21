| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | d030 | 24 | 22/24 | 0/24 | 171.3 | 44.7 | 106.6 | 0.84 |
| normal | d030t12 | 24 | 22/24 | 0/24 | 146.1 | 32.4 | 106.6 | 0.93 |
| normal | d040t12 | 24 | 20/24 | 0/24 | 113.0 | 32.4 | 117.7 | 1.47 |
| normal | d050 | 24 | 17/24 | 0/24 | 128.0 | 44.8 | 120.6 | 1.45 |
| normal | exact | 24 | 21/24 | 24/24 | 284.1 | 44.8 | 98.3 | 0.41 |
| terse | d030 | 24 | 24/24 | 20/24 | 62.3 | 49.4 | 10.2 | 0.70 |
| terse | d030t12 | 24 | 24/24 | 20/24 | 60.6 | 49.3 | 10.2 | 0.79 |
| terse | d040t12 | 24 | 24/24 | 18/24 | 56.5 | 48.9 | 11.1 | 1.27 |
| terse | d050 | 24 | 23/24 | 15/24 | 60.4 | 48.9 | 16.5 | 1.22 |
| terse | exact | 24 | 24/24 | 24/24 | 74.8 | 48.9 | 9.9 | 0.34 |

Incorrect answers:
- code-factorial / normal / d050
- code-factorial / normal / exact
- code-palindrome / normal / d040t12
- code-palindrome / normal / d050
- code-vowels / terse / d050
- logic-sisters / normal / d040t12
- logic-sisters / normal / d050
- logic-sisters / normal / exact
- math-apples / normal / d050
- math-mul / normal / d040t12
- math-pct / normal / d030
- math-pct / normal / d030t12
- math-pct / normal / d050
- math-pow / normal / d040t12
- math-pow / normal / d050
- math-pow / normal / exact
- math-train / normal / d030
- math-train / normal / d030t12
- math-train / normal / d050
