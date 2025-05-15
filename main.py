import numpy as np
import json

def main():
    # PSO variables
    n_particles = 200
    dimensions = 12     # Number of dimensions in the space. In this case, number of nodes
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
    abilene_topology = np.genfromtxt('./resources/AbileneTopology.csv', delimiter=',')
    carbon_intensity_nodes = json.load(open('./resources/topologies/Emissions/Abilene/emisiones_Abilene_20250421_2131.json'))



if __name__ == "__main__":
    main()