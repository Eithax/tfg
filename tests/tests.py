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
        "Topología base": 274.5541053459976,
        "VCH-100p-600i": 179.62151396560843,
        "VCH-200p-1200i": 170.27939222023672,
        "VCH-100p-1200i": 173.68060126306774,
        "PSO-200p-1200i": 201.642244998825
    },
    "TM2": {
        "Topología base": 275.5825264151971,
        "VCH-100p-600i": 179.18421007762392,
        "VCH-200p-1200i": 172.29365508413494,
        "VCH-100p-1200i": 173.93992381062842,
        "PSO-200p-1200i": 202.03155646771605
    },
    "TM3": {
        "Topología base": 277.1251580189963,
        "VCH-100p-600i": 181.60895322713098,
        "VCH-200p-1200i": 174.4531158775359,
        "VCH-100p-1200i": 178.2689186433911,
        "PSO-200p-1200i": 202.40542585959577
    },
    "TM4": {
        "Topología base": 279.69621069199496,
        "VCH-100p-600i": 188.95763472317113,
        "VCH-200p-1200i": 182.42817998889525,
        "VCH-100p-1200i": 184.35248039799145,
        "PSO-200p-1200i": 212.0422013065832
    },
    "TM5": {
        "Topología base": 284.83831603799234,
        "VCH-100p-600i": 205.0574346531328,
        "VCH-200p-1200i": 199.6276459821045,
        "VCH-100p-1200i": 202.06613487849093,
        "PSO-200p-1200i": 236.25371065171645
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