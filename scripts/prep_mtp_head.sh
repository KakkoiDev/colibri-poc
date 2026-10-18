#!/bin/sh
# Add an int8 MTP draft head to GLM-5.3 without touching the owner's model folder.
# Downloads the 3 FP8 shards holding layer 78 of zai-org/GLM-5.3 one at a time (~16 GB
# downloaded, deleted after conversion), converts the head to int8 with Colibri's own
# converter (~10 GB kept), then builds ~/colibri-models/glm-5.3-mtp: symlinks to every
# glm-5.3 file plus the out-mtp-* files. torch/numpy/safetensors come from a throwaway
# uv environment (nothing installed globally). Resumable: rerun if it stops.
set -eu
SRC=~/colibri-models/glm-5.3
HEAD=~/colibri-models/glm-5.3-mtp-head
DST=~/colibri-models/glm-5.3-mtp
mkdir -p "$HEAD"
uv run --no-project --python 3.12 --with torch --with numpy --with safetensors --with huggingface_hub \
  python ~/Code/colibri/c/tools/convert_fp8_to_int4.py --mtp --repo zai-org/GLM-5.3 --outdir "$HEAD" --min-free-gb 30
mkdir -p "$DST"
for f in "$SRC"/* "$HEAD"/out-mtp-*; do ln -sf "$f" "$DST/$(basename "$f")"; done
ls -l "$HEAD"/out-mtp-*
touch "$DST/.mtp-ready"
echo "Ready: $DST"
