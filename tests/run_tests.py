import os
import json
import pickle
import argparse
import time
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
from pyswarms.discrete.binary import BinaryPSO
from libs.optimization_functions import (
    carbon_intensity_wrapper,
    load_possible_links_from_csv,
    #total_carbon_intensity, total_carbon_intensity_vch,
    carbon_intensity_wrapper_vch
)
from libs.shortest_paths import (
    all_pairs_k_shortest_paths,
    all_pairs_k_shortest_paths_nx
)
from libs.utils import generate_initial_positions


PROJECT_ROOT = Path(__file__).parent

# Tipografía / tamaño de figura
fuente = 14
fuente_eje = 11
fuente_leyenda = fuente-5
fs = (6, 4)

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
# SOLUCIONES CON TODOS LOS ENLACES ENCENDIDOS
# ============================================================

SOLUCIONES_COMPLETAS = {
    "Abilene": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    "Geant": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    "Nobel": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    "Germany": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
}


# ============================================================
# MEJORES SOLUCIONES PSO
# ============================================================

BEST_SOLUTIONS = {
    "Abilene": {
        1: [1,1,1,0,1,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,1,1,0,0,1],
        2: [1,1,1,0,1,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,1,1,0,0,1],
        3: [1,1,1,0,1,1,0,1,0,0,1,0,1,1,0,0,0,1,0,0,1,1,0,0,0,1,1,0,0,1],
        4: [1,1,1,0,1,1,0,0,0,1,1,1,1,1,0,0,1,0,0,1,0,1,1,0,1,0,0,1,1,1],
        5: [1,1,1,1,1,1,0,0,0,1,1,0,1,1,0,1,1,0,0,1,0,1,1,0,1,0,0,1,1,1],
    },
    "Geant": {
        1: [0,0,1,1,1,1,1,0,0,1,1,1,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1,1,1,1,0,0,1,1,0,1,1,1,1,0,0,1,0,1,0,0,0,1,0,1,1,1,0,1,1,1,1,0,1,1,1,1,1,0,1,0,1,0,1,1,1,1],
        2: [1,1,1,1,1,1,1,1,1,0,1,1,0,0,0,1,1,1,0,1,1,1,1,1,1,0,1,1,1,1,1,0,1,0,1,1,0,1,1,1,0,1,1,1,0,0,0,1,0,1,0,1,0,1,0,0,1,1,0,1,1,1,1,1,1,0,1,1,1,1,0,1],
        3: [0,1,0,1,1,0,1,1,1,1,1,1,0,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,1,1,1,0,0,1,1,1,0,0,1,0,1,1,0,1,1,1,1,1,0,1,0,1,1,1,0,1,1,0,1,1,1,1,1,0,1,1,1,1,0,1,1],
        4: [1,1,1,0,1,0,0,1,1,1,1,1,0,0,1,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,1,1,1,0,1,0,1,1,0,1,0,1],
        5: [0,1,1,1,1,1,1,1,1,0,1,1,0,0,1,1,1,1,0,0,1,1,1,1,0,1,1,0,1,0,1,1,0,1,1,1,1,1,0,1,0,1,1,0,1,1,0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,0,1,0,0,1,1,0,1,1],
    },
    "Nobel": {
        1: [1,1,1,1,1,1,1,1,1,1,0,0,1,0,1,0,1,1,1,1,0,0,1,1,1,0,0,1,1,1,0,1,1,0,1,1,0,1,0,0,0,1,1,0,1,1,0,1,0,1,0,0],
        2: [1,1,0,1,1,0,1,1,1,1,0,1,1,0,1,0,1,0,0,0,1,1,0,1,0,1,1,1,0,0,1,1,0,1,0,1,1,0,1,1,1,1,0,0,1,1,0,0,0,1,1,0],
        3: [1,0,1,1,1,1,1,1,1,0,0,1,0,0,1,0,1,1,1,0,0,1,1,1,1,0,1,1,1,0,0,0,1,0,1,1,0,0,1,0,1,1,1,0,1,1,0,0,1,1,0,0],
        4: [1,0,1,1,1,0,1,1,1,1,1,1,0,0,0,1,0,1,1,1,0,0,1,1,0,1,1,1,1,0,0,1,1,1,0,1,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,0],
        5: [1,0,1,0,1,1,1,1,1,1,1,1,0,0,1,0,0,1,1,0,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,1,1,0,1,1,0,1,0,1,1,1,0,1,1,1,1,0],
    },
}





def total_carbon_intensity(position, **kwargs):
    nodes_traffic = defaultdict(int)
    links_traffic = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=float)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0

    # Crear conjunto de enlaces activos
    active_links = set()
    for i in range(kwargs['num_nodes']):
        for j in range(kwargs['num_nodes']):
            if position[i][j] == 1:
                active_links.add((i, j))

    # Función auxiliar para verificar si un camino usa solo enlaces activos
    def path_is_valid(v_path):
        for index in range(len(v_path) - 1):
            if (v_path[index], v_path[index + 1]) not in active_links:
                return False
        return True

    # Función auxiliar para verificar capacidad disponible
    def path_has_capacity(v_path, v_demand, current_links_traffic):
        """
        Verifica si un camino tiene capacidad suficiente para la demanda.
        """
        for index in range(len(v_path) - 1):
            src_node = v_path[index]
            dst_node = v_path[index + 1]
            current_flow = current_links_traffic[src_node][dst_node]
            max_flow = kwargs['nodes_max_flow'][src_node][dst_node]

            if current_flow + v_demand > max_flow:
                return False
        return True

    # Asignación de flujos
    # Crear lista de demandas ordenadas
    demands = []
    for src in range(kwargs['num_nodes']):
        for dst in range(kwargs['num_nodes']):
            if src != dst:
                demand = kwargs['flow_matrix'][src][dst]
                demands.append((src, dst, demand))

    # Ordenar por demanda descendente
    demands.sort(key=lambda x: x[2], reverse=True)

    # Intentar asignar cada flujo
    for (src, dst, demand) in demands:
        if demand == 0:
            continue

        # Buscar el mejor camino disponible
        selected_path = None

        if (src, dst) in kwargs['all_k_paths']:
            for path in kwargs['all_k_paths'][(src, dst)]:
                if path_is_valid(path) and path_has_capacity(path, demand, links_traffic):
                    selected_path = path
                    break

        # Si no hay camino válido, topología inválida
        if selected_path is None:
            return float('inf')

        # Actualizar tráfico en enlaces y nodos
        prev = selected_path[0]
        for n in selected_path[1:]:
            links_traffic[prev][n] += demand
            nodes_traffic[n] += demand
            prev = n

    # Cargar la información histórica de carbono de esa red
    nodes_carbon_intensity = json.load(open(
        './resources/topologies/Historic_Carbon_Intensity/' + kwargs['filepath'] + '.json'))

    # Cálculo de emisiones
    per_node_emissions = {}

    for node_x in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
        node_dynamic = nodes_traffic[node_x] * lambda_n * node_carbon
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon
        node_ports = 0.0

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

        per_node_emissions[node_x] = {
            'dynamic': node_dynamic,
            'ports': node_ports,
            'total': node_dynamic + node_ports,
            'carbon_intensity': node_carbon,
            'traffic': nodes_traffic[node_x],
            'active_links': sum(1 for ny in range(kwargs['num_nodes'])
                                if node_x != ny and position[node_x][ny] != 0)
        }

    return {
        'total': dynamic_power + power_ports,
        'dynamic_power': dynamic_power,
        'power_ports': power_ports,
        'active_links': len(active_links),
        'link_utilization': links_traffic / kwargs['nodes_max_flow'],
        'per_node_emissions': per_node_emissions
    }






def total_carbon_intensity_vch(position, **kwargs):
    nodes_traffic = defaultdict(int)
    links_traffic = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=float)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0
    violations = 0
    big_m = 1e12

    # Crear conjunto de enlaces activos
    active_links = set()
    for i in range(kwargs['num_nodes']):
        for j in range(kwargs['num_nodes']):
            if position[i][j] == 1:
                active_links.add((i, j))

    # Función auxiliar para verificar si un camino usa solo enlaces activos
    def path_is_valid(v_path):
        for index in range(len(v_path) - 1):
            if (v_path[index], v_path[index + 1]) not in active_links:
                return False
        return True

    # Función auxiliar para verificar capacidad disponible
    def path_has_capacity(v_path, v_demand, current_links_traffic):
        """
        Verifica si un camino tiene capacidad suficiente para la demanda.
        """
        for index in range(len(v_path) - 1):
            src_node = v_path[index]
            dst_node = v_path[index + 1]
            current_flow = current_links_traffic[src_node][dst_node]
            max_flow = kwargs['nodes_max_flow'][src_node][dst_node]

            if current_flow + v_demand > max_flow:
                return False
        return True

    # Asignación de flujos
    # Crear lista de demandas ordenadas
    demands = []
    for src in range(kwargs['num_nodes']):
        for dst in range(kwargs['num_nodes']):
            if src != dst:
                demand = kwargs['flow_matrix'][src][dst]
                demands.append((src, dst, demand))

    # Ordenar por demanda descendente
    demands.sort(key=lambda x: x[2], reverse=True)

    # Intentar asignar cada flujo
    for (src, dst, demand) in demands:
        if demand == 0:
            continue

        # Buscar el mejor camino disponible
        selected_path = None

        if (src, dst) in kwargs['all_k_paths']:
            for path in kwargs['all_k_paths'][(src, dst)]:
                if path_is_valid(path) and path_has_capacity(path, demand, links_traffic):
                    selected_path = path
                    break

        # Si no hay camino válido, topología inválida
        if selected_path is None:
            violations += 1
            continue

        # Actualizar tráfico en enlaces y nodos
        prev = selected_path[0]
        for n in selected_path[1:]:
            links_traffic[prev][n] += demand
            nodes_traffic[n] += demand
            prev = n

    # Cargar la información histórica de carbono de esa red
    nodes_carbon_intensity = json.load(open(
        './resources/topologies/Historic_Carbon_Intensity/' + kwargs['filepath'] + '.json'))

    # Cálculo de emisiones
    for node_x in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    total_cost = dynamic_power + power_ports + violations*big_m
    return total_cost








# ============================================================
# GRÁFICA 1 — % de enlaces apagados por TM  (una por red)
# ============================================================

def plot_sleeping_links_per_tm(
    results_per_tm: dict[int, dict],
    network: str,
    total_links: int,
    output_dir: str | Path = None,
    fmt: str = "pdf",
    show: bool = True,
):
    """
    Gráfica de barras con el porcentaje de enlaces apagados para cada TM.

    Parámetros
    ----------
    results_per_tm : dict  { tm_index -> resultado de total_carbon_intensity() }
                     Cada valor debe tener la clave 'active_links'.
    network        : nombre de la red (usado en título y nombre de fichero).
    total_links    : número total de enlaces posibles en la topología.
    output_dir     : carpeta de salida. Por defecto <PROJECT_ROOT>/results/figures/
    fmt            : formato — "pdf", "png", "svg" …
    show           : si True llama a plt.show().
    """
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    labels   = []
    sleeping = []

    for tm, result in sorted(results_per_tm.items()):
        active = result["active_links"]
        pct    = (1 - active / total_links) * 100
        labels.append(f"TM{tm}")
        sleeping.append(pct)

    plt.rcParams.update({"font.size": fuente, "axes.labelsize": fuente_eje})
    fig, ax = plt.subplots(figsize=fs)

    ax.bar(labels, sleeping, color="#F06292", alpha=0.88)

    ax.set_ylabel("Enlaces apagados (%)")
    ax.set_ylim(0, 100)
    #ax.set_title(f"Porcentaje de enlaces apagados — {network}", fontsize=fuente + 1, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.55)
    ax.set_axisbelow(True)

    # Anotar valor encima de cada barra
    #for i, v in enumerate(sleeping):
    #    ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=fuente - 1)

    fig.tight_layout()

    filepath = output_dir / f"sleeping_links_{network}.{fmt}"
    fig.savefig(filepath, format=fmt, dpi=600, bbox_inches="tight")
    print(f"  Guardada: {filepath}")

    if show:
        plt.show()
    plt.close(fig)


# ============================================================
# GRÁFICA 2 — Histograma de % de uso de enlaces  (una por red)
# ============================================================

def plot_link_utilization_histogram(
    results_per_tm: dict[int, dict],
    network: str,
    possible_links: list[tuple],
    output_dir: str | Path = None,
    fmt: str = "pdf",
    show: bool = True,
    bins: int = 20,
):
    """
    Histograma del porcentaje de utilización de los enlaces activos,
    agregando todos los TM de la red.

    Parámetros
    ----------
    results_per_tm : dict  { tm_index -> resultado de total_carbon_intensity() }
                     Cada valor debe tener la clave 'link_utilization' (matriz NxN).
    network        : nombre de la red.
    possible_links : lista de tuplas (i, j) con los enlaces posibles de la topología.
    output_dir     : carpeta de salida. Por defecto <PROJECT_ROOT>/results/figures/
    fmt            : formato — "pdf", "png", "svg" …
    show           : si True llama a plt.show().
    bins           : número de bins del histograma (default 20).
    """
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    #all_utilizations = []
#
    #for tm, result in sorted(results_per_tm.items()):
    #    util_matrix = result["link_utilization"]   # matriz NxN con valores en [0, 1]
#
    #    for (i, j) in possible_links:
    #        u = util_matrix[i][j]
    #        if u > 0:   # solo enlaces activos (apagados tienen u == 0)
    #            all_utilizations.append(u * 100)

    # Sumar las matrices de utilización de todos los TM y dividir entre el número de TM
    sorted_results = sorted(results_per_tm.items())
    n_tms = len(sorted_results)

    avg_util_matrix = sum(
        result["link_utilization"] for _, result in sorted_results
    ) / n_tms

    # Un valor por enlace (solo los activos en media)
    avg_utilizations = []
    for (i, j) in possible_links:
        u = avg_util_matrix[i][j]
        if u > 0:
            avg_utilizations.append(u * 100)


    plt.rcParams.update({"font.size": fuente, "axes.labelsize": fuente_eje})
    fig, ax = plt.subplots(figsize=fs)

    ax.hist(
        avg_utilizations,
        bins=bins,
        range=(0, 100),
        color="#8E44AD",
        alpha=0.85,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_xlabel("Utilización del enlace (%)")
    ax.set_ylabel("Número de enlaces")
    ax.set_xlim(0, 100)
    #ax.set_title(f"Distribución de uso de enlaces — {network}", fontsize=fuente + 1, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.55)
    ax.set_axisbelow(True)

    fig.tight_layout()

    filepath = output_dir / f"link_utilization_{network}.{fmt}"
    fig.savefig(filepath, format=fmt, dpi=600, bbox_inches="tight")
    print(f"  Guardada: {filepath}")

    if show:
        plt.show()
    plt.close(fig)










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
        #G.add_edge(i, j, weight=1)

    paths = all_pairs_k_shortest_paths_nx(G, k)

    with open(cache_path, "wb") as f:
        pickle.dump(paths, f)

    return paths


# ============================================================
# PSO
# ============================================================

def run_pso(kwargs, init_pos, vch):
    dimensions = init_pos.shape[1]
    print(dimensions)

    pso = BinaryPSO(
        n_particles=PSO_CONFIG["n_particles"],
        dimensions=dimensions,
        options=PSO_CONFIG["options"],
        init_pos=init_pos
    )

    if vch:
        return pso.optimize(
            carbon_intensity_wrapper_vch,
            iters=PSO_CONFIG["iters"],
            n_processes=PSO_CONFIG["n_processes"],
            **kwargs
        )
    else:
        return pso.optimize(
            carbon_intensity_wrapper,
            iters=PSO_CONFIG["iters"],
            n_processes=PSO_CONFIG["n_processes"],
            **kwargs
        )


# ============================================================
# MAIN EXPERIMENTO
# ============================================================

def run_experiment(network="Abilene", tm=1, comprobar_solucion_jose=False, k=10, vch=False):
    print(f"\nEjecutando {network} | TM{tm}")

    start_time_init = time.time()
    kwargs = load_network(network, tm)
    dimensions = len(kwargs["possible_links"])
    kwargs["all_k_paths"] = load_k_paths(
        network,
        kwargs["carbon_matrix"],
        kwargs["possible_links"],
        k
    )

    init_pos = generate_initial_positions(PSO_CONFIG["n_particles"], dimensions)

    #start_time = time.time()
    #best_cost, best_pos = run_pso(kwargs, init_pos, vch)
    #end_time = time.time()

    #print("\n=== RESULTADO FINAL ===")
    #print("Best cost:", best_cost)
    #print("Best position:", best_pos)
    #print("Tiempo con carga de entorno: ", end_time - start_time_init)
    #print("Tiempo sin carga de entorno: ", end_time - start_time)

    #adj = np.zeros((kwargs["num_nodes"], kwargs["num_nodes"]), dtype=int)
    #for k, (i, j) in enumerate(kwargs["possible_links"]):
    #    adj[i][j] = SOLUCIONES_COMPLETAS[network][k]
#
    #cost = total_carbon_intensity(adj, **kwargs)
    #print("\n=== SOLUCIÓN CON TODOS LOS ENLACES ENCENDIDOS ===")
    #print("Coste:", cost)

    results_normal = {}

    for network_v, tms in BEST_SOLUTIONS.items():
        for tm_v, solution_vector in tms.items():
            kwargs = load_network(network_v, tm_v)
            kwargs["all_k_paths"] = load_k_paths(
                network_v,
                kwargs["carbon_matrix"],
                kwargs["possible_links"],
                k
            )
            adj = np.zeros((kwargs["num_nodes"], kwargs["num_nodes"]), dtype=int)
            for idx, (i, j) in enumerate(kwargs["possible_links"]):
                adj[i][j] = solution_vector[idx]

            result_test = total_carbon_intensity(adj, **kwargs)
            #print(result_test['link_utilization'])
            results_normal[tm_v] = result_test

        total_links = len(kwargs["possible_links"])

        # Gráfica 1: % de enlaces apagados
        plot_sleeping_links_per_tm(
            results_per_tm=results_normal,
            network=network_v,
            total_links=total_links
        )

        # Gráfica 2: histograma de utilización de enlaces
        plot_link_utilization_histogram(
            results_per_tm=results_normal,
            network=network_v,
            possible_links=kwargs["possible_links"]
        )


    if comprobar_solucion_jose:
        adj = np.zeros((kwargs["num_nodes"], kwargs["num_nodes"]), dtype=int)
        for k, (i, j) in enumerate(kwargs["possible_links"]):
            adj[i][j] = JOSE_SOLUTIONS[network][tm][k]

        cost = total_carbon_intensity(adj, **kwargs)
        print("\n=== VERIFICACIÓN JOSE ===")
        print(f"Solución proporcionada: {JOSE_SOLUTIONS[network][tm]}")
        print("Coste:", cost)



# ============================================================
# EVALUACIÓN DE MEJORES SOLUCIONES
# ============================================================

def evaluate_best_solutions(k=15, fmt="pdf", show=True):
    """
    Para cada red y TM definidos en BEST_SOLUTIONS:
      - Carga el entorno de red.
      - Evalúa el vector solución con total_carbon_intensity
        y total_carbon_intensity_vch.
      - Imprime los costes por consola.
      - Genera las gráficas de enlaces apagados y utilización.
    """
    for network, tms in BEST_SOLUTIONS.items():
        print(f"\n{'='*50}")
        print(f"  Red: {network}")
        print(f"{'='*50}")

        results_normal = {}
        kwargs = {}

        for tm, solution_vector in tms.items():
            if not solution_vector:
                print(f"  [AVISO] {network} TM{tm}: vector vacío, se omite.")
                continue

            print(f"\n  Cargando {network} TM{tm}...")
            kwargs = load_network(network, tm)
            kwargs["all_k_paths"] = load_k_paths(
                network,
                kwargs["carbon_matrix"],
                kwargs["possible_links"],
                k
            )

            # Vector 1D -> matriz de adyacencia NxN (igual que comprobar_jose)
            adj = np.zeros((kwargs["num_nodes"], kwargs["num_nodes"]), dtype=int)
            for idx, (i, j) in enumerate(kwargs["possible_links"]):
                adj[i][j] = solution_vector[idx]

            # Evaluar con ambas funciones
            result_normal = total_carbon_intensity(adj, **kwargs)
            result_vch    = total_carbon_intensity_vch(adj, **kwargs)

            if result_normal != float('inf'):
                results_normal[tm] = result_normal
                print(f"    Normal — coste: {result_normal['total']:.4f} "
                      f"| enlaces activos: {result_normal['active_links']}")
            else:
                print(f"    Normal — TM{tm}: solución inválida (inf)")

            print(f"    VCH    — coste: {result_vch:.4f}")

        if not results_normal or not kwargs:
            print(f"  Sin resultados válidos para {network}, se omiten las gráficas.")
            continue

        total_links = len(kwargs["possible_links"])

        # Gráfica 1: % de enlaces apagados por TM
        plot_sleeping_links_per_tm(
            results_per_tm=results_normal,
            network=network,
            total_links=total_links,
            fmt=fmt,
            show=show,
        )

        # Gráfica 2: histograma de utilización de enlaces
        plot_link_utilization_histogram(
            results_per_tm=results_normal,
            network=network,
            possible_links=kwargs["possible_links"],
            fmt=fmt,
            show=show,
        )


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default="Abilene")
    parser.add_argument("--tm", type=int, default=1)
    parser.add_argument("--comprobar_jose", action="store_true")
    parser.add_argument("--vch", action="store_true")
    parser.add_argument("--k", type=int, default=10)

    args = parser.parse_args()

    run_experiment(
        network=args.network,
        tm=args.tm,
        comprobar_solucion_jose=args.comprobar_jose,
        k=args.k,
        vch=args.vch
    )
