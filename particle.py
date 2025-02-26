class Particle:
    def __init__(self):
        self.position = []          # Particle position, represents a possible solution
        self.velocity = []          # Particle velocity, represents how the link configuration changes
        self.p_best = []            # Best individual position
        self.fitness_best = -1      # Best individual fitness value
        self.fitness = -1           # Individual fitness

    def evaluate(self, costFunc):
        self.fitness = costFunc

        if self.fitness < self.fitness_best or self.fitness_best == -1:
            self.p_best = self.position
            self.fitness_best = self.fitness

    def update_position(self, position):
        num_links = 8

        for i in range(0, num_links):
            self.position[i] = position[i]