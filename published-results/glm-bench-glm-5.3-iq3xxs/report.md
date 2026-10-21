| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | d030 | 24 | 19/24 | 1/24 | 362.2 | 51.9 | 109.7 | 0.35 |
| normal | d030t12 | 24 | 19/24 | 1/24 | 234.1 | 28.6 | 109.7 | 0.54 |
| normal | d040t12 | 24 | 17/24 | 0/24 | 243.9 | 29.3 | 118.0 | 0.56 |
| normal | d050 | 24 | 18/24 | 0/24 | 389.6 | 51.9 | 128.0 | 0.38 |
| normal | exact | 24 | 21/24 | 24/24 | 540.9 | 52.9 | 103.0 | 0.21 |
| terse | d030 | 24 | 24/24 | 20/24 | 108.3 | 77.3 | 10.9 | 0.31 |
| terse | d030t12 | 24 | 24/24 | 20/24 | 63.6 | 42.1 | 10.9 | 0.42 |
| terse | d040t12 | 24 | 24/24 | 17/24 | 61.4 | 41.2 | 12.2 | 0.49 |
| terse | d050 | 24 | 23/24 | 17/24 | 114.5 | 77.7 | 15.2 | 0.39 |
| terse | exact | 24 | 24/24 | 24/24 | 132.2 | 78.5 | 11.0 | 0.18 |

Incorrect answers:
- code-factorial / normal / d030
- code-factorial / normal / d030t12
- code-factorial / normal / d040t12
- code-factorial / normal / d050
- code-factorial / normal / exact
- code-fib / normal / d030
- code-fib / normal / d030t12
- code-fib / normal / d040t12
- code-fib / normal / d050
- code-vowels / normal / d040t12
- logic-sisters / normal / d030
- logic-sisters / normal / d030t12
- logic-sisters / normal / d040t12
- logic-sisters / normal / d050
- logic-sisters / normal / exact
- logic-sisters / terse / d050
- math-apples / normal / d050
- math-pct / normal / d040t12
- math-pct / normal / d050
- math-pow / normal / d030
- math-pow / normal / d030t12
- math-pow / normal / d040t12
- math-pow / normal / exact
- math-train / normal / d030
- math-train / normal / d030t12
- math-train / normal / d040t12
- math-train / normal / d050
