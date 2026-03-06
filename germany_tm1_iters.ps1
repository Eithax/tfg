Write-Host "# 10 - 100 iter / 100 particles / c1 1.75 / c2 2.25"

for ($iters = 10; $iters -le 100; $iters += 10) {
    python main.py --network Germany --runs 20 --tm 1 --threads 6 `
    --iters $iters --particles 100 --history-step 5 `
    --c1 1.75 --c2 2.25 --k 100 --history-inf null --vch
}

Write-Host ""