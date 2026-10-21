| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | d030 | 24 | 18/24 | 0/24 | 345.8 | 47.4 | 114.7 | 0.38 |
| normal | d030t12 | 24 | 18/24 | 0/24 | 198.5 | 24.9 | 114.7 | 0.68 |
| normal | d040t12 | 24 | 19/24 | 0/24 | 205.3 | 24.8 | 123.4 | 0.77 |
| normal | d050 | 24 | 15/24 | 0/24 | 329.4 | 47.2 | 128.0 | 0.47 |
| normal | exact | 24 | 23/24 | 24/24 | 463.5 | 47.5 | 97.0 | 0.23 |
| terse | d030 | 24 | 23/24 | 18/24 | 114.9 | 74.1 | 14.0 | 0.31 |
| terse | d030t12 | 24 | 23/24 | 18/24 | 66.5 | 39.6 | 14.0 | 0.46 |
| terse | d040t12 | 24 | 24/24 | 16/24 | 76.8 | 39.1 | 20.1 | 0.54 |
| terse | d050 | 24 | 23/24 | 13/24 | 142.7 | 74.2 | 29.5 | 0.42 |
| terse | exact | 24 | 24/24 | 24/24 | 122.2 | 74.1 | 10.5 | 0.20 |

Incorrect answers:
- code-factorial / normal / d030
- code-factorial / normal / d030t12
- code-factorial / normal / d040t12
- code-factorial / normal / d050
- code-fib / normal / d050
- code-palindrome / normal / d030
- code-palindrome / normal / d030t12
- code-palindrome / normal / d050
- code-palindrome / terse / d030
- code-palindrome / terse / d030t12
- code-reverse-words / normal / d050
- code-vowels / normal / d030
- code-vowels / normal / d030t12
- code-vowels / normal / d040t12
- code-vowels / normal / d050
- logic-sisters / normal / d030
- logic-sisters / normal / d030t12
- logic-sisters / normal / d040t12
- logic-sisters / normal / d050
- logic-sisters / terse / d050
- math-apples / normal / d040t12
- math-apples / normal / d050
- math-pow / normal / d030
- math-pow / normal / d030t12
- math-pow / normal / d040t12
- math-pow / normal / d050
- math-pow / normal / exact
- math-train / normal / d030
- math-train / normal / d030t12
- math-train / normal / d050
