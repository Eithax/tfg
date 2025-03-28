import numpy as np
import networkx as nx
from particle import Particle
from optimization_functions import total_carbon_intensity


class PSO:
    def __init__(self, num_nodes, num_particles, num_links):
        self.num_nodes = num_nodes
        self.num_particles = num_particles
        self.particles = [Particle(num_links) for _ in range(self.num_particles)]
        self.cap_matrix = np.empty((num_nodes, num_nodes))      # Capacity Matrix
        self.topology = np.empty((num_nodes, num_nodes))        # Network topology
        self.topology_graph = nx.DiGraph                        # Network topology as a networkx directed graph
        self.g_best = []                    # Best global position
        self.fitness_best = float('inf')    # Best global fitness value

    def load_cap_matrix(self, filename):
        self.cap_matrix = np.genfromtxt(filename, delimiter=',')
        print(self.cap_matrix)

    def create_topology(self, filename):
        self.topology = np.genfromtxt(filename, delimiter=',')
        print(self.topology)
        print('\n\n\n')
        self.topology_graph = nx.from_numpy_array(self.topology,  create_using=nx.DiGraph)
        path_len = dict(nx.all_pairs_dijkstra_path_length(self.topology_graph))
        path = dict(nx.all_pairs_dijkstra_path(self.topology_graph))

        for node in range(self.num_nodes):
            print(f"{node}: {path_len[node]}")

        print('\n\n\n')

        for node in range(self.num_nodes):
            print(f"{node}: {path[node]}")

    def evaluate_network(self, max_iter):
        for iteration in range(max_iter):
            for particle in self.particles:
                fitness = total_carbon_intensity()

                # Update local values
                if fitness < particle.fitness_best:
                    particle.fitness_best = fitness
                    particle.p_best = particle.position.copy()

                # Update global values
                if fitness < self.fitness_best:
                    self.fitness_best = fitness
                    self.g_best = particle.position.copy()

            # Update position and velocity of each particle
            for particle in self.particles:
                particle.update_position()
                particle.update_velocity()

        return self.g_best



# Tests

pso = PSO(12, 37, 24)
# pso.load_cap_matrix('.\\resources\\topologies\\AbileneCapMatrix.csv')
# pso.create_topology('.\\resources\\topologies\\AbileneCarbonMatrix.csv')
pso.create_topology('./resources/topologies/AbileneCarbonMatrix.csv')
pso.evaluate_network(3)