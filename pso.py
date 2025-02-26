import numpy as np
import networkx as nx

class PSO:
    def __init__(self, num_links):
        self.num_links = num_links
        self.cap_matrix = np.empty((num_links, num_links))      # Capacity Matrix
        self.topology = np.empty((num_links, num_links))        # Network topology
        self.topology_graph = nx.DiGraph                        # Network topology as a networkx directed graph
        self.g_best = []            # Best global position
        self.fitness_best = -1      # Best global fitness value

    def load_cap_matrix(self, filename):
        self.cap_matrix = np.genfromtxt(filename, delimiter=',')
        print(self.cap_matrix)

    def create_topology(self, filename):
        self.topology = np.genfromtxt(filename, delimiter=',')
        print(self.topology)
        print('\n\n\n')
        self.topology_graph = nx.from_numpy_array(self.topology,  create_using=nx. DiGraph)
        path_len = dict(nx.all_pairs_dijkstra_path_length(self.topology_graph))
        path = dict(nx.all_pairs_dijkstra_path(self.topology_graph))

        for node in range(self.num_links):
            print(f"{node}: {path_len[node]}")

        print('\n\n\n')

        for node in range(self.num_links):
            print(f"{node}: {path[node]}")

# Tests

pso = PSO(12)
# pso.load_cap_matrix('.\\resources\\topologies\\AbileneCapMatrix.csv')
pso.create_topology('.\\resources\\topologies\\AbileneCarbonMatrix.csv')