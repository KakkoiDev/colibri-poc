#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
export COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1 RAM_GB=18 NGEN=48
run(){ name=$1; shift; env "$@" $S/glmrun.sh $name $S/colibri --ram 18 --ctx 1024; }
run l0-exact-48
run l1-degrade-003 DEGRADE_ZERO=1 DEGRADE_TAU=0.03
run l2-degrade-005 DEGRADE_ZERO=1 DEGRADE_TAU=0.05
run l3-degrade-010 DEGRADE_ZERO=1 DEGRADE_TAU=0.10
run l4-cacheroute CACHE_ROUTE=1
run l5-cacheroute-j1-m24 CACHE_ROUTE=1 ROUTE_J=1 ROUTE_M=24
run l6-degrade-010-cacheroute DEGRADE_ZERO=1 DEGRADE_TAU=0.10 CACHE_ROUTE=1
run l7-degrade-020 DEGRADE_ZERO=1 DEGRADE_TAU=0.20
