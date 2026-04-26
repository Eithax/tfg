from libs.result_analysis import (
    procesar_barrido_particulas,
    procesar_barrido_iteraciones,
    procesar_barrido_particulas_min_max,
    procesar_barrido_iteraciones_min_max,
    plot_tm_bars_with_confidence, plot_all_runs_iteraciones,
    procesar_barrido_iteraciones_regex,
    procesar_barrido_particulas_regex
)
from pathlib import Path
from datetime import datetime


# ============================================================
# EMISIONES CON TODOS LOS ENLACES ENCENDIDOS
# ============================================================

MAX_CARBON = {
    "Abilene": {
        1: 119.23285957325584,
        2: 120.1275744665698,
        3: 122.49521077433485,
        4: 124.44984242414479,
        5: 125.42715824904977
    },
    "Geant": {
        1: 243.43302882243873,
        2: 244.4690691882402,
        3: 245.2932219294174,
        4: 246.12476584315752,
        5: 247.10510576733463
    },
    "Nobel": {
        1: 274.5541053459976,
        2: 275.5825264151971,
        3: 277.1251580189963,
        4: 279.69621069199496,
        5: 284.83831603799234
    },
    "Germany": {
        1: 902.0110059173542,
        2: 904.8737573966937,
        3: 910.5992603553727,
        4: 916.3247633140517,
        5: 919.1875147933912
    }
}


network="Nobel"
config_dir="p200_i600_c1-1.75_c2-2.25_w0.7_k100"
tm_indices=[1, 2, 3, 4, 5]
confidence=0.95
pso_type="PSO_VCH"

plot_tm_bars_with_confidence(network, config_dir, tm_indices, confidence, pso_type)

#procesar_barrido_iteraciones(
#    network,
#    pso_type,
#    iter_start=100,
#    iter_end=1500,
#    iter_step=100,
#    particles_fixed=200,
#    tm_index=5
#)

#procesar_barrido_particulas(
#    network,
#    pso_type,
#    particles_start=100,
#    particles_end=500,
#    particles_step=100,
#    iterations_fixed=1500,
#    tm_index=5
#)

#plot_all_runs_iteraciones(
#    network,
#    pso_type,
#    iter_start=10,
#    iter_end=100,
#    iter_step=10,
#    particles_fixed=100,
#    tm_index=1
#)



regex = r"""
^(?P<date>\d{8})_
(?P<time>\d{6})_
(?P<particles>\d+)particles_
(?P<iters>\d+)iters_
(?P<c1>[\d.]+)c1_
(?P<c2>[\d.]+)c2_.*\.json$
"""


dir_path = Path("/Users/santi/Documents/universidad/tfg/results/Abilene/sweeps/TM5")

start = datetime(2026, 1, 22, 10, 0, 0)
end   = datetime(2026, 1, 22, 12, 0, 0)

#procesar_barrido_iteraciones_regex(
#    directory=dir_path,
#    regex_pattern=regex,
#    iter_start=1000,
#    iter_end=1500,
#    iter_step=100,
#    particles_fixed=200,
#    start_datetime=start,
#    end_datetime=end
#)


#dir_path = Path("/Users/santi/Documents/universidad/tfg/results/Abilene/sweeps/TM5")
#
#start = datetime(2026, 1, 22, 14, 0, 0)
#end   = datetime(2026, 1, 22, 16, 0, 0)
#
#procesar_barrido_particulas_regex(
#    directory=dir_path,
#    regex_pattern=regex,
#    particles_start=100,
#    particles_end=500,
#    particles_step=100,
#    iterations_fixed=1500,
#    start_datetime=start,
#    end_datetime=end
#)