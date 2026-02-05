import os
import json
import pickle
import argparse
import numpy as np
import networkx as nx

from pyswarms.discrete.binary import BinaryPSO

from libs.optimization_functions import (
    carbon_intensity_wrapper,
    load_possible_links_from_csv,
    total_carbon_intensity
)
from libs.shortest_paths import (
    all_pairs_k_shortest_paths,
    all_pairs_k_shortest_paths_nx
)

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================

PSO_CONFIG = {
    "n_particles": 200,
    "iters": 1200,
    "n_processes": 6,
    "options": {
        "c1": 1.75,
        "c2": 2.25,
        "w": 0.7,
        "k": 100,
        "p": 1
    }
}

LAMBDA_J = (41.625 - 23.375) / 400000  # W/Mbps


# ============================================================
# SOLUCIONES MANUALES (JOSE)
# ============================================================

JOSE_SOLUTIONS = {
    "Abilene": {
        1: [1,1,1,0,1,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,1,1,0,0,1],
        2: [1,1,1,0,1,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,1,1,0,0,1],
        3: [1,1,1,0,1,1,0,1,0,0,1,0,1,1,0,0,0,1,0,0,1,1,0,0,0,1,1,0,0,1],
        4: [1,1,1,0,1,1,0,0,0,1,1,1,1,1,0,0,1,0,0,1,0,1,1,0,1,0,0,1,1,1],
        5: [1,1,1,1,1,1,0,0,0,1,1,0,1,1,0,1,1,0,0,1,0,1,1,0,1,0,0,1,1,1]
    }
}


# ============================================================
# CARGA DE RED
# ============================================================

def load_network(network: str, tm: int):
    base = f"./resources/topologies"

    topology_path = f"{base}/{network}Topology.csv"
    carbon_path = f"{base}/Historic_Carbon_Intensity/{network}.json"
    tm_path = f"{base}/Matrices_trafico/{network}/{network}TM{tm}.csv"
    coords_path = f"{base}/Coordenadas/{network}Ubications.json"
    cap_path = f"{base}/Capacidades/{network}/{network}CapMatrix.csv"

    topology = np.genfromtxt(topology_path, delimiter=',')
    carbon_matrix = topology.copy()

    carbon_nodes = json.load(open(carbon_path))
    num_nodes = topology.shape[0]

    for i in range(num_nodes):
        for j in range(num_nodes):
            if topology[i][j] == 1:
                carbon_matrix[i][j] = 1 + (carbon_nodes['carbon_intensity'][j] / 1000) * LAMBDA_J

    traffic_matrix = np.genfromtxt(tm_path, delimiter=',')
    coordinates = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open(coords_path))]
    cap_matrix = np.genfromtxt(cap_path, delimiter=',')
    possible_links = load_possible_links_from_csv(topology_path)

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
# K-SHORTEST PATHS (CACHE)
# ============================================================

def load_k_paths(network, carbon_matrix, possible_links, k=10):
    cache_dir = f"resources/cache/shortest_paths/{network}"
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
# PSO
# ============================================================

def run_pso(kwargs, init_pos):
    dimensions = init_pos.shape[1]
    print(dimensions)

    pso = BinaryPSO(
        n_particles=PSO_CONFIG["n_particles"],
        dimensions=dimensions,
        options=PSO_CONFIG["options"],
        init_pos=init_pos
    )

    return pso.optimize(
        carbon_intensity_wrapper,
        iters=PSO_CONFIG["iters"],
        n_processes=PSO_CONFIG["n_processes"],
        **kwargs
    )


# ============================================================
# MAIN EXPERIMENTO
# ============================================================

def run_experiment(network="Abilene", tm=1, comprobar_solucion_jose=False, k=10):
    print(f"\nEjecutando {network} | TM{tm}")

    kwargs = load_network(network, tm)
    dimensions = len(kwargs["possible_links"])
    kwargs["all_k_paths"] = load_k_paths(
        network,
        kwargs["carbon_matrix"],
        kwargs["possible_links"],
        k
    )

    init_pos = np.random.randint(
        0, 2,
        size=(PSO_CONFIG["n_particles"], dimensions)
    )
    init_pos[0].fill(1)

    best_cost, best_pos = run_pso(kwargs, init_pos)

    print("\n=== RESULTADO FINAL ===")
    print("Best cost:", best_cost)
    print("Best position:", best_pos)

    if comprobar_solucion_jose:
        adj = np.zeros((kwargs["num_nodes"], kwargs["num_nodes"]), dtype=int)
        for k, (i, j) in enumerate(kwargs["possible_links"]):
            adj[i][j] = JOSE_SOLUTIONS[network][tm][k]

        cost = total_carbon_intensity(adj, **kwargs)
        print("\n=== VERIFICACIÓN JOSE ===")
        print(f"Solución proporcionada: {JOSE_SOLUTIONS[network][tm]}")
        print("Coste:", cost)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default="Abilene")
    parser.add_argument("--tm", type=int, default=1)
    parser.add_argument("--comprobar_jose", action="store_true")
    parser.add_argument("--k", type=int, default=10)

    args = parser.parse_args()

    run_experiment(
        network=args.network,
        tm=args.tm,
        comprobar_solucion_jose=args.comprobar_jose,
        k=args.k
    )
