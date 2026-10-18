#!/bin/sh
# Add an int8 MTP draft head to GLM-5.3 without touching the owner's model folder.
# Downloads only the FP8 shards holding layer 78 from zai-org/GLM-5.3 (~10 GB out),
# converts them with Colibri's converter (int8, as Colibri requires), then builds
# ~/colibri-models/glm-5.3-mtp: symlinks to every glm-5.3 file plus the out-mtp-* files.
# Uses a throwaway uv environment for torch/numpy/safetensors (nothing installed globally).
set -eu
SRC=~/colibri-models/glm-5.3
HEAD=~/colibri-models/glm-5.3-mtp-head
DST=~/colibri-models/glm-5.3-mtp
uv run --no-project --with torch --with numpy --with safetensors --with huggingface_hub \
  python ~/Code/colibri/c/tools/convert_fp8_to_int4.py --mtp --repo zai-org/GLM-5.3 --outdir "$HEAD" --min-free-gb 30
mkdir -p "$DST"
for f in "$SRC"/* "$HEAD"/out-mtp-*; do ln -sf "$f" "$DST/$(basename "$f")"; done
ls -l "$HEAD"/out-mtp-*
touch "$DST/.mtp-ready"
echo "Ready: $DST (now run: make glm-quiet)"
