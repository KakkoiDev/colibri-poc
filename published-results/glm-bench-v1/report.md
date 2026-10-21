| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | d030 | 24 | 21/24 | 1/24 | 162.6 | 42.3 | 103.9 | 0.86 |
| normal | d030t12 | 24 | 21/24 | 1/24 | 143.8 | 31.6 | 103.9 | 0.92 |
| normal | d040t12 | 24 | 18/24 | 0/24 | 130.2 | 33.2 | 120.3 | 1.25 |
| normal | d050 | 24 | 17/24 | 0/24 | 119.9 | 42.2 | 119.5 | 1.54 |
| normal | exact | 24 | 21/24 | 24/24 | 281.3 | 42.4 | 98.3 | 0.41 |
| terse | d030 | 24 | 24/24 | 18/24 | 51.8 | 39.9 | 10.3 | 0.84 |
| terse | d030t12 | 24 | 24/24 | 18/24 | 53.3 | 41.4 | 10.3 | 0.81 |
| terse | d040t12 | 24 | 24/24 | 18/24 | 52.0 | 41.8 | 12.3 | 1.25 |
| terse | d050 | 24 | 24/24 | 18/24 | 50.7 | 39.9 | 16.1 | 1.44 |
| terse | exact | 24 | 24/24 | 24/24 | 63.9 | 39.9 | 9.9 | 0.41 |

Incorrect answers:
- code-factorial / normal / d040t12
- code-factorial / normal / exact
- code-fib / normal / d050
- code-palindrome / normal / d030
- code-palindrome / normal / d030t12
- code-palindrome / normal / d040t12
- code-palindrome / normal / d050
- explain-sky / normal / d050
- logic-sisters / normal / d040t12
- logic-sisters / normal / d050
- logic-sisters / normal / exact
- math-mul / normal / d040t12
- math-pct / normal / d030
- math-pct / normal / d030t12
- math-pct / normal / d050
- math-pow / normal / d030
- math-pow / normal / d030t12
- math-pow / normal / d040t12
- math-pow / normal / d050
- math-pow / normal / exact
- math-train / normal / d040t12
- math-train / normal / d050
