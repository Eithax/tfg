import os
import json
import pickle
import time
import numpy as np
import networkx as nx
import csv
from itertools import product

from pyswarms.discrete.binary import BinaryPSO

from libs.optimization_functions import (
    carbon_intensity_wrapper,
    load_possible_links_from_csv,
    total_carbon_intensity,
    carbon_intensity_wrapper_vch
)
from libs.shortest_paths import all_pairs_k_shortest_paths_nx
from libs.utils import generate_initial_positions

# ============================================================
# CONFIGURACIÓN DEL BENCHMARK
# ============================================================

NETWORKS = ["Abilene", "Geant", "Nobel", "Germany"]
TRAFFIC_MATRICES = [1, 2, 3, 4, 5]
STRATEGIES = ["normal", "vch"]

PSO_CONFIGS = [
    {"n_particles": 100, "iters": 600,  "label": "100p_600i"},
    {"n_particles": 100, "iters": 1200, "label": "100p_1200i"},
    {"n_particles": 200, "iters": 600,  "label": "200p_600i"},
    {"n_particles": 200, "iters": 1200, "label": "200p_1200i"},
]

BASE_OPTIONS = {
    "c1": 1.75,
    "c2": 2.25,
    "w": 0.7,
    "k": 100,
    "p": 1
}

N_PROCESSES = 6
K_PATHS = 15

LAMBDA_J = (41.625 - 23.375) / 400000  # W/Mbps

RESULTS_DIR = "results"
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_times.csv")

# ============================================================
# CARGA DE RED  (igual que en main.py)
# ============================================================

def load_network(network: str, tm: int):
    base = "./resources/topologies"

    topology_path   = f"{base}/{network}Topology.csv"
    carbon_path     = f"{base}/Historic_Carbon_Intensity/{network}.json"
    tm_path         = f"{base}/Matrices_trafico/{network}/{network}TM{tm}.csv"
    coords_path     = f"{base}/Coordenadas/{network}Ubications.json"
    cap_path        = f"{base}/Capacidades/{network}/{network}CapMatrix.csv"

    topology = np.genfromtxt(topology_path, delimiter=',')
    carbon_matrix = topology.copy()

    carbon_nodes = json.load(open(carbon_path))
    num_nodes = topology.shape[0]

    for i in range(num_nodes):
        for j in range(num_nodes):
            if topology[i][j] == 1:
                carbon_matrix[i][j] = 1 + (carbon_nodes['carbon_intensity'][j] / 1000) * LAMBDA_J

    traffic_matrix  = np.genfromtxt(tm_path, delimiter=',')
    coordinates     = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open(coords_path))]
    cap_matrix      = np.genfromtxt(cap_path, delimiter=',')
    possible_links  = load_possible_links_from_csv(topology_path)

    return {
        "num_nodes": num_nodes,
        "carbon_matrix": carbon_matrix,
        "flow_matrix": traffic_matrix,
        "nodes_geoposition": coordinates,
        "nodes_max_flow": cap_matrix,
        "possible_links": possible_links,
        "filepath": network
    }


# ============================================================
# K-SHORTEST PATHS (con caché)
# ============================================================

def load_k_paths(network, carbon_matrix, possible_links, k=10):
    cache_dir  = f"resources/cache/shortest_paths/{network}"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = f"{cache_dir}/{network.lower()}_k{k}_paths.pkl"

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    G = nx.DiGraph()
    num_nodes = carbon_matrix.shape[0]
    G.add_nodes_from(range(num_nodes))
    for i, j in possible_links:
        G.add_edge(i, j, weight=carbon_matrix[i][j])

    paths = all_pairs_k_shortest_paths_nx(G, k)

    with open(cache_path, "wb") as f:
        pickle.dump(paths, f)

    return paths


# ============================================================
# EJECUCIÓN PSO
# ============================================================

def run_pso(kwargs, init_pos, vch, n_particles, iters):
    dimensions = init_pos.shape[1]

    pso = BinaryPSO(
        n_particles=n_particles,
        dimensions=dimensions,
        options=BASE_OPTIONS,
        init_pos=init_pos
    )

    objective = carbon_intensity_wrapper_vch if vch else carbon_intensity_wrapper

    return pso.optimize(
        objective,
        iters=iters,
        n_processes=N_PROCESSES,
        **kwargs
    )


# ============================================================
# BENCHMARK PRINCIPAL
# ============================================================

def run_benchmark():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Cabecera CSV
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "network", "tm", "strategy", "pso_config",
            "n_particles", "iters",
            "time_s", "best_cost"
        ])

    total = len(NETWORKS) * len(TRAFFIC_MATRICES) * len(STRATEGIES) * len(PSO_CONFIGS)
    done  = 0

    for network in NETWORKS:
        print(f"\n{'='*60}")
        print(f"  RED: {network}")
        print(f"{'='*60}")

        for tm in TRAFFIC_MATRICES:
            print(f"\n  Cargando {network} TM{tm}...")

            try:
                kwargs = load_network(network, tm)
            except Exception as e:
                print(f"    [ERROR] No se pudo cargar {network} TM{tm}: {e}")
                continue

            kwargs["all_k_paths"] = load_k_paths(
                network,
                kwargs["carbon_matrix"],
                kwargs["possible_links"],
                K_PATHS
            )

            dimensions = len(kwargs["possible_links"])

            for pso_cfg in PSO_CONFIGS:
                n_particles = pso_cfg["n_particles"]
                iters       = pso_cfg["iters"]
                label       = pso_cfg["label"]

                # Generar posiciones iniciales una sola vez por config
                # para que normal y vch partan del mismo punto
                init_pos = generate_initial_positions(n_particles, dimensions)

                for strategy in STRATEGIES:
                    vch = (strategy == "vch")
                    done += 1

                    print(f"\n  [{done}/{total}] {network} | TM{tm} | {strategy.upper()} | {label}")

                    try:
                        t_start = time.time()
                        best_cost, best_pos = run_pso(kwargs, init_pos, vch, n_particles, iters)
                        elapsed = time.time() - t_start

                        print(f"    Tiempo: {elapsed:.2f}s  |  Coste: {best_cost:.6f}")

                        with open(RESULTS_FILE, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                network, tm, strategy, label,
                                n_particles, iters,
                                round(elapsed, 4), round(float(best_cost), 6)
                            ])

                    except Exception as e:
                        print(f"    [ERROR] {e}")
                        with open(RESULTS_FILE, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                network, tm, strategy, label,
                                n_particles, iters,
                                "ERROR", str(e)
                            ])

    print(f"\n\nBenchmark completado. Resultados en: {RESULTS_FILE}")


# ============================================================
# ANÁLISIS RÁPIDO DE RESULTADOS
# ============================================================

def summarize_results():
    """Lee el CSV generado e imprime la tabla de medias por topología."""
    import csv
    from collections import defaultdict

    data = defaultdict(list)

    with open(RESULTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["time_s"] == "ERROR":
                continue
            key = (row["network"], row["strategy"], row["pso_config"])
            data[key].append(float(row["time_s"]))

    print(f"\n{'Network':<12} {'Strategy':<8} {'Config':<14} {'N matrices':<12} {'Media (s)':<12} {'Min (s)':<10} {'Max (s)'}")
    print("-" * 78)

    for (network, strategy, cfg), times in sorted(data.items()):
        print(f"{network:<12} {strategy:<8} {cfg:<14} {len(times):<12} "
              f"{np.mean(times):<12.2f} {np.min(times):<10.2f} {np.max(times):.2f}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark PSO vs PSO-VCH en todas las configuraciones")
    parser.add_argument("--summarize", action="store_true",
                        help="Solo mostrar resumen del CSV existente, sin ejecutar PSO")
    args = parser.parse_args()

    if args.summarize:
        summarize_results()
    else:
        run_benchmark()
        summarize_results()