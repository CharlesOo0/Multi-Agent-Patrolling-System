"""Heuristic multi-agent patrolling utilities.

This module implements a lightweight heuristic patrolling algorithm that:
- partitions the free space into connected clusters (one per agent),
- assigns an initial seed to each agent using farthest-point sampling, and
- at each step proposes a greedy move towards the neighboring cell with the
  highest "idleness" value (preference is given to move inside the agent's
  assigned cluster).

The implementation is intentionally simple and intended to be used as a
baseline or fallback strategy. It does not perform advanced collision
resolution or coordinated planning; those are expected to be handled by the
simulation environment or a higher-level controller.
"""

from typing import Tuple, List
import numpy as np
from algorithm import Algorithm
from collections import deque
import random


class Heuristic(Algorithm):
    """Simple heuristic-based multi-agent patrolling algorithm.

    The heuristic partitions the map into connected clusters and assigns each
    agent to the cluster that contains its seed. During execution each agent
    greedily selects among its 4-neighbors (or stays) the cell with maximum
    recorded idleness. Cluster membership is used as a preference to keep
    agents covering different regions.

    Parameters
    ----------
    map : np.ndarray
        2D grid with values where 0 denotes free cell and non-zero denotes an
        obstacle.
    num_agents : int
        Number of agents to manage.
    **kwargs
        Additional keyword arguments are forwarded to the base `Algorithm`
        initializer.
    """

    def __init__(self, map: np.ndarray, num_agents: int, **kwargs):
        """Initialize state and precompute clusters.

        The constructor computes a clustering of the free cells and stores an
        initial agent position per cluster (the first cell of each cluster).
        The cluster assignment uses multi-source BFS starting from well-spaced
        seeds chosen by farthest-point sampling.
        """
        super().__init__(map, num_agents, **kwargs)
        # Partition free cells into connected clusters and assign seeds
        self.clusters = self._map_clustering()

        # Log basic cluster assignment (helpful for debugging)
        for cluster, agent_idx in zip(self.clusters, range(self.num_agents)):
            print(f"Agent {agent_idx} assigned to cluster with {len(cluster)} cells.")
            print(cluster)

        # Initialize agent positions: pick one representative cell per cluster
        self.agents = [cluster[0] for cluster in self.clusters if cluster]

    def _get_free_cells(self, map_: np.ndarray) -> List[Tuple[int, int]]:
        """Return a list of (row, col) coordinates for free cells.

        A free cell is defined by the map value equal to zero.
        """
        xs, ys = np.where(map_ == 0)
        return list(zip(xs, ys))

    def _choose_seeds_farthest(self, map_: np.ndarray, num_agents: int) -> List[Tuple[int, int]]:
        """Select `num_agents` seed cells using farthest-point sampling.

        Starting with a random free cell, the method iteratively selects the
        free cell that maximizes the minimum squared Euclidean distance to the
        already chosen seeds. The returned seeds are coordinates in (row, col)
        order.

        Raises
        ------
        ValueError
            If there are fewer free cells than agents.
        """
        free_cells = self._get_free_cells(map_)
        if len(free_cells) < num_agents:
            raise ValueError("Not enough free cells to place one seed per agent.")

        coords = np.array(free_cells)  # shape (N, 2)

        # Pick the first seed at random to break symmetry
        first_idx = random.randint(0, len(free_cells) - 1)
        seeds = [free_cells[first_idx]]

        # Iteratively select the point farthest (in min-distance sense) from
        # existing seeds.
        for _ in range(1, num_agents):
            seed_arr = np.array(seeds)  # shape (k, 2)
            # Vectorized squared distances from every free cell to every seed
            diff = coords[:, None, :] - seed_arr[None, :, :]
            dist2 = np.sum(diff**2, axis=2)  # (N, k)
            min_dist2 = dist2.min(axis=1)

            # Remove coordinates that are already selected as seeds
            for s in seeds:
                mask = np.logical_not((coords[:, 0] == s[0]) & (coords[:, 1] == s[1]))
                coords = coords[mask]
                min_dist2 = min_dist2[mask]

            best_idx = int(np.argmax(min_dist2))
            seeds.append((int(coords[best_idx, 0]), int(coords[best_idx, 1])))

        return seeds

    def _map_clustering(self) -> list[list[Tuple[int, int]]]:
        """Partition the free space into connected clusters, one per agent.

        The algorithm:
        1. Chooses `num_agents` seeds via `_choose_seeds_farthest`.
        2. Performs a multi-source BFS from seeds to assign each reachable free
           cell to the nearest seed (in BFS order), producing connected
           clusters under 4-connectivity (up/down/left/right).

        Returns
        -------
        list[list[tuple[int,int]]]
            A list of clusters where each cluster is a list of (row, col)
            coordinates. If the map has fewer free cells than agents, a
            ValueError is raised.
        """
        free_cells = self._get_free_cells(self.map)
        num_free = len(free_cells)

        if num_free == 0:
            return [[] for _ in range(self.num_agents)]

        if num_free < self.num_agents:
            raise ValueError("Number of agents exceeds number of free cells.")

        # Select seeds that are well spaced across the free space
        seeds = self._choose_seeds_farthest(self.map, self.num_agents)

        h, w = self.map.shape
        owner = -np.ones((h, w), dtype=int)  # -1 indicates unassigned
        q = deque()

        # Initialize BFS queue with seeds and mark their ownership
        for agent_idx, (x, y) in enumerate(seeds):
            owner[x, y] = agent_idx
            q.append((x, y, agent_idx))

        # 4-neighborhood directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while q:
            x, y, agent_idx = q.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # Check bounds, free cell and not yet assigned
                if 0 <= nx < h and 0 <= ny < w:
                    if self.map[nx, ny] == 0 and owner[nx, ny] == -1:
                        owner[nx, ny] = agent_idx
                        q.append((nx, ny, agent_idx))

        # Build clusters from owner map
        clusters: list[list[Tuple[int, int]]] = [[] for _ in range(self.num_agents)]
        xs, ys = np.where(owner != -1)
        for x, y in zip(xs, ys):
            clusters[owner[x, y]].append((int(x), int(y)))

        return clusters

    def _pick_best(self, coords: Tuple[int, int], cands: list[tuple[int, int]]) -> tuple[int, int]:
        """Return the candidate with maximum idleness among `cands`.

        If a candidate is out of bounds (IndexError), it is skipped. If no
        valid candidate is found the method falls back to a random choice from
        the provided list (this situation should be rare in correct maps).
        """
        max_idleness = -1
        best = coords
        for nx, ny in cands:
            try:
                val = self.idleness[nx, ny]
            except IndexError:
                # Skip candidates outside the idleness array bounds
                continue
            if val > max_idleness:
                max_idleness = val
                best = (nx, ny)

        if max_idleness < 0:
            # No in-bounds candidate found; choose randomly as a last resort
            return random.choice(cands)
        return best

    def compute_move_agents(self) -> list[tuple[int, int]]:
        """Compute proposed moves for each agent.

        For every agent the method considers its 4-neighbors and the current
        cell (staying). It first prefers cells that belong to the agent's
        cluster; if none exist among the immediate neighbors, it selects
        among all neighbors the cell with maximum idleness.

        Returns
        -------
        list[tuple[int,int]]
            Proposed (row, col) position for each agent in order.
        """
        new_positions: list[tuple[int, int]] = []

        for i, (x, y) in enumerate(self.agents):
            # 4-neighborhood plus current position (allow staying still)
            neighbors = [(x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
            candidates = neighbors + [(x, y)]

            cluster = self.clusters[i] if i < len(self.clusters) else []

            # Prefer candidates inside the agent's assigned cluster
            cluster_candidates = [c for c in candidates if c in cluster]

            if cluster_candidates:
                chosen = self._pick_best((x, y), cluster_candidates)
            else:
                chosen = self._pick_best((x, y), candidates)

            new_positions.append(chosen)

        return new_positions

    def run_step(self) -> None:
        """Perform a simulation step.

        The method computes proposed moves (via `compute_move_agents`) and
        forwards them to the base class `run_step` which is expected to handle
        updates such as movement application, collision resolution and
        idleness bookkeeping.
        """
        new_pos = self.compute_move_agents()
        super().run_step(new_pos)