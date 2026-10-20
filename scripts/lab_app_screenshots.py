"""Screenshot the lab app's main pages at desktop and phone widths, and check them.

    .venv/bin/python lab_app/demo_server.py &            # isolated demo on :8767
    .venv/bin/python scripts/lab_app_screenshots.py      # writes docs/lab-app/screenshots/*.png

Needs Playwright (pip install playwright && playwright install chromium). Point --url at the
demo server, never at the real app: the script clicks through pages (it does not press any
button that starts, stops, downloads or removes, but the demo makes that harmless anyway).
Each page is also checked for console errors, horizontal overflow, unlabeled form controls
and images without alt text; problems are printed and make the exit code non-zero.
"""
import argparse, sys
from pathlib import Path

PAGES = [('dashboard', 'Run benchmarks'), ('results', 'Results'), ('models', 'Models'), ('queue', 'Queue'),
         ('start', 'Select several'), ('bench/v1', 'Bench answers'), ('results/speed', 'Speed runs'), ('results/coverage', 'Coverage')]
MAX_H = 2400
SIZES = [('wide', 1440, 1000), ('narrow', 390, 844)]

CHECK = """() => {
  const out = [];
  const doc = document.documentElement;
  if (doc.scrollWidth > window.innerWidth + 1) out.push('horizontal overflow: ' + doc.scrollWidth + 'px > ' + window.innerWidth + 'px');
  document.querySelectorAll('input, select, textarea').forEach(el => {
    if (el.type === 'hidden') return;
    const lab = el.labels && el.labels.length, aria = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
    if (!lab && !aria) out.push('unlabeled ' + el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''));
  });
  document.querySelectorAll('button, a[href]').forEach(el => {
    const name = (el.getAttribute('aria-label') || el.textContent || '').trim();
    if (!name) out.push('control without a name: ' + el.outerHTML.slice(0, 80));
  });
  document.querySelectorAll('img:not([alt])').forEach(el => out.push('img without alt: ' + el.src));
  return out;
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:8767')
    ap.add_argument('--out', default=str(Path(__file__).resolve().parent.parent / 'docs' / 'lab-app' / 'screenshots'))
    ap.add_argument('--theme', choices=['light', 'dark'], default='light')
    ap.add_argument('--suffix', default='')
    o = ap.parse_args()
    from playwright.sync_api import sync_playwright
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for size, w, hgt in SIZES:
            ctx = b.new_context(viewport={'width': w, 'height': hgt}, color_scheme=o.theme, service_workers='block')
            page = ctx.new_page()
            errs = []
            page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            page.on('pageerror', lambda e: errs.append(str(e)))
            for name, _ in PAGES:
                errs.clear()
                page.goto(f'{o.url}/#{name}')
                page.wait_for_selector(f'main[data-ready][data-route="{name}"]', timeout=15000)
                page.wait_for_timeout(300)
                found = page.evaluate(CHECK) + [f'console: {e}' for e in errs]
                problems += [f'{name} ({size}): {x}' for x in found]
                tall = min(page.evaluate('document.documentElement.scrollHeight'), MAX_H)   # long tables: the top is enough
                page.screenshot(path=str(out / f"{name.replace('/', '-')}-{size}{o.suffix}.png"), full_page=True, clip=dict(x=0, y=0, width=w, height=tall))
            ctx.close()
        b.close()
    for x in problems:
        print('PROBLEM', x)
    print(f'{len(PAGES) * len(SIZES)} screenshots in {out}; {len(problems)} problems')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
