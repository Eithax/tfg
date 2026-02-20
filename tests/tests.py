from libs.result_analysis import (
    procesar_barrido_particulas,
    procesar_barrido_iteraciones,
    procesar_barrido_particulas_min_max,
    procesar_barrido_iteraciones_min_max,
    plot_tm_bars_with_confidence
)

network="Abilene"
config_dir="p100_i600_c1-1.75_c2-2.25_w0.7_k100"
tm_indices=[1, 2, 3, 4, 5]
confidence=0.95
pso_type="PSO_VCH"

#plot_tm_bars_with_confidence(network, config_dir, tm_indices, confidence, pso_type)

procesar_barrido_particulas(
    network,
    pso_type,
    particles_start=100,
    particles_end=500,
    particles_step=100,
    iterations_fixed=1500,
    tm_index=5
)