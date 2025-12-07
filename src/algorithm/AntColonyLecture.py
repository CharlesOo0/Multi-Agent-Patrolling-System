"""Lightweight Ant Colony variant used for lecture/demo purposes.

This module provides `AntColonyLecture`, a simplified ACO-like patrolling
algorithm that biases agents towards high-idleness cells using a
pheromone-like matrix. The implementation is intentionally didactic and
mirrors the public method structure used by other algorithms in the
project (e.g. `compute_move_agents`, `update_pheromone`, `run_step`).
"""

import numpy as np
import random
from .Algorithm import Algorithm
from typing import List, Tuple


class AntColonyLecture(Algorithm):
    """Simplified Ant Colony Optimization for multi-agent patrolling.

    Agents move stochastically according to a combination of pheromone
    intensity and a heuristic visibility (here: cell idleness). A small
    exploration probability forces occasional random moves. Pheromones
    evaporate and are reinforced at visited cells.
    """

    TABU_LENGTH = 15
    EXPLORATION_RATE = 0.15

    def __init__(
        self,
        map: np.ndarray,
        num_agents: int,
        alpha: float = 1,
        beta: float = 2,
        rho: float = 0.1,
        Q: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(map, num_agents, **kwargs)
        self.alpha = alpha
        self.beta = beta
        self.rho = rho  # evaporation rate
        self.Q = Q  # pheromone deposition constant

        # Pheromone on every free cell
        self.pheromone = np.ones(map.shape)

        # Tabu lists per agent
        self.tabu = [[] for _ in range(num_agents)]

    def visibility(self, x: int, y: int) -> float:
        """Heuristic desirability η for cell (x, y).

        Higher idleness should attract ants; add 1 to avoid zero values.
        """
        return self.idleness[x, y] + 1

    def compute_transition_probabilities(
        self, agent_index: int, pos: Tuple[int, int]
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        """Return neighbor list and corresponding transition probabilities.

        Probabilities are proportional to (pheromone^alpha) * (visibility^beta).
        Short-term tabu entries are excluded when possible.
        """
        x, y = pos

        neighbors = [
            (x + dx, y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if self.in_bounds(x + dx, y + dy) and self.map[x + dx, y + dy] == 0
        ]

        allowed = [n for n in neighbors if n not in self.tabu[agent_index]]
        if not allowed:
            allowed = neighbors

        scores: List[float] = []
        for nx, ny in allowed:
            tau = self.pheromone[nx, ny]
            eta = self.visibility(nx, ny)
            scores.append((tau ** self.alpha) * (eta ** self.beta))

        total = sum(scores)
        if total == 0:
            probs = [1 / len(scores)] * len(scores)
        else:
            probs = [s / total for s in scores]

        return allowed, probs

    def compute_move_agents(self) -> List[Tuple[int, int]]:
        """Propose moves for each agent and return the list of target cells.

        This method mirrors the name and behavior expected by the other
        algorithms in the codebase: it returns a list of proposed new
        positions (one per agent) and does not itself apply side-effects.
        """
        new_positions: List[Tuple[int, int]] = []

        for i, pos in enumerate(self.agents):
            # Exploration branch
            if random.random() < self.EXPLORATION_RATE:
                neighbors = [
                    (pos[0] + dx, pos[1] + dy)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    if self.in_bounds(pos[0] + dx, pos[1] + dy)
                    and self.map[pos[0] + dx, pos[1] + dy] == 0
                ]

                if neighbors:
                    new_pos = random.choice(neighbors)
                else:
                    new_pos = pos

                # Update tabu list (short-term memory)
                self.tabu[i].append(new_pos)
                if len(self.tabu[i]) > self.TABU_LENGTH:
                    self.tabu[i].pop(0)

                new_positions.append(new_pos)
                continue

            # ACO-based transition
            allowed, probs = self.compute_transition_probabilities(i, pos)
            new_pos = random.choices(allowed, weights=probs, k=1)[0]

            # Update tabu list
            self.tabu[i].append(new_pos)
            if len(self.tabu[i]) > self.TABU_LENGTH:
                self.tabu[i].pop(0)

            new_positions.append(new_pos)

        return new_positions

    def update_pheromone(self, new_positions: List[Tuple[int, int]]) -> None:
        """Evaporate and reinforce pheromones according to visited cells.

        Pheromone evaporation is applied first, then visited cells receive an
        increment inversely proportional to the (possibly updated)
        idleness value at the visited cell.
        """
        # Evaporation
        self.pheromone = (1 - self.rho) * self.pheromone

        # Reinforce pheromone on visited positions
        for x, y in new_positions:
            Lk = max(1, self.idleness[x, y])
            delta = self.Q / Lk
            self.pheromone[x, y] += delta

    def run_step(self) -> None:
        """Run a single simulation step.

        Sequence:
        - Propose moves with `compute_move_agents()`.
        - Forward the proposals to the base `run_step` for resolution.
        - Update pheromones with `update_pheromone()`.
        """
        proposed = self.compute_move_agents()
        final_positions = super().run_step(proposed)
        self.update_pheromone(final_positions)
