from collections import defaultdict

import requests
from requests import Response

from carbon_api import obtener_carbon_intensity_nodo
import numpy as np
import networkx as nx

"""
- kwargs: dictionary            -> dictionary containing the following parameters
- num_nodes: int                -> number of nodes the topology has
- num_links: int                -> number of links the topology has
- position: np.array            -> np array (matrix) with a possible solution
- carbon_matrix: np.array       -> np array (matrix) with the carbon intensity for each link of the topology
- flow_matrix: np.array         -> np array (matrix) with the flow intensity for each link of the topology
- nodes_geoposition: dictionary -> dictionary of dictionaries containing the nodes and their positions (latitude, longitude)
- nodes_max_flow: dictionary    -> dictionary containing the maximum flow intensity for each node of the topology
"""

def total_carbon_intensity(num_nodes, num_links, position, carbon_matrix, flow_matrix, nodes_geoposition, cap_matrix, **kwargs) -> float:
    nodes_traffic = defaultdict(int)
    lambda_n = (41.625-23.375/400000)   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0

    result_carbon_matrix = np.bitwise_and(kwargs['carbon_matrix'], position)
    carbon_digraph = nx.from_numpy_array(result_carbon_matrix, create_using=nx.DiGraph)
    shortest_paths = dict(nx.all_pairs_dijkstra_path(carbon_digraph))

    for src in carbon_digraph.nodes:
        for dst in carbon_digraph.nodes:
            if src != dst:
                path = shortest_paths[src][dst]

                for n in path[1:]:
                    if kwargs['nodes_max_flow'][n] < flow_matrix[src][dst]+nodes_traffic[n]:
                        return 99999.0
                    else:
                        nodes_traffic[n] += flow_matrix[src][dst]

    for node in range(num_nodes):
        node_carbon_intensity = obtener_carbon_intensity_nodo(nodes_geoposition[node]['lat'], nodes_geoposition[node]['lon'])
        dynamic_power += nodes_traffic[node]*lambda_n*node_carbon_intensity

    for node_x in range(num_nodes):
        for node_y in range(num_nodes):
            if node_x != node_y and position[node_x][node_y] != 0:
                node_x_carbon = obtener_carbon_intensity_nodo(nodes_geoposition[node_x]['lat'], nodes_geoposition[node_x]['lon'])
                node_y_carbon = obtener_carbon_intensity_nodo(nodes_geoposition[node_y]['lat'], nodes_geoposition[node_y]['lon'])
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    return dynamic_power + power_ports





print(obtener_carbon_intensity_nodo(40.7833, -73.9667)) # New York node coordinates
print(obtener_carbon_intensity_nodo(38.897303, -77.026842)) # Washington node coordinates