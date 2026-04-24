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

network="Abilene"
config_dir="p200_i1200_c1-1.75_c2-2.25_w0.7_k100"
tm_indices=[1, 2, 3, 4, 5]
confidence=0.95
pso_type="PSO"

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