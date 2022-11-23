#!/bin/bash

set -e
set -x

tract=`jq -r '.track' config.json`
names=(`cat names.csv`)
indices='index.csv'

# make output directory
[ ! -d ./tcks ] && mkdir -p ./tcks
outdir='./tcks'

# generate individual tractograms of all nodes
echo "generating individual tractograms using connectome2tck"
connectome2tck ${tract} ${indices} tmp -files per_node -keep_self

# updating names
echo "updating names"
for (( i=0; i<${#names[*]}; i++ ))
do
    name=${names[$i]}
    mv tmp$((i+1)).tck $outdir/$name.tck
done
