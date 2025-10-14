import numpy as np
import random
from .Algorithm import Algorithm

class AntColony(Algorithm):
    def __init__(self, map: np.ndarray, num_agents: int, evaporation_rate=0.1, alpha=1, beta=2):
        super().__init__(map, num_agents)
        self.evaporation_rate = evaporation_rate
        self.alpha = alpha
        self.beta = beta
        self.pheromone = np.ones(map.shape)
        
        self.tabu_lists = [[] for _ in range(num_agents)]

    # Evaporate pheromone and add random noise
    def update_pheromone(self):
        self.evaporation_rate = min(self.evaporation_rate + 0.0005, 0.5)
        self.pheromone *= (1 - self.evaporation_rate)
        self.pheromone += np.random.uniform(0, 0.01, self.pheromone.shape)

    # Move agents based on pheromone and idleness
    def move_agents(self):
        for i, (x, y) in enumerate(self.agents):
            if random.random() < 0.05:
                neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
                neighbors = [(nx, ny) for nx, ny in neighbors
                             if 0 <= nx < self.map.shape[0] and 0 <= ny < self.map.shape[1]]
                if neighbors:
                    new_pos = random.choice(neighbors)
                    self.agents[i] = new_pos
                    self.pheromone[new_pos] += 1
                    self.idleness[new_pos] = 0
                    self.tabu_lists[i].append(new_pos)
                    if len(self.tabu_lists[i]) > 5:
                        self.tabu_lists[i].pop(0)
                continue

            neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
            neighbors = [(nx, ny) for nx, ny in neighbors
                         if 0 <= nx < self.map.shape[0] and 0 <= ny < self.map.shape[1]
                         and (nx, ny) not in self.tabu_lists[i]]

            if not neighbors:
                self.tabu_lists[i] = []
                continue

            probs = []
            for nx, ny in neighbors:
                pheromone_effect = self.pheromone[nx, ny] ** self.alpha
                idleness_effect = (self.idleness[nx, ny] + 1) ** self.beta
                probs.append(pheromone_effect * idleness_effect)

            total_prob = sum(probs)
            if total_prob == 0:
                probs = [1/len(probs)] * len(probs)
            else:
                probs = [p / total_prob for p in probs]

            new_pos = random.choices(neighbors, weights=probs, k=1)[0]
            self.agents[i] = new_pos

            if self.idleness[new_pos] > np.mean(self.idleness):
                self.pheromone[new_pos] += 2.0
            else:
                self.pheromone[new_pos] += 1

            self.idleness[new_pos] = 0

            self.tabu_lists[i].append(new_pos)
            if len(self.tabu_lists[i]) > 5:
                self.tabu_lists[i].pop(0)

    # New method to run a single step of the ACO algorithm
    def run_step(self):
        super().run_step()
        self.move_agents()
        self.update_pheromone()
