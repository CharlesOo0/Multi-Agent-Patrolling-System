import numpy as np
import random
from .Algorithm import Algorithm
from typing import List, Tuple


class AntColonyLecture(Algorithm):
    """Simplified Ant Colony Optimization for multi-agent patrolling.

    In this corrected version, agents no longer avoid walls, limits, or
    other agents when computing their movement. They may propose invalid
    positions and the environment (run_step from the parent class) is
    responsible for resolving collisions and constraints.
    """

    def __init__(
        self,
        map: np.ndarray,
        num_agents: int,
        alpha: float = 1,
        beta: float = 2,
        exploration_rate: float = 0.15,
        tabu_length: int = 15,
        rho: float = 0.1,
        Q: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(map, num_agents, **kwargs)
        self.alpha = alpha
        self.beta = beta
        self.exploration_rate = exploration_rate
        self.tabu_length = tabu_length
        self.rho = rho
        self.Q = Q

        # Pheromone on map cells
        self.pheromone = np.ones(map.shape)

        # One tabu list per agent
        self.tabu = [[] for _ in range(num_agents)]

    def visibility(self, x: int, y: int) -> float:
        """Heuristic desirability η for cell (x, y).

        Handles out-of-bound indices by returning a neutral constant.
        """
        if self.in_bounds(x, y):
            return self.idleness[x, y] + 1
        return 1.0  # Neutral heuristic if out of bounds

    def compute_transition_probabilities(
        self, agent_index: int, pos: Tuple[int, int]
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        """Return neighbor list and corresponding transition probabilities.

        This version no longer filters walls, agents, or map boundaries.
        All four cardinal directions are always allowed.
        """

        x, y = pos

        # Raw neighbors without ANY filtering
        neighbors = [
            (x + dx, y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        ]

        # Short-term tabu forbids recently visited cells
        allowed = [n for n in neighbors if n not in self.tabu[agent_index]]
        if not allowed:
            allowed = neighbors

        scores: List[float] = []
        for nx, ny in allowed:
            if self.in_bounds(nx, ny):
                tau = self.pheromone[nx, ny]
                eta = self.visibility(nx, ny)
            else:
                # Neutral values out of bounds
                tau = 1
                eta = 1

            scores.append((tau ** self.alpha) * (eta ** self.beta))

        total = sum(scores)
        if total == 0:
            probs = [1 / len(scores)] * len(scores)
        else:
            probs = [s / total for s in scores]

        return allowed, probs

    def compute_move_agents(self) -> List[Tuple[int, int]]:
        """Propose moves for each agent.

        This corrected version does NOT check walls, map limits, or collisions.
        """

        new_positions: List[Tuple[int, int]] = []

        for i, pos in enumerate(self.agents):

            # Random exploration step
            if random.random() < self.exploration_rate:
                neighbors = [
                    (pos[0] + dx, pos[1] + dy)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                ]
                new_pos = random.choice(neighbors)

            else:
                # ACO-directed movement
                allowed, probs = self.compute_transition_probabilities(i, pos)
                new_pos = random.choices(allowed, weights=probs, k=1)[0]

            # Update tabu list
            self.tabu[i].append(new_pos)
            if len(self.tabu[i]) > self.tabu_length:
                self.tabu[i].pop(0)

            new_positions.append(new_pos)

        return new_positions

    def update_pheromone(self, new_positions: List[Tuple[int, int]]) -> None:
        """Evaporate and reinforce pheromone.

        Reinforcement only applies on valid map cells.
        """

        # Evaporation
        self.pheromone = (1 - self.rho) * self.pheromone

        # Reinforcement
        for x, y in new_positions:
            if self.in_bounds(x, y):
                Lk = max(1, self.idleness[x, y])
                delta = self.Q / Lk
                self.pheromone[x, y] += delta

    def run_step(self) -> None:
        """Run one full step of the simulation."""
        proposed = self.compute_move_agents()
        final_positions = super().run_step(proposed)
        self.update_pheromone(final_positions)
