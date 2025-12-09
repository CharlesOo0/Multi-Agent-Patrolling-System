import numpy as np
import random
from .Algorithm import Algorithm


class AntColony(Algorithm):
    """Ant Colony Optimization (ACO) algorithm for multi-agent patrolling.

    Agents move according to a stochastic policy biased by pheromone intensity
    and cell idleness. Pheromones evaporate over time to avoid stagnation.
    """

    def __init__(
        self,
        map: np.ndarray,
        num_agents: int,
        evaporation_rate=0.1,
        alpha=1,
        beta=2,
        exploration_rate=0.15,
        tabu_length=15,
        **kwargs
    ):
        """Initialize the ACO algorithm state.

        Args:
            map: 2D numpy array where 0=free cell and 1=obstacle.
            num_agents: Number of agents to patrol the grid.
            evaporation_rate: Fraction of pheromone that evaporates each step (0-1).
            alpha: Exponent controlling the influence of pheromone.
            beta: Exponent controlling the influence of idleness.
        """
        super().__init__(map, num_agents, **kwargs)
        self.evaporation_rate = evaporation_rate
        self.alpha = alpha
        self.beta = beta
        self.exploration_rate = exploration_rate
        self.tabu_length = tabu_length
        self.pheromone = np.ones(map.shape)
        self.agentswork = [0.0 for _ in range(num_agents)]

        self.tabu_lists = [[] for _ in range(num_agents)]

    # Evaporate pheromone and add random noise
    def update_pheromone(self, new_positions: list[tuple[int, int]]):
        """Apply pheromones side effects and evaporation and inject small noise to encourage exploration.

        Side effects:
            - Increases evaporation rate slightly over time (capped at 0.5).
            - Scales down pheromone by (1 - evaporation_rate).
            - Adds uniform random noise in [0, 0.01] per cell to avoid stagnation.
        """
        # Apply movement side-effects now that `self.agents` contains resolved positions
        for i, pos in enumerate(new_positions):
            x, y = pos
            # Sanity: skip obstacles (shouldn't happen after resolution)
            if self.map[x, y] == 1:
                continue

            # Increase pheromone according to idleness prior to visiting (idleness
            # has already been incremented by super().run_step)
            if self.idleness[pos] > np.mean(self.idleness):
                self.pheromone[pos] += 2.0
            else:
                self.pheromone[pos] += 1.0

            # Accumulate agent workload and reset idleness at visited cell
            self.agentswork[i] += self.idleness[pos]

            # Update tabu list for the agent
            self.tabu_lists[i].append(pos)
            if len(self.tabu_lists[i]) > self.tabu_length:
                self.tabu_lists[i].pop(0)

        # Finally evaporate/add noise to pheromones
        self.evaporation_rate = min(self.evaporation_rate + 0.0005, 0.5)
        self.pheromone *= 1 - self.evaporation_rate
        self.pheromone += np.random.uniform(0, 0.01, self.pheromone.shape)

    # Move agents based on pheromone and idleness
    def compute_move_agents(self) -> list[tuple[int, int]]:
        """Move each agent to a neighboring cell using pheromone and idleness cues.

        Policy:
            - With small probability (5%), explore randomly.
            - Otherwise, select neighbor probabilistically based on:
              (pheromone^alpha) * (idleness^beta), excluding short-term tabu list.
        
        Returns:
            The new positions of the agents after movement.
        """
        new_positions = []

        # Compute new positions for each agent
        for i, (x, y) in enumerate(self.agents):
            # With small probability, explore randomly
            if random.random() < 0.05:
                neighbors = [
                    (x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                ]

                if neighbors:
                    new_pos = random.choice(neighbors)
                    new_positions.append(new_pos)
                    self.tabu_lists[i].append(new_pos)

                    # Safe-guard tabu list length
                    if len(self.tabu_lists[i]) > 5:
                        self.tabu_lists[i].pop(0)
                else:
                    new_positions.append((x, y))
                continue

            neighbors = [
                (x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            ]

            # Exclude short-term tabu for move proposal only
            valid_neighbors = [n for n in neighbors if n not in self.tabu_lists[i]]
            if not valid_neighbors:
                valid_neighbors = neighbors

            probs = []
            for nx, ny in valid_neighbors:
                # Safeguard against out-of-bounds
                try:
                    idln = self.idleness[nx, ny]
                    phero = self.pheromone[nx, ny]
                except IndexError:
                    probs.append(0)
                    continue

                pheromone_effect = phero ** self.alpha
                idleness_effect = (idln + 1) ** self.beta
                probs.append(pheromone_effect * idleness_effect)

            total_prob = sum(probs)
            if total_prob == 0:
                probs = [1 / len(probs)] * len(probs)
            else:
                probs = [p / total_prob for p in probs]

            new_pos = random.choices(valid_neighbors, weights=probs, k=1)[0]
            new_positions.append(new_pos)

        return new_positions

    # New method to run a single step of the ACO algorithm
    def run_step(self) -> None:
        """Run a single ACO step.

        Sequence:
        1. Propose moves (no side-effects) via `move_agents()`
        2. Call `super().run_step(proposed_moves)` which increases idleness,
           handles events, updates statistics and resolves conflicts setting
           `self.agents` to the final positions.
        3. Apply pheromone updates and side-effects via `update_pheromone()`.
        """
        proposed = self.compute_move_agents()
        new_positions = super().run_step(proposed)

        self.update_pheromone(new_positions)