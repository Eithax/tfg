import os
import random
import numpy as np
import json
import argparse
from datetime import datetime
from pathlib import Path
from pyswarms.discrete.binary import BinaryPSO
from pso_libs.optimization_functions import carbon_intensity_wrapper, load_possible_links_from_csv


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

    return topology.shape[0], kwargs


def save_results_grouped(network, tm_index, runs_results, config):
    """Guarda en un solo JSON los resultados de todas las ejecuciones de una misma TM"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(f"results/{network}").mkdir(parents=True, exist_ok=True)
    filename = f"results/{network}/{network}_TM{tm_index}_{timestamp}.json"

    data = {
        "network": network,
        "traffic_matrix": tm_index,
        "config": config,
        "results": runs_results
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Resultados de TM{tm_index} guardados en {filename}")


def run_pso(network, n_runs, n_iters, tm_option, n_threads):
    # Parámetros de PSO
    n_particles = 200
    dimensions = 30  # Ajustar según el problema
    options = {'c1': 2.0, 'c2': 2.0, 'w': 0.7, 'k': 20, 'p': 1}

    config = {
        "n_particles": n_particles,
        "dimensions": dimensions,
        "options": options,
        "iterations": n_iters,
        "runs": n_runs
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
        _, kwargs = load_topology(network, tm_index)
        runs_results = []

        for run in range(n_runs):
            print(f"\n>>> Ejecutando PSO {run + 1}/{n_runs} en {network} con TM{tm_index} y {n_iters} iteraciones...")
            pso = BinaryPSO(n_particles=n_particles, dimensions=dimensions, options=options)
            if n_threads is None:
                result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=n_iters, **kwargs)
            else:
                result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=n_iters, n_processes=n_threads, **kwargs)
            best_cost, best_pos = result
            print(f"Resultado ejecución {run + 1} (TM{tm_index}): Coste={best_cost}, Posicion={best_pos}")

            runs_results.append({
                "run": run + 1,
                "best_cost": float(best_cost),
                "best_pos": best_pos.tolist(),
            })

        # Guardar todos los runs de ese TM en un solo archivo
        save_results_grouped(network, tm_index, runs_results, config)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta PSO en distintas topologías de red")
    parser.add_argument("--network", type=str, required=True, choices=["Abilene", "Geant", "Germany", "Nobel"],
                        help="Red sobre la que correrá el PSO")
    parser.add_argument("--runs", type=int, default=1, help="Número de ejecuciones por matriz de tráfico")
    parser.add_argument("--iters", type=int, default=500, help="Número de iteraciones por ejecución")
    parser.add_argument("--tm", type=str, default=None,
                        help="Índice de la matriz de tráfico a usar (1-5), 'all' para todas, o vacío para aleatoria")
    parser.add_argument("--threads", type=int, default=None, help="Número de hilos que se quieren crear en las ejecuciones")
    args = parser.parse_args()

    run_pso(args.network, args.runs, args.iters, args.tm, args.threads)


if __name__ == "__main__":
    main()
