$c1_values = @(1.5, 1.75, 2.0, 2.25, 2.5)
$c2_values = @(2.5, 2.25, 2.0, 1.75, 1.5)

for ($i = 0; $i -lt $c1_values.Length; $i++) {
    $c1 = $c1_values[$i]
    $c2 = $c2_values[$i]

    Write-Host "# 10 - 200 iter / 100 particles / c1 $c1 / c2 $c2"

    for ($iters = 10; $iters -le 200; $iters += 10) {
        python main.py --network Germany --runs 20 --tm 1 --threads 6 `
        --iters $iters --particles 100 --history-step 5 `
        --c1 $c1 --c2 $c2 --k 100 --history-inf null --vch
    }

    Write-Host ""
}