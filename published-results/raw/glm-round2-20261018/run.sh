#!/bin/zsh
# Round 2: GPU prompt reading (COLI_METAL_PREFILL) and the skip-threshold curve at 12 threads
D=~/Code/colibri-poc/results/glm-round2-20261018
SKY="Explain in two sentences why the sky is blue."
CODE="Write a Python function that returns the n-th Fibonacci number iteratively, then state its time complexity."
base=(USAGE_SAVE=0 KVSAVE=0 COLI_TEMP=0 PROF=1 RAM_GB=18 COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1 OMP_NUM_THREADS=12)
run(){ name=$1; ngen=$2; prompt=$3; shift 3
  { echo "# $name env: $*"; env $base "$@" ~/Code/colibri/c/coli run --model ~/colibri-models/glm-5.3 --no-tune-profile --no-think --ngen $ngen --ram 18 --ctx 1024 "$prompt"; } > $D/$name.log 2>&1
  echo "$name: $(grep -o 'prefill [0-9]* tokens in [0-9.]*s' $D/$name.log) | $(grep -o 'decode [0-9]* tokens in [0-9.]*s ([0-9.]* tok/s)' $D/$name.log)"; }
run p0-sky-exact 24 "$SKY"
run p1-sky-exact-gpuprefill 24 "$SKY" COLI_METAL_PREFILL=1
run p0-code-exact 24 "$CODE"
run p1-code-exact-gpuprefill 24 "$CODE" COLI_METAL_PREFILL=1
for tau in 0.30 0.40 0.50; do run k-sky-skip${tau/./}-t12 48 "$SKY" DEGRADE_ZERO=1 DEGRADE_TAU=$tau; done
for tau in 0.30 0.50; do run k-code-skip${tau/./}-t12 48 "$CODE" DEGRADE_ZERO=1 DEGRADE_TAU=$tau; done
