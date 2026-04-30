from libs.result_analysis import (
    procesar_barrido_particulas,
    procesar_barrido_iteraciones,
    procesar_barrido_particulas_min_max,
    procesar_barrido_iteraciones_min_max,
    plot_tm_bars_with_confidence, plot_all_runs_iteraciones,
    procesar_barrido_iteraciones_regex,
    procesar_barrido_particulas_regex,
    plot_costes_por_tm_ordenado
)
from pathlib import Path
from datetime import datetime


resultados_por_tm = {
    "TM1": {
        "Topología base": 119.23285957325584,
        "VCH-100p-600i": 64.6541,
        "VCH-200p-1200i": 61.6078,
        "VCH-100p-1200i": 62.774431968843,
        "PSO-200p-1200i": 76.34725291422204
    },
    "TM2": {
        "Topología base": 120.1275744665698,
        "VCH-100p-600i": 66.4288,
        "VCH-200p-1200i": 62.3903,
        "VCH-100p-1200i": 64.085814068305,
        "PSO-200p-1200i": 74.72472120476489
    },
    "TM3": {
        "Topología base": 122.49521077433485,
        "VCH-100p-600i": 70.3919,
        "VCH-200p-1200i": 68.1253,
        "VCH-100p-1200i": 68.225574044569,
        "PSO-200p-1200i": 77.69085871891823
    },
    "TM4": {
        "Topología base": 124.44984242414479,
        "VCH-100p-600i": 83.7212,
        "VCH-200p-1200i": 80.407983637171,
        "VCH-100p-1200i": 81.5042294689255,
        "PSO-200p-1200i": 88.91831835694208
    },
    "TM5": {
        "Topología base": 125.42715824904977,
        "VCH-100p-600i": 88.6265,
        "VCH-200p-1200i": 87.218973686884,
        "VCH-100p-1200i": 87.2759902693895,
        "PSO-200p-1200i": 94.5696864778004
    }
}

plot_costes_por_tm_ordenado(resultados_por_tm)


network="Nobel"
config_dir="p200_i600_c1-1.75_c2-2.25_w0.7_k100"
tm_indices=[1, 2, 3, 4, 5]
confidence=0.95
pso_type="PSO_VCH"

#plot_tm_bars_with_confidence(network, config_dir, tm_indices, confidence, pso_type)

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