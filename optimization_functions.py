from collections import defaultdict
from carbon_api import obtener_carbon_intensity_nodo
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
- nodes_max_flow: dictionary            -> dictionary containing the maximum flow intensity for each node of the topology

Local variables:
- nodes_carbon_intensity: dictionary    -> dictionary containing the carbon intensity for each node of the topology. Acts as a substitute for the API
"""

def total_carbon_intensity(position, **kwargs) -> float:
    nodes_traffic = defaultdict(int)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0

    #result_carbon_matrix = np.bitwise_and(kwargs['carbon_matrix'], position)
    result_carbon_matrix = np.where(position == 1, kwargs['carbon_matrix'], 0)
    carbon_digraph = nx.from_numpy_array(result_carbon_matrix, create_using=nx.DiGraph)
    shortest_paths = dict(nx.all_pairs_dijkstra_path(carbon_digraph))

    if not nx.is_strongly_connected(carbon_digraph):
        return float('inf')

    for src in list(shortest_paths.keys()):
        for dst in list(shortest_paths.keys()):
            if src != dst:
                path = shortest_paths[src][dst]

                for n in path[1:]:
                    if kwargs['nodes_max_flow'][n] < kwargs['flow_matrix'][src][dst]+nodes_traffic[n]:
                        return float('inf')
                    else:
                        nodes_traffic[n] += kwargs['flow_matrix'][src][dst]

    nodes_carbon_intensity = json.load(open('./resources/topologies/Emissions/Abilene/emisiones_Abilene_20250421_2131.json'))

    for node in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['emisiones'][node]
        #node_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node]['lat'], kwargs['nodes_geoposition'][node]['lon'])
        dynamic_power += nodes_traffic[node]*lambda_n*node_carbon

    for node_x in range(kwargs['num_nodes']):
        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                # node_x_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_x]['lat'], kwargs['nodes_geoposition'][node_x]['lon'])
                # node_y_carbon = obtener_carbon_intensity_nodo(kwargs['nodes_geoposition'][node_y]['lat'], kwargs['nodes_geoposition'][node_y]['lon'])
                node_x_carbon = nodes_carbon_intensity['emisiones'][node_x]
                node_y_carbon = nodes_carbon_intensity['emisiones'][node_y]
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    return (dynamic_power + power_ports)/3600000





print(obtener_carbon_intensity_nodo(40.7833, -73.9667)) # New York node coordinates
# print(obtener_carbon_intensity_nodo(38.897303, -77.026842)) # Washington node coordinates