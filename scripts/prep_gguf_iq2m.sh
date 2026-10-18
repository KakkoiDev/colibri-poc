#!/bin/sh
# Download Unsloth's 2-bit GLM-5.3 GGUF (UD-IQ2_M, ~239 GB) and import it with the
# Colibri dev build (GGUF read in place, colibri#2140). The engine clone is built by
# `glm_lab.py run-planned` if missing; build it first here so `coli import` exists.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GG=~/colibri-models/glm-5.3-iq2m-gguf
DST=~/colibri-models/glm-5.3-iq2m
ENG="$ROOT/engines/colibri-16239caa"
[ -x "$ENG/c/colibri" ] || "$ROOT/.venv/bin/python" -c "import glm_lab; glm_lab.build_engine({'coli_dir': 'engines/colibri-16239caa', 'build': {'ref': '16239caa'}})"
hf download unsloth/GLM-5.3-GGUF --include "UD-IQ2_M/*" --local-dir "$GG"
FIRST=$(ls "$GG"/UD-IQ2_M/*00001-of-*.gguf | head -1)
"$ENG/c/coli" import "$FIRST" --out "$DST"
echo "Ready: $DST (now run: make glm-quiet)"
