$c1_values = @(1.5, 1.75, 2.0, 2.25, 2.5)
$c2_values = @(2.5, 2.25, 2.0, 1.75, 1.5)

for ($i = 0; $i -lt $c1_values.Length; $i++) {
    $c1 = $c1_values[$i]
    $c2 = $c2_values[$i]

    Write-Host "# 1000 - 1500 iter / 200 particles / c1 $c1 / c2 $c2"

    for ($iters = 1000; $iters -le 1500; $iters += 100) {
        python main.py --network Abilene --runs 5 --tm 5 --threads 6 `
        --iters $iters --particles 200 --history-step 100 `
        --c1 $c1 --c2 $c2 --k 100 --history-inf null
    }

    Write-Host ""
}