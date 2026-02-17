import math

import numpy as np
from scipy.stats import t, norm

def confidence_interval(values, confidence=0.95):
    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))

    alpha = 1 - confidence

    if n < 30:
        factor = t.ppf(1 - alpha / 2, df=n - 1)
    else:
        factor = norm.ppf(1 - alpha / 2)

    ci = factor * std / math.sqrt(n)
    return mean, ci

def parse_config_dir(config_dir):
    parts = config_dir.split("_")

    particles = int(parts[0][1:])
    iterations = int(parts[1][1:])
    c1 = float(parts[2].split("-")[1])
    c2 = float(parts[3].split("-")[1])
    w = float(parts[4][1:])
    k = int(parts[5][1:])

    return particles, iterations, c1, c2, w, k

def generate_initial_positions(particles, dimensions):
    init_pos = np.zeros((particles, dimensions), dtype=int)

    # Definir la posición inicial con todos los enlaces encendidos para tener siempre resultados asegurados
    init_pos[0].fill(1)

    # Definir el resto de partículas con un 50-90% de los enlaces encendidos para filtrar soluciones inviables
    for i in range(1, particles):
        # Elegir porcentaje entre 50% y 90%
        activation_ratio = np.random.uniform(0.5, 0.9)

        # Número de enlaces activos
        num_active = int(dimensions * activation_ratio)

        # Elegir índices aleatorios sin repetición
        active_indices = np.random.choice(dimensions, num_active, replace=False)

        # Activarlos
        init_pos[i, active_indices] = 1

    return init_pos