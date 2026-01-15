import os
import random
import numpy as np
import json
import argparse
import math
from datetime import datetime
from pathlib import Path
from pyswarms.discrete.binary import BinaryPSO
from libs.optimization_functions import carbon_intensity_wrapper, load_possible_links_from_csv


"""
Convierte valores a float y maneja inf/nan.
replace_inf_with:
    - 'prev' : reemplaza por el último valor finito conocido (si no hay, pone None)
    - 'null' : pone None (-> se serializa como null en JSON)
    - 'zero' : pone 0.0
Devuelve lista de floats o None.
"""
def sanitize_history(history, replace_inf_with='prev'):
    sanitized = []
    last_finite = None
    for v in history:
        # si es numpy scalar convertir a python float
        try:
            val = float(v)
        except Exception:
            # si no convertible (por ejemplo None), lo guardamos como None
            sanitized.append(None)
            continue

        if math.isfinite(val):
            sanitized.append(val)
            last_finite = val
        else:
            if replace_inf_with == 'prev':
                sanitized.append(last_finite if last_finite is not None else None)
            elif replace_inf_with == 'null':
                sanitized.append(None)
            elif replace_inf_with == 'zero':
                sanitized.append(0.0)
            else:
                sanitized.append(None)
    return sanitized


"""
history: lista (ya saneada) con un valor por iteración (index 0 = iter 1)
step: tomar cada 'step' iteración (1 = todo)
remove_consecutive_duplicates: si True elimina entradas que repiten el mismo valor
Devuelve lista de dicts: [{"iter": iteration_index (1-based), "cost": value_or_null}, ...]
"""
def compress_history(history, step=1, remove_consecutive_duplicates=True):
    if step <= 1:
        indices = range(len(history))
    else:
        indices = range(0, len(history), step)

    compressed = []
    last_val = object()  # sentinel
    for i in indices:
        val = history[i]
        if remove_consecutive_duplicates and compressed and compressed[-1]["cost"] == val:
            continue
        compressed.append({"iter": i + 1, "cost": val})
    return compressed


def load_topology(network_name, tm_index):
    """Carga topología, emisiones, matrices de tráfico y capacidades de la red elegida"""

    base_path = "./resources/topologies/"
    supported_networks = ["Abilene", "Geant", "Germany", "Nobel"]

    if network_name not in supported_networks:
        raise ValueError(f"Red '{network_name}' no reconocida. Usa una de: {supported_networks}")

    topo_file = f"{base_path}{network_name}Topology.csv"
    emissions_file = f"{base_path}Historic_Carbon_Intensity/{network_name}.json"
    coords_file = f"{base_path}Coordenadas/{network_name}Ubications.json"
    cap_file = f"{base_path}Capacidades/{network_name}/{network_name}CapMatrix.csv"
    tm_file = f"{base_path}Matrices_trafico/{network_name}/{network_name}TM{tm_index}.csv"

    # Validar existencia de archivos
    for f in [topo_file, emissions_file, coords_file, cap_file, tm_file]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"No se encontró el fichero requerido: {f}")

    # Cargar matrices
    topology = np.genfromtxt(topo_file, delimiter=',')
    carbon_matrix = topology.copy()
    carbon_intensity_nodes = json.load(open(emissions_file))
    lambda_j = (41.625 - 23.375) / 400000  # 0.000045625 W/Mbps
    num_nodes = topology.shape[0]
    num_links = int(np.sum(topology))

    for i in range(num_nodes):
        for j in range(num_nodes):
            if topology[i][j] == 1:
                carbon_matrix[i][j] = 1 + (carbon_intensity_nodes['carbon_intensity'][j] / 1000) * lambda_j

    traffic_matrix = np.genfromtxt(tm_file, delimiter=',')
    coordinates = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open(coords_file))]
    cap_matrix = np.genfromtxt(cap_file, delimiter=',')
    possible_links = load_possible_links_from_csv(topo_file)

    kwargs = {
        'num_nodes': num_nodes,
        'carbon_matrix': carbon_matrix,
        'flow_matrix': traffic_matrix,
        'nodes_geoposition': coordinates,
        'nodes_max_flow': cap_matrix,
        'possible_links': possible_links,
        'filepath': f"{network_name}"
    }

    return num_nodes, num_links, kwargs


def save_results_grouped(network, tm_index, runs_results, config):
    """Guarda en un solo JSON los resultados de todas las ejecuciones de una misma TM"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(f"results/{network}/TM{tm_index}").mkdir(parents=True, exist_ok=True)
    filename = f"results/{network}/TM{tm_index}/{timestamp}_{config['n_particles']}particles_{config['iterations']}iters_{config['options']['c1']}c1_{config['options']['c2']}c2_{config['options']['w']}w_{config['options']['k']}k.json"

    data = {
        "network": network,
        "traffic_matrix": tm_index,
        "config": config,
        "results": runs_results
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Resultados de TM{tm_index} guardados en {filename}")


def run_pso(network, n_runs, n_iters, tm_option, n_threads, particles, c1, c2, w, k, history_step=1, history_compress=False, history_inf="prev"):
    # Parámetros de PSO
    options = {
        'c1': c1,
        'c2': c2,
        'w': w,
        'k': k,
        'p': 1
    }

    # Determinar qué matrices de tráfico usar
    if tm_option == "all":
        tm_indices = [1, 2, 3, 4, 5]
    elif tm_option is None:
        tm_indices = [random.randint(1, 5)]
    else:
        tm_indices = [int(tm_option)]

    # Ejecutar sobre cada matriz de tráfico seleccionada
    for tm_index in tm_indices:
        num_nodes, num_links, kwargs = load_topology(network, tm_index)
        runs_results = []
        dimensions = num_links

        config = {
            "n_particles": particles,
            "dimensions": dimensions,
            "options": options,
            "iterations": n_iters,
            "runs": n_runs,
            "threads": n_threads
        }

        print(config)

        for run in range(n_runs):
            print(f"\n>>> Ejecutando PSO {run + 1}/{n_runs} en {network} con TM{tm_index} y {n_iters} iteraciones...")
            pso = BinaryPSO(n_particles=particles, dimensions=dimensions, options=options)
            if n_threads is None:
                result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=n_iters, **kwargs)
            else:
                result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=n_iters, n_processes=n_threads, **kwargs)
            best_cost, best_pos = result
            print(f"Resultado ejecución {run + 1} (TM{tm_index}): Coste={best_cost}, Posicion={best_pos}")

            raw_history = list(pso.cost_history)
            sanitized = sanitize_history(raw_history, replace_inf_with=history_inf)
            compressed = compress_history(
                sanitized,
                step=history_step,
                remove_consecutive_duplicates=history_compress
            )

            runs_results.append({
                "run": run + 1,
                "best_cost": None if float(best_cost) == float('inf') else float(best_cost),
                "best_pos": best_pos.tolist(),
                "cost_history": {
                    "mode": "compressed",
                    "step": history_step,
                    "remove_consecutive_duplicates": history_compress,
                    "inf_strategy": history_inf,
                    "data": compressed
                }
            })

        # Guardar todos los runs de ese TM en un solo archivo
        save_results_grouped(network, tm_index, runs_results, config)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta PSO en distintas topologías de red")
    parser.add_argument("--network", type=str, required=True, nargs='+', choices=["Abilene", "Geant", "Germany", "Nobel"], help="Red sobre la que correrá el PSO. Se pueden indicar varias, tan solo hay que dejar un espacio entre el nombre de cada red")
    parser.add_argument("--runs", type=int, default=1, help="Número de ejecuciones por matriz de tráfico")
    parser.add_argument("--iters", type=int, default=500, help="Número de iteraciones por ejecución")
    parser.add_argument("--tm", type=str, default=None, help="Índice de la matriz de tráfico a usar (1-5), 'all' para todas, o vacío para aleatoria")
    parser.add_argument("--threads", type=int, default=None, help="Número de hilos que se quieren crear en las ejecuciones")
    parser.add_argument("--thread-range", type=int, default=None, help="Ejecuta PSO variando el número de hilos desde 1 hasta este valor")
    parser.add_argument("--particles", type=int, default=200, help="Número de partículas (número de soluciones simultáneas) [default: 200]")
    parser.add_argument(
        "--particle-range",
        type=int,
        default=None,
        help="Si se indica, ejecuta PSO incrementando el número de partículas desde el valor base hasta este número (inclusive), en pasos iguales al valor base."
    )

    parser.add_argument("--c1", type=float, default=2.0, help="Constante cognitiva (tendencia hacia la mejor posición personal) [default: 2.0]")
    parser.add_argument("--c2", type=float, default=2.0, help="Constante social (tendencia hacia la mejor posición global) [default: 2.0]")
    parser.add_argument("--w", type=float, default=0.7, help="Peso de inercia (influencia de la velocidad anterior) [default: 0.7]")
    parser.add_argument("--k", type=int, default=20, help="Número de vecinos a considerar en el modelo de topología local [default: 20]")
    parser.add_argument("--iter-range", type=int, default=None, help="Paso del rango de iteraciones. Si se indica, PSO se ejecutará desde este valor hasta --iters en incrementos de este tamaño.")
    parser.add_argument("--history-step", type=int, default=1, help="Frecuencia de guardado del histórico (1 = todas las iteraciones, 10 = una cada 10).")
    parser.add_argument(
        "--history-compress",
        action="store_true",
        help="Si se activa, elimina valores consecutivos duplicados en el histórico para reducir tamaño."
    )
    parser.add_argument(
        "--history-inf",
        type=str,
        choices=["prev", "null", "zero"],
        default="prev",
        help="Cómo manejar valores infinitos o NaN en el histórico: "
             "'prev' = reemplaza con último valor finito, "
             "'null' = los deja como null, "
             "'zero' = los reemplaza por 0.0."
    )


    args = parser.parse_args()

    if args.thread_range:
        thread_values = list(range(1, args.thread_range+1))
    else:
        thread_values = [args.threads or 1]

    if args.iter_range:
        iter_values = list(range(args.iter_range, args.iters + 1, args.iter_range))
    else:
        iter_values = [args.iters]

    if args.particle_range and args.particle_range > args.particles:
        particle_values = list(range(args.particles, args.particle_range + 1, args.particles))
    else:
        particle_values = [args.particles]

    for network in args.network:
        for threads in thread_values:
            for iters in iter_values:
                for n_particles in particle_values:
                    run_pso(
                        network,
                        args.runs,
                        iters,
                        args.tm,
                        threads,
                        n_particles,
                        args.c1,
                        args.c2,
                        args.w,
                        args.k,
                        history_step=args.history_step,
                        history_compress=args.history_compress,
                        history_inf=args.history_inf
                    )


if __name__ == "__main__":
    main()
