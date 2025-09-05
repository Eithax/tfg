import random
import numpy as np
import json
from pyswarms.discrete.binary import BinaryPSO
from pso_libs.optimization_functions import carbon_intensity_wrapper, load_possible_links_from_csv


def main():
    # PSO variables
    n_particles = 200
    dimensions = 30     # Number of dimensions in the space. In this case, number of links
    c1 = 2.0            # Cognitive constant. Usually set between 1.5 and 2.5
    c2 = 2.0            # Social constant. Usually set between 1.5 and 2.5
    w = 0.7             # Inertia weight. Usually set between 0.4 and 0.9
    k = 20              # Number of neighbors to be considered
    options = {
        'c1': c1,
        'c2': c2,
        'w': w,
        'k': k,
        'p': 1
    }

    # total_carbon_intensity variables
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
    path_abilene_tm = 'resources/topologies/Matrices_trafico/Abilene/AbileneTM2.csv'
    #path_abilene_tm = 'resources/topologies/Matrices_trafico/Abilene/AbileneTM' + str(random_tm) + '.csv'
    abilene_traffic_matrix = np.genfromtxt(path_abilene_tm, delimiter=',')
    abilene_coordinates = [{'lon': lon, 'lat': lat} for lon, lat in json.load(open('resources/topologies/Coordenadas/AbileneUbications.json'))]
    abilene_cap_matrix = np.genfromtxt('resources/topologies/Capacidades/Abilene/AbileneCapMatrix.csv', delimiter=',')
    possible_links = load_possible_links_from_csv('./resources/topologies/AbileneTopology.csv')

    kwargs = {
        'num_nodes': num_nodes,
        'carbon_matrix': abilene_carbon_matrix,
        'flow_matrix': abilene_traffic_matrix,
        'nodes_geoposition': abilene_coordinates,
        'nodes_max_flow': abilene_cap_matrix,
        'possible_links': possible_links
    }


    # Init PySwarms BinaryPSO
    pso = BinaryPSO(n_particles=n_particles, dimensions=dimensions, options=options)
    result = pso.optimize(objective_func=carbon_intensity_wrapper, iters=1000, **kwargs)
    print(result)



if __name__ == "__main__":
    main()