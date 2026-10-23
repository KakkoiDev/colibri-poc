#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
export COLI_METAL=1 RAM_GB=18
run(){ name=$1; shift; env "$@" $S/glmrun.sh $name $S/colibri --ram 18 --ctx 1024; }
run c3-pipe PIPE=1
run c4-pipe-direct PIPE=1 DIRECT=1
run c5-pipe-direct-resset PIPE=1 DIRECT=1 COLI_METAL_RESSET=1
run c6-pipe-direct-spin PIPE=1 DIRECT=1 COLI_METAL_SPIN=1
run c7-pipe4-direct PIPE=1 PIPE_WORKERS=4 DIRECT=1
run c8-pipe-direct-pilot PIPE=1 DIRECT=1 PILOT=1 PILOT_REAL=1
