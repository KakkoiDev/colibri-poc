#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
export COLI_METAL=1 PIPE=1 DIRECT=1 COLI_METAL_RESSET=1 COLI_METAL_SPIN=1 RAM_GB=18
run(){ name=$1; shift; env "$@" $S/glmrun.sh $name $S/colibri --ram 18 --ctx 1024; }
run l11-degrade-070 NGEN=48 DEGRADE_ZERO=1 DEGRADE_TAU=0.70
run l12-degrade-100 NGEN=48 DEGRADE_ZERO=1 DEGRADE_TAU=1.0
run q3-code-degrade-050 NGEN=48 PROMPT="Write a Python function that returns the n-th Fibonacci number iteratively, then state its time complexity." DEGRADE_ZERO=1 DEGRADE_TAU=0.50
i=0
for p in "What is the capital of Australia? Answer in one word." "What is 17 multiplied by 23? Give only the number." "Who wrote the novel Pride and Prejudice? Answer with the name only." "What is the chemical symbol for gold? Answer with the symbol only." "Translate 'thank you very much' into Japanese. Answer with the Japanese only."; do
  i=$((i+1))
  run f$i-exact NGEN=16 PROMPT="$p"
  run f$i-d050 NGEN=16 PROMPT="$p" DEGRADE_ZERO=1 DEGRADE_TAU=0.50
  run f$i-d070 NGEN=16 PROMPT="$p" DEGRADE_ZERO=1 DEGRADE_TAU=0.70
done
