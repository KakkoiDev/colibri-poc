#!/bin/zsh
# Thread-count test: OMP_NUM_THREADS 2 (Colibri's M6 default) vs 6 vs 12, installed engine
D=~/Code/colibri-poc/results/glm-threads-20261018
SKY="Explain in two sentences why the sky is blue."
base=(USAGE_SAVE=0 KVSAVE=0 COLI_TEMP=0 PROF=1 RAM_GB=18)
metal=(COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1)
run(){ name=$1; ngen=$2; shift 2; env $base "$@" ~/Code/colibri/c/coli run --model ~/colibri-models/glm-5.3 --no-tune-profile --no-think --ngen $ngen --ram 18 --ctx 1024 "$SKY" > $D/$name.log 2>&1; echo "$name: $(grep -o 'omp threads)' $D/$name.log | head -1) $(grep -o '[0-9]* omp threads' $D/$name.log | head -1) | $(grep -o 'decode [0-9]* tokens in [0-9.]*s ([0-9.]* tok/s)' $D/$name.log)"; }
for t in 2 6 12; do run metal-exact-t$t 24 $metal OMP_NUM_THREADS=$t; done
for t in 2 6 12; do run metal-skip050-t$t 48 $metal DEGRADE_ZERO=1 DEGRADE_TAU=0.50 OMP_NUM_THREADS=$t; done
for t in 2 6 12; do run cpu-exact-t$t 12 PIPE=1 DIRECT=1 OMP_NUM_THREADS=$t; done
