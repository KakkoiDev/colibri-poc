#!/bin/sh
# Download one Unsloth GGUF quant and import it with the Colibri dev build (GGUF read in
# place, colibri#2140). Usage: sh scripts/prep_gguf.sh REPO QUANT NAME
#   sh scripts/prep_gguf.sh unsloth/GLM-5.3-GGUF UD-IQ2_M glm-5.3-iq2m        (~239 GB)
#   sh scripts/prep_gguf.sh unsloth/GLM-5.3-GGUF UD-IQ3_XXS glm-5.3-iq3xxs    (~282 GB)
#   sh scripts/prep_gguf.sh unsloth/GLM-5.3-Flash-GGUF UD-IQ3_XXS glm-5.3-flash-iq3xxs (~120 GB)
# Resumable: rerun the same command if the download stops.
set -eu
REPO=$1; QUANT=$2; NAME=$3
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GG=~/colibri-models/gguf/$NAME
DST=~/colibri-models/$NAME
ENG="$ROOT/engines/colibri-16239caa"
[ -x "$ENG/c/colibri" ] || (cd "$ROOT" && .venv/bin/python -c "import glm_lab; glm_lab.build_engine({'coli_dir': 'engines/colibri-16239caa', 'build': {'ref': '16239caa'}})")
case "$REPO" in *Flash*) [ -x "$ENG/c/glm53" ] || make -C "$ENG/c" -j8 glm53 METAL=1 ;; esac
df -h ~ | tail -1
hf download "$REPO" --include "$QUANT/*" --local-dir "$GG"
FIRST=$(ls "$GG/$QUANT"/*.gguf | sort | head -1)
"$ENG/c/coli" import "$FIRST" --out "$DST"
echo "Ready: $DST"
