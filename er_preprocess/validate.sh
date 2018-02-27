#!/bin/bash

for i in `ls speakers/`; do
  wavs=`ls speakers/$i/*.wav | wc -l`
  sentences=`wc -l <speakers/$i/sentences.csv`
  if [ $wavs -ne $sentences ]; then
    echo $i $wavs $sentences
  fi
done
