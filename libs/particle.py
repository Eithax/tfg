import numpy as np
import random

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

    def update_velocity(self, g_best, inertia_weight, cognitive_coefficient, social_coefficient):
        r1 = random.random()
        r2 = random.random()

        cognitive_influence = cognitive_coefficient * r1 * (self.p_best - self.position)    # Personal influence
        social_influence = social_coefficient * r2 * (g_best - self.position)               # Swarm/Global influence
        inertia = inertia_weight * self.velocity

        self.velocity = inertia + cognitive_influence + social_influence

        self.velocity = np.clip(self.velocity, 0, 1)