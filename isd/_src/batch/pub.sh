#!/bin/zsh
# pub.sh WORKDIR "commit msg" : copy built pages + specs + logos, push, wait for Pages, verify 200 + md5
W=$1; M=$2; cd ~/paginadedicata || exit 1
S=($(ls $W/out | grep -v '^assets$'))
for s in $S; do [ -e isd/$s/index.html ] && { echo "SKIP exists $s"; continue; }; cp -R $W/out/$s isd/$s; git add isd/$s isd/_src/specs/$s.json; [ -d isd/assets/leads/$s ] && git add isd/assets/leads/$s; done
git add isd/_src/batch
git commit -qm "$M

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git pull --rebase --autostash -q && git push -q || exit 1
H=$(git rev-parse HEAD); echo $H
for i in $(seq 60); do st=$(gh run list -L 20 --json headSha,status,conclusion -q ".[]|select(.headSha==\"$H\")|.status+\":\"+.conclusion"); echo "$st" | grep -q completed && break; sleep 10; done; echo "deploy $st"
for s in $S; do c=$(curl -sI https://paginadedicata.com/isd/$s/ | head -1 | awk '{print $2}'); m1=$(curl -s https://paginadedicata.com/isd/$s/ | md5); m2=$(md5 -q isd/$s/index.html); echo "$s $c $([ $m1 = $m2 ] && echo md5ok || echo MISMATCH)"; done
