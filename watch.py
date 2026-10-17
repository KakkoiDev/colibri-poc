"""Run the full campaign initially and whenever experiment inputs change."""
import hashlib
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent

def fingerprint():
    paths = [ROOT/'bench.py',ROOT/'prompts.json',ROOT/'model.lock.json',ROOT/'requirements.lock']
    paths += sorted((ROOT/'variants').glob('*.json'))
    paths += sorted((ROOT/'pocs').rglob('*.py'))
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes() if path.exists() else b'<missing>')
    return h.hexdigest()

def main():
    previous = None
    try:
        while True:
            current = fingerprint()
            if current != previous:
                # Debounce edits; if a campaign's inputs change while it runs,
                # the next iteration runs the changed state too.
                time.sleep(2)
                current = fingerprint()
                print('Experiment inputs changed; running campaign', flush=True)
                result = subprocess.run([sys.executable,str(ROOT/'bench.py'),'run',*sys.argv[1:]],cwd=ROOT)
                print(f'Campaign exit {result.returncode}; watching for the next edit',flush=True)
                previous = current
            time.sleep(2)
    except KeyboardInterrupt:
        print('\nWatcher stopped')

if __name__ == '__main__':
    main()
