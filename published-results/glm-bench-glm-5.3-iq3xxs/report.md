| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | d030 | 24 | 19/24 | 1/24 | 362.2 | 51.9 | 109.7 | 0.35 |
| normal | d030t12 | 24 | 19/24 | 1/24 | 234.1 | 28.6 | 109.7 | 0.54 |
| normal | d040t12 | 24 | 17/24 | 0/24 | 243.9 | 29.3 | 118.0 | 0.56 |
| normal | d050 | 24 | 18/24 | 0/24 | 389.6 | 51.9 | 128.0 | 0.38 |
| normal | exact | 24 | 21/24 | 24/24 | 540.9 | 52.9 | 103.0 | 0.21 |
| terse | d030 | 18 | 18/18 | 17/18 | 93.6 | 76.1 | 5.4 | 0.28 |
| terse | d030t12 | 18 | 18/18 | 17/18 | 55.4 | 42.3 | 5.4 | 0.37 |
| terse | d040t12 | 17 | 17/17 | 14/17 | 48.1 | 40.6 | 3.2 | 0.41 |
| terse | d050 | 18 | 17/18 | 15/18 | 91.9 | 76.7 | 6.1 | 0.37 |
| terse | exact | 18 | 18/18 | 18/18 | 105.0 | 77.6 | 5.1 | 0.17 |

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
