#!/bin/zsh
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
for f in $S/glm/*.log; do n=${f:t:r}; d=$(grep -o 'decode [0-9]* tokens in [0-9.]*s ([0-9.]* tok/s)' $f); sh=$(grep -o 'time shares:.*' $f | cut -c14-90); av=$(grep -o '[0-9.]* GB available' $f); echo "$n | $d | $av | $sh"; done
