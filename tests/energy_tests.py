from collections import defaultdict
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Tipografía / tamaño de figura
fuente     = 12
fuente_eje = 13
fs         = (7, 4)

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

    ax.bar(labels, sleeping, color="#E67E22", alpha=0.88)

    ax.set_ylabel("Enlaces apagados (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Porcentaje de enlaces apagados — {network}",
                 fontsize=fuente + 1, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.55)
    ax.set_axisbelow(True)

    # Anotar valor encima de cada barra
    for i, v in enumerate(sleeping):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=fuente - 1)

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

    all_utilizations = []

    for tm, result in sorted(results_per_tm.items()):
        util_matrix = result["link_utilization"]   # matriz NxN con valores en [0, 1]

        for (i, j) in possible_links:
            u = util_matrix[i][j]
            if u > 0:   # solo enlaces activos (apagados tienen u == 0)
                all_utilizations.append(u * 100)

    plt.rcParams.update({"font.size": fuente, "axes.labelsize": fuente_eje})
    fig, ax = plt.subplots(figsize=fs)

    ax.hist(
        all_utilizations,
        bins=bins,
        range=(0, 100),
        color="#3266AD",
        alpha=0.85,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_xlabel("Utilización del enlace (%)")
    ax.set_ylabel("Número de enlaces")
    ax.set_xlim(0, 100)
    ax.set_title(f"Distribución de uso de enlaces — {network}",
                 fontsize=fuente + 1, fontweight="bold")
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
# MEJORES SOLUCIONES  —  rellena cada TM con su vector óptimo
# ============================================================
#
# Formato: BEST_SOLUTIONS[red][tm] = lista de 0/1 con longitud
# igual al número de enlaces posibles de esa red:
#   Abilene ->  30 enlaces
#   Geant   ->  72 enlaces
#   Nobel   ->  52 enlaces

BEST_SOLUTIONS = {
    "Abilene": {
        1: [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        2: [],
        3: [],
        4: [],
        5: [],
    },
    "Geant": {
        1: [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        2: [],
        3: [],
        4: [],
        5: [],
    },
    "Nobel": {
        1: [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        2: [],
        3: [],
        4: [],
        5: [],
    },
}


# ============================================================
# MAIN — genera todas las gráficas para las redes definidas
# ============================================================

def run_analysis(fmt: str = "pdf", show: bool = True):
    """
    Para cada red en BEST_SOLUTIONS:
      1. Carga el entorno de cada TM.
      2. Convierte el vector solución en matriz de adyacencia.
      3. Llama a total_carbon_intensity y total_carbon_intensity_vch.
      4. Genera las gráficas de enlaces apagados y utilización.
    """
    # Ajusta este import a tu estructura de proyecto
    from tests.run_tests import load_network, load_k_paths

    for network, tms in BEST_SOLUTIONS.items():
        print(f"\n{'='*50}")
        print(f"  Procesando: {network}")
        print(f"{'='*50}")

        results_normal = {}
        kwargs         = {}

        for tm, solution_vector in tms.items():
            if not solution_vector:
                print(f"  [AVISO] {network} TM{tm}: vector vacío, se omite.")
                continue

            print(f"  Cargando TM{tm}...")
            kwargs = load_network(network, tm)
            kwargs["all_k_paths"] = load_k_paths(
                network,
                kwargs["carbon_matrix"],
                kwargs["possible_links"],
            )

            # Convertir vector 1D -> matriz de adyacencia NxN
            num_nodes = kwargs["num_nodes"]
            adj       = np.zeros((num_nodes, num_nodes), dtype=int)
            for idx, (i, j) in enumerate(kwargs["possible_links"]):
                adj[i][j] = solution_vector[idx]

            # Evaluar con ambas funciones
            result_normal = total_carbon_intensity(adj, **kwargs)
            result_vch    = total_carbon_intensity_vch(adj, **kwargs)

            if result_normal != float("inf"):
                results_normal[tm] = result_normal
                print(f"    Normal — coste: {result_normal['total']:.4f} | "
                      f"enlaces activos: {result_normal['active_links']}")
            else:
                print(f"    Normal — TM{tm}: solución inválida (inf)")

            print(f"    VCH    — coste: {result_vch:.4f}")

        if not results_normal:
            print(f"  Sin resultados válidos para {network}, se omiten las gráficas.")
            continue

        total_links = len(kwargs["possible_links"])

        # Gráfica 1: % de enlaces apagados
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Análisis de soluciones PSO")
    parser.add_argument("--fmt",     default="pdf", help="Formato: pdf, png, svg ...")
    parser.add_argument("--no-show", action="store_true", help="No llamar a plt.show()")
    args = parser.parse_args()

    run_analysis(fmt=args.fmt, show=not args.no_show)