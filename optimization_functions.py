from collections import defaultdict

import requests
from requests import Response

from carbon_api import obtener_carbon_intensity_nodo
import numpy as np
import networkx as nx

"""
- num_nodes: int                -> number of nodes the topology has
- num_links: int                -> number of links the topology has
- position: np.array            -> np array (matrix) with a possible solution
- carbon_matrix: np.array       -> np array (matrix) with the carbon intensity for each link of the topology
- flow_matrix: np.array         -> np array (matrix) with the flow intensity for each link of the topology
- nodes_geoposition: dictionary -> dictionary of dictionaries containing the nodes and their positions (latitude, longitude)
"""

def total_carbon_intensity(num_nodes, num_links, position, carbon_matrix, flow_matrix, nodes_geoposition) -> float:
    nodes_traffic = defaultdict(int)
    lambda_n = (333-187/39600000)   # W/Mbps

    result_carbon_matrix = np.bitwise_and(carbon_matrix, position)
    carbon_digraph = nx.from_numpy_array(result_carbon_matrix, create_using=nx.DiGraph)
    shortest_paths = dict(nx.all_pairs_dijkstra_path(carbon_digraph))

    for src in carbon_digraph.nodes:
        for dst in carbon_digraph.nodes:
            if src != dst:
                path = shortest_paths[src][dst]

                if flow_matrix[src][dst] > 0:
                    for n in path[:1]:
                        nodes_traffic[n] += flow_matrix[src][dst]

    dynamic_power = 0.0

    for node in range(num_nodes):
        node_carbon_intensity = obtener_carbon_intensity_nodo(nodes_geoposition[node]['lat'], nodes_geoposition[node]['lon'])
        dynamic_power += nodes_traffic[node]*lambda_n*node_carbon_intensity




obtener_carbon_intensity_nodo(33.75, -84.3833)