import numpy as np
import random
from .Algorithm import Algorithm

class AntColony(Algorithm):

    def __init__(self, map, num_agents, alpha=1, beta=2, rho=0.1, Q=1.0):
        super().__init__(map, num_agents)
        self.alpha = alpha
        self.beta = beta
        self.rho = rho      # evaporation rate
        self.Q = Q          # pheromone deposition constant

        # Pheromone on every free cell
        self.pheromone = np.ones(map.shape)

        # Tabu lists
        self.tabu = [[] for _ in range(num_agents)]

    def visibility(self, x, y):
        """Define η: heuristic desirability."""
        # We want high-idleness cells → attract ants
        return self.idleness[x, y] + 1   # avoid zero

    def compute_transition_probabilities(self, agent_index, pos):
        x, y = pos

        neighbors = [
            (x+dx, y+dy) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]
            if self.in_bounds(x+dx, y+dy) and self.map[x+dx,y+dy] == 0
        ]

        allowed = [n for n in neighbors if n not in self.tabu[agent_index]]
        if not allowed:
            allowed = neighbors

        scores = []
        for nx, ny in allowed:
            tau = self.pheromone[nx, ny]
            eta = self.visibility(nx, ny)
            scores.append((tau**self.alpha) * (eta**self.beta))

        total = sum(scores)
        if total == 0:
            probs = [1/len(scores)] * len(scores)
        else:
            probs = [s/total for s in scores]

        return allowed, probs

    def build_solutions(self):
        """Each ant builds a trajectory of moves."""
        trajectories = []

        for i, pos in enumerate(self.agents):
            allowed, probs = self.compute_transition_probabilities(i, pos)
            new_pos = random.choices(allowed, weights=probs, k=1)[0]
            trajectories.append((pos, new_pos))
            self.tabu[i].append(new_pos)

        return trajectories

    def update_pheromones(self, trajectories):
        """Classical lecture-compatible pheromone update."""
        # Evaporation
        self.pheromone = (1 - self.rho) * self.pheromone

        # Compute solution quality
        # For patrolling, let L_k = reduced idleness
        for (old_pos, new_pos) in trajectories:
            x, y = new_pos
            Lk = max(1, self.idleness[x, y])   # or another metric
            delta = self.Q / Lk
            self.pheromone[x, y] += delta

    def run_step(self):
        trajectories = self.build_solutions()
        final_positions = super().run_step([n for _, n in trajectories])
        self.update_pheromones(trajectories)
