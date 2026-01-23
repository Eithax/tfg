import random
import pickle
import networkx as nx
import numpy as np
import json
from pyswarms.discrete.binary import BinaryPSO
from libs.optimization_functions import carbon_intensity_wrapper, load_possible_links_from_csv, total_carbon_intensity
from libs.shortest_paths import all_pairs_k_shortest_paths


def main():
    # PSO variables
    n_particles = 200
    dimensions = 30     # Number of dimensions in the space. In this case, number of links
    c1 = 1.75           # Cognitive constant. Usually set between 1.5 and 2.5
    c2 = 2.25           # Social constant. Usually set between 1.5 and 2.5
    w = 0.7             # Inertia weight. Usually set between 0.4 and 0.9
    k = 100             # Number of neighbors to be considered
    options = {
        'c1': c1,
        'c2': c2,
        'w': w,
        'k': k,
        'p': 1
    }

    # total_carbon_intensity variables

    # Abilene

    abilene_topology = np.genfromtxt('./resources/topologies/AbileneTopology.csv', delimiter=',')
    abilene_carbon_matrix = abilene_topology.copy()
    carbon_intensity_nodes = json.load(open('./resources/topologies/Emissions/Abilene/emisiones_Abilene_20250421_2131.json'))
    lambda_j = (41.625 - 23.375) / 400000  # 0.000045625 W/Mbps
    num_nodes = abilene_topology.shape[0]

    for i in range(num_nodes):
        for j in range(num_nodes):
            if abilene_topology[i][j] == 1:
                abilene_carbon_matrix[i][j] = 1 + (carbon_intensity_nodes['emisiones'][j] / 1000) * lambda_j

    random_tm = random.randint(1, 5)
    path_abilene_tm = 'resources/topologies/Matrices_trafico/Abilene/AbileneTM5.csv'
    #path_abilene_tm = 'resources/topologies/Matrices_trafico/Abilene/AbileneTM' + str(random_tm) + '.csv'
    abilene_traffic_matrix = np.genfromtxt(path_abilene_tm, delimiter=',')
    abilene_coordinates = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open('resources/topologies/Coordenadas/AbileneUbications.json'))]
    abilene_cap_matrix = np.genfromtxt('resources/topologies/Capacidades/Abilene/AbileneCapMatrix.csv', delimiter=',')
    possible_links = load_possible_links_from_csv('./resources/topologies/AbileneTopology.csv')

    carbon_digraph = nx.DiGraph()

    # Construir primero el grafo con los nodos
    for i in range(num_nodes):
        carbon_digraph.add_node(i)

    # Incluir los arcos (enlaces)
    for (i, j) in possible_links:
        carbon_digraph.add_edge(i, j, weight=abilene_carbon_matrix[i][j])

    all_k_paths = all_pairs_k_shortest_paths(carbon_digraph, 10)

    with open('abilene_k10_paths.pkl', 'wb') as f:
        pickle.dump(all_k_paths, f)

    print("possible_links:")
    for i, (x, y) in enumerate(possible_links):
        print(f"{i}: ({x}, {y})")
    print(f"\nTotal: {len(possible_links)} enlaces")

    kwargs = {
        'num_nodes': num_nodes,
        'carbon_matrix': abilene_carbon_matrix,
        'flow_matrix': abilene_traffic_matrix,
        'nodes_geoposition': abilene_coordinates,
        'nodes_max_flow': abilene_cap_matrix,
        'possible_links': possible_links,
        'filepath': 'Abilene',
        'all_k_paths': all_k_paths
    }

    init_pos = np.random.randint(0, 2, size=(n_particles, dimensions))
    init_pos[0] = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])


    init_pos_2 = np.random.randint(0, 2, size=(n_particles, dimensions))
    init_pos_2[0] = [1,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            0,
            1,
            1,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            0,
            1,
            1,
            1]




    # Geant
    """
    geant_topology = np.genfromtxt('./resources/topologies/GeantTopology.csv', delimiter=',')
    geant_carbon_matrix = geant_topology.copy()
    carbon_intensity_nodes = json.load(open('./resources/topologies/Historic_Carbon_Intensity/Geant.json'))
    lambda_j = (41.625 - 23.375) / 400000  # 0.000045625 W/Mbps
    num_nodes = geant_topology.shape[0]

    for i in range(num_nodes):
        for j in range(num_nodes):
            if geant_topology[i][j] == 1:
                geant_carbon_matrix[i][j] = 1 + (carbon_intensity_nodes['carbon_intensity'][j] / 1000) * lambda_j

    random_tm = random.randint(1, 5)
    path_geant_tm = 'resources/topologies/Matrices_trafico/Geant/GeantTM1.csv'
    #path_geant_tm = 'resources/topologies/Matrices_trafico/Geant/GeantTM' + str(random_tm) + '.csv'
    geant_traffic_matrix = np.genfromtxt(path_geant_tm, delimiter=',')
    geant_coordinates = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open('resources/topologies/Coordenadas/GeantUbications.json'))]
    geant_cap_matrix = np.genfromtxt('resources/topologies/Capacidades/Geant/GeantCapMatrix.csv', delimiter=',')
    possible_links = load_possible_links_from_csv('./resources/topologies/GeantTopology.csv')

    kwargs = {
        'num_nodes': num_nodes,
        'carbon_matrix': geant_carbon_matrix,
        'flow_matrix': geant_traffic_matrix,
        'nodes_geoposition': geant_coordinates,
        'nodes_max_flow': geant_cap_matrix,
        'possible_links': possible_links
        'filepath': 'Geant'
    }
    """


    # Init PySwarms BinaryPSO
    pso = BinaryPSO(n_particles=n_particles, dimensions=dimensions, options=options, init_pos=init_pos)
    #pso = BinaryPSO(n_particles=n_particles, dimensions=dimensions, options=options, init_pos=init_pos_2)
    #pso = BinaryPSO(n_particles=n_particles, dimensions=dimensions, options=options)
    result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=1500, **kwargs)

    print("\n=== RESULTADO FINAL ===")
    print(f"Best position: {result[1]}")
    print(f"Best cost: {result[0]}")

    # Verificar manualmente la mejor solución
    adj_matrix_final = np.zeros((num_nodes, num_nodes), dtype=int)
    for k, (x, y) in enumerate(possible_links):
        adj_matrix_final[x][y] = result[1][k]

    print(f"\nEnlaces activos en mejor solución: {np.count_nonzero(adj_matrix_final)}")
    final_cost = total_carbon_intensity(adj_matrix_final, **kwargs)
    print(f"Cost verificado manualmente: {final_cost}")

    # [1,1,1,1,1,1,0,0,0,1,1,0,1,1,0,1,1,0,0,1,0,1,1,0,1,0,0,1,1,1]
    # [1 1 1 1 1 1 0 0 0 1 1 0 1 1 1 1 1 0 0 1 0 1 1 0 1 0 0 1 1 1]


if __name__ == "__main__":
    main()