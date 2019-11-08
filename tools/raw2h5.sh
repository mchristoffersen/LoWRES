#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch job.txt
rm -f job.txt
touch job.txt

pfix=/zippy/MARS/orig/supl/UAF/2019

while read p;
do
    echo "python /zippy/MARS/code/xped/LoWRES/tools/raw2h5.py $pfix/${p}" >> job.txt
done <$1

cd ..
parallel -j 1 < /zippy/MARS/code/xped/LoWRES/tools/job.txt
#parallel -j 50 --sshloginfile $pfix/code/batch/machines.txt < $pfix/code/batch/job.txt

