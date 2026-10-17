"""Download a commit-pinned MLX checkpoint; reruns resume incomplete files."""
import json
import hashlib
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parent
MODEL = 'mlx-community/OLMoE-1B-7B-0125-Instruct-4bit'

def main():
    path = ROOT / 'model.lock.json'
    lock = json.loads(path.read_text()) if path.exists() else {'repo': MODEL, 'revision': HfApi().model_info(MODEL).sha}
    path.write_text(json.dumps(lock, indent=2) + '\n')
    dest = ROOT / 'models' / 'olmoe-1b-7b-4bit'
    snapshot_download(lock['repo'], revision=lock['revision'], local_dir=dest,
                      allow_patterns=['*.json', '*.safetensors', '*.jinja', '*.txt', '*.model', 'README.md'], max_workers=3)
    files = []
    for file in sorted(dest.iterdir()):
        if file.is_file():
            sha = hashlib.sha256()
            with file.open('rb') as stream:
                for block in iter(lambda: stream.read(8 << 20), b''):
                    sha.update(block)
            files.append({'name':file.name,'bytes':file.stat().st_size,'sha256':sha.hexdigest()})
    (ROOT/'model.files.json').write_text(json.dumps(files,indent=2)+'\n')
    print(dest)

if __name__ == '__main__':
    main()
