#!/bin/bash

# FLYCOP 
# Author: Beatriz García-Jiménez
# April 2018

suffix=$1
cycle=$2

inFile="media_log_${suffix}.txt"
outFile="media_cycle_"${cycle}".txt"

echo -e "#met\tvalueOneCycle" > $outFile

listMets=`egrep "^media_names" ${inFile} | cut -d{ -f2 | cut -d} -f1 |sed 's/\[e\]//g' | sed 's/\ //g' | sed 's/,/\ /g' | sed 's/'\''//g'`
for met in ${listMets}
do
    numMet=`head -n1 ${inFile} | sed "s/.*{ //" | sed "s/}.*//" | sed "s/'//g" | sed "s/, /\n/g" | egrep -w -n ${met} | cut -d: -f1`
    # Get a column with values of the media in the given time point. tail preserves just last line if there are several lines for the same cycle.
    value=`egrep '^media\_'${cycle}'\{'$numMet'\}' ${inFile} | cut -d= -f2 | sed "s/^\ //" | sed "s/;$//" | sed "s/sparse.*/0.0/" | tail -n1`
    echo -e "${met}\t${value}" >> $outFile
done




