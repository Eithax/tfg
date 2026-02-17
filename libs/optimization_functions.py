from collections import defaultdict
from api.carbon_api import obtener_carbon_intensity_nodo
import numpy as np
import networkx as nx
import json

"""
Parameters
- position: np.array                    -> np array (matrix) with a possible solution
- kwargs: dictionary                    -> dictionary containing the following parameters
- num_nodes: int                        -> number of nodes the topology has
- carbon_matrix: np.array               -> np array (matrix) with the carbon intensity for each link of the topology
- flow_matrix: np.array                 -> np array (matrix) with the flow intensity for each link of the topology
- nodes_geoposition: dictionary         -> dictionary of dictionaries containing the nodes and their positions (latitude, longitude)
- nodes_max_flow: dictionary            -> np array (matrix) containing the maximum flow intensity for each link of the topology
- possible_links: list                  -> list of tuples that define the links available in the network
- filepath: string                      -> string with the relative path for the historic carbon intensity file for a specific network

Local variables:
- nodes_carbon_intensity: dictionary    -> dictionary containing the carbon intensity for each node of the topology. Acts as a substitute for the API
"""

def total_carbon_intensity(position, **kwargs) -> float:
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
    for node_x in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
        # node_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node]['lat'], kwargs['nodes_geoposition'][node]['lon'])
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                # node_x_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_x]['lat'], kwargs['nodes_geoposition'][node_x]['lon'])
                # node_y_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_y]['lat'], kwargs['nodes_geoposition'][node_y]['lon'])
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    return dynamic_power + power_ports


"""
Variación de total_carbon_intensity que maneja el número de violaciones que la solución en estudio comete
"""
def total_carbon_intensity_vch(position, **kwargs) -> float:
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
        # node_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node]['lat'], kwargs['nodes_geoposition'][node]['lon'])
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                # node_x_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_x]['lat'], kwargs['nodes_geoposition'][node_x]['lon'])
                # node_y_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_y]['lat'], kwargs['nodes_geoposition'][node_y]['lon'])
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    total_cost = dynamic_power + power_ports + violations*big_m
    return total_cost


"""
Función wrapper que aplica total_carbon_intensity a todas las partículas del enjambre
"""
def carbon_intensity_wrapper(positions, **kwargs):
    n_particles = positions.shape[0]
    results = np.zeros(n_particles)

    for i in range(n_particles):
        # Crear matriz de adyacencia con ceros
        adj_matrix = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=int)
        links = np.count_nonzero(positions[i])

        # Enumerar los pares de posibles links (nodo_src, nodo_dst) y por cada uno de ellos
        # almacenar el valor (0 o 1, encendido o apagado) en la matriz de adyacencia
        for k, (x, y) in enumerate(kwargs['possible_links']):
            # El índice i representa la partícula que se está procesando
            adj_matrix[x][y] = positions[i][k]

        G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)

        if not nx.is_strongly_connected(G): # Comprobar que la posición genera un grafo fuertemente conexo
            results[i] = float('inf')
        elif links < kwargs['num_nodes']: # Comprobar si la posición tiene al menos num_nodes enlaces activos
            results[i] = float('inf')
        else:
            results[i] = total_carbon_intensity(adj_matrix, **kwargs)

    return results

"""
Variación de carbon_intensity_wrapper que maneja las violaciones que cada solución comete
"""
def carbon_intensity_wrapper_vch(positions, **kwargs):
    n_particles = positions.shape[0]
    results = np.zeros(n_particles)
    big_m = 1e12

    for i in range(n_particles):
        # Crear matriz de adyacencia con ceros
        adj_matrix = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=int)
        links = np.count_nonzero(positions[i])

        # Enumerar los pares de posibles links (nodo_src, nodo_dst) y por cada uno de ellos
        # almacenar el valor (0 o 1, encendido o apagado) en la matriz de adyacencia
        for k, (x, y) in enumerate(kwargs['possible_links']):
            # El índice i representa la partícula que se está procesando
            adj_matrix[x][y] = positions[i][k]

        G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)

        if not nx.is_strongly_connected(G): # Comprobar que la posición genera un grafo fuertemente conexo
            results[i] = big_m
        elif links < kwargs['num_nodes']: # Comprobar si la posición tiene al menos num_nodes enlaces activos
            results[i] = (kwargs['num_nodes'] - links) * big_m
        else:
            results[i] = total_carbon_intensity_vch(adj_matrix, **kwargs)

    return results


def load_possible_links_from_csv(path):
    adjacency_mask = np.genfromtxt(path, delimiter=',')
    num_nodes = adjacency_mask.shape[0]

    possible_links = []

    for i in range(num_nodes):
        for j in range(num_nodes):
            if adjacency_mask[i, j] == 1:
                possible_links.append((i, j))

    return possible_links