#!/bin/bash

c1_values=(1.5 1.75 2.0 2.25 2.5)
c2_values=(2.5 2.25 2.0 1.75 1.5)

for i in ${!c1_values[@]}; do
  c1=${c1_values[$i]}
  c2=${c2_values[$i]}

  echo "# 1000 - 1500 iter / 200 particles / c1 $c1 / c2 $c2"

  for iters in $(seq 1000 100 1500); do
    python main.py --network Abilene --runs 20 --tm 5 --threads 6 \
    --iters $iters --particles 200 --history-step 100 \
    --c1 $c1 --c2 $c2 --k 100 --history-inf null
  done

  echo ""
done