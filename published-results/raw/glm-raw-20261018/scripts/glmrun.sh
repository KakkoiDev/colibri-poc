#!/bin/zsh
# usage: glmrun.sh NAME COLI_DIR [extra coli args...]  (env passes through)
S=<tmp>/claude-501/-Users-kakkoidev-Code-pi-local-harness/95e98610-3ae1-4256-8832-7c25ada2f2cd/scratchpad
name=$1; dir=$2; shift 2
export USAGE_SAVE=0 KVSAVE=0 COLI_TEMP=0 PROF=1
log=$S/glm/$name.log
{ echo "# $name $(date -u +%FT%TZ) dir=$dir args=$* env: RAM_GB=$RAM_GB COLI_METAL=$COLI_METAL PIPE=$PIPE DIRECT=$DIRECT MTP=$MTP CACHE_ROUTE=$CACHE_ROUTE PILOT=$PILOT"; } > $log
vm_stat | grep -E 'Swapouts|Pageouts' >> $log
/usr/bin/time -l $dir/c/coli run --model ~/colibri-models/glm-5.3 --no-tune-profile --no-think --ngen ${NGEN:-24} "$@" "${PROMPT:-Explain in two sentences why the sky is blue.}" >> $log 2>&1
echo "exit $?" >> $log
vm_stat | grep -E 'Swapouts|Pageouts' >> $log
