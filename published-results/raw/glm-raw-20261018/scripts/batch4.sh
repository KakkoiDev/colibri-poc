#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
export COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1 RAM_GB=18 NGEN=48
run(){ name=$1; shift; env "$@" $S/glmrun.sh $name $S/colibri --ram 18 --ctx 1024; }
run l8-degrade-030 DEGRADE_ZERO=1 DEGRADE_TAU=0.30
run l9-degrade-040 DEGRADE_ZERO=1 DEGRADE_TAU=0.40
run l10-degrade-050 DEGRADE_ZERO=1 DEGRADE_TAU=0.50
P2="Write a Python function that returns the n-th Fibonacci number iteratively, then state its time complexity."
run q0-code-exact PROMPT="$P2"
run q1-code-degrade-020 PROMPT="$P2" DEGRADE_ZERO=1 DEGRADE_TAU=0.20
run q2-code-degrade-030 PROMPT="$P2" DEGRADE_ZERO=1 DEGRADE_TAU=0.30
