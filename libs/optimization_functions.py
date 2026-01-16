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

    # DEBUG
    # print(f"\n=== total_carbon_intensity called ===")
    # print(f"position shape: {position.shape}")
    # print(f"position non-zero count: {np.count_nonzero(position)}")
    # print(f"position:\n{position}")

    # edges_count = 0

    # for i in range(kwargs['num_nodes']):
    #     for j in range(kwargs['num_nodes']):
    #         if position[i][j] == 1:
    #             edges_count += 1

    # if edges_count < kwargs['num_nodes']:
    #     return float('inf')

    nodes_traffic = defaultdict(int)
    links_traffic = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=float)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0

    # A partir de la matriz de carbono, generar el grafo dirigido y los caminos más cortos con Dijkstra
    # result_carbon_matrix = np.where(position == 1, kwargs['carbon_matrix'], 0)
    # carbon_digraph = nx.from_numpy_array(result_carbon_matrix, create_using=nx.DiGraph)

    carbon_digraph = nx.DiGraph()

    # for i in range(kwargs['num_nodes']):
    #     for j in range(kwargs['num_nodes']):
    #         if position[i][j] == 1:
    #             carbon_digraph.add_edge(
    #                 i, j,
    #                 weight=kwargs['carbon_matrix'][i][j]
    #             )

    # Construir primero el grafo con los nodos
    for i in range(kwargs['num_nodes']):
        carbon_digraph.add_node(i)

    # Incluir los arcos (enlaces)
    for i in range(kwargs['num_nodes']):
        for j in range(kwargs['num_nodes']):
            if position[i][j] == 1:
                # Verificar que este enlace esté en possible_links
                if (i, j) in kwargs['possible_links']:
                    carbon_digraph.add_edge(i, j, weight=kwargs['carbon_matrix'][i][j])

    # DEBUG: Mostrar qué enlaces se añadieron
    # print(f"\nEdges added to graph:")
    # for edge in carbon_digraph.edges():
    #     print(f"  {edge}")

    shortest_paths = dict(nx.all_pairs_dijkstra_path(carbon_digraph, weight='weight'))

    # DEBUG
    # print(f"Graph has {carbon_digraph.number_of_nodes()} nodes and {carbon_digraph.number_of_edges()} edges")
    # print(f"Is strongly connected: {nx.is_strongly_connected(carbon_digraph)}")
    # for src in shortest_paths:
    #     print(f"From node {src}, can reach {len(shortest_paths[src])} nodes")

    # Si no es fuertemente conexo, solución no válida
    if not nx.is_strongly_connected(carbon_digraph):
        #     print(
        #     f"⚠️  Graph NOT strongly connected! Nodes: {carbon_digraph.number_of_nodes()}, Edges: {carbon_digraph.number_of_edges()}")
        return float('inf')
        # else:
        # print(
        #     f"✓ Graph is strongly connected. Nodes: {carbon_digraph.number_of_nodes()}, Edges: {carbon_digraph.number_of_edges()}")

    # Lista de flujos con sus rutas
    flow_list = []
    for src in shortest_paths:
        for dst in shortest_paths:
            if src != dst:
                demand = kwargs['flow_matrix'][src][dst]
                path = shortest_paths[src][dst]
                flow_list.append((src, dst, demand, path))

    # Ordenar flujos por demanda (en orden descendente)
    flow_list.sort(key=lambda x: x[2], reverse=True)

    # Comprobar que los flujos no superan la capacidad de los enlaces
    for (src, dst, demand, path) in flow_list:
        prev = path[0]
        for n in path[1:]:
            if links_traffic[prev][n] + demand > kwargs['nodes_max_flow'][prev][n]:
                return float('inf')
            links_traffic[prev][n] += demand
            nodes_traffic[n] += demand
            prev = n

    # Cargar la información histórica de carbono de esa red
    nodes_carbon_intensity = json.load(open(
        './resources/topologies/Historic_Carbon_Intensity/' + kwargs['filepath'] + '.json'))


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
Wrapper function to apply total_carbon_intensity to every particle in the swarm
"""
def carbon_intensity_wrapper(positions, **kwargs):
    n_particles = positions.shape[0]
    results = np.zeros(n_particles)

    for i in range(n_particles):
        # Crear matriz de adyacencia con ceros
        adj_matrix = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=int)

        # Enumerar los pares de posibles links (nodo_src, nodo_dst) y por cada uno de ellos
        # almacenar el valor (0 o 1, encendido o apagado) en la matriz de adyacencia
        for k, (x, y) in enumerate(kwargs['possible_links']):
            # El índice i
            adj_matrix[x][y] = positions[i][k]
        results[i] = total_carbon_intensity(adj_matrix, **kwargs)

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