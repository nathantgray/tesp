#!/bin/bash

# change the ready folder
sims="/mnt/dsot/run_outputs/ready"

# cd to directory where the cases
for dir in $1*
do
  if [ -d "$dir" ]
  then
#    FILE=$dir/tso.yaml
    FILE=$dir/tso_h.json
    if [ -f "$FILE" ]
    then
      echo "Submit simulation" $dir
      rm -rf $sims/$dir
      cp -r $dir $sims
      rm -rf $dir
    fi
  fi
done
