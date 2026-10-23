#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
export COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1
run(){ name=$1; ram=$2; shift 2; env RAM_GB=$ram "$@" $S/glmrun.sh $name $S/colibri --ram $ram --ctx 1024; }
run c9-best-combo 18
run c10-combo-w2 18 PIPE_WORKERS=2
run c11-combo-w16 18 PIPE_WORKERS=16
run c12-combo-cap2-r20 20 CAP=2
run c13-combo-mmap 18 COLI_MMAP=1 DIRECT=0
run c14-combo-nomlock 18 MLOCK=0
run c15-combo-repeat 18
