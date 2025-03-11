import numpy as np

class Particle:
    def __init__(self, num_links):
        self.position = np.empty(num_links)   # Particle position, represents a possible solution
        self.velocity = np.empty(num_links)   # Particle velocity, represents how the link configuration changes
        self.p_best = np.empty(num_links)     # Best individual position
        self.fitness_best = float('inf')      # Best individual fitness value
        self.fitness = float('inf')           # Individual fitness

    def evaluate(self, cost_func):
        self.fitness = cost_func

        if self.fitness < self.fitness_best:
            self.p_best = self.position
            self.fitness_best = self.fitness

    def update_position(self):
        self.position = np.where(self.velocity > 0.5, 1-self.position, self.position)