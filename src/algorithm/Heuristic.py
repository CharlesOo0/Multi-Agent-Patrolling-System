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
import heapq
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
        # for cluster, agent_idx in zip(self.clusters, range(self.num_agents)):
            # print(f"Agent {agent_idx} assigned to cluster with {len(cluster)} cells.")
            # print(cluster)

        # Initialize agent positions: pick one representative cell per cluster
        # self.agents = [cluster[0] for cluster in self.clusters if cluster]

        # Priority offset for prioritized planning (rotates each step to avoid starvation)
        self._priority_offset = 0

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

    def _astar_to_nearest(self, start: Tuple[int, int], goals: set[tuple[int, int]]) -> list[tuple[int, int]] | None:
        """A* search from `start` to the nearest cell in `goals`.

        Returns the path as a list of coordinates from `start` to goal (inclusive),
        or `None` if no path is found. Uses Manhattan distance as heuristic.
        """
        h, w = self.map.shape

        def in_bounds(p):
            x, y = p
            return 0 <= x < h and 0 <= y < w

        # Quick check: if start already in goals
        if start in goals:
            return [start]

        # Obstacles: cells with non-zero map value
        def passable(p):
            x, y = p
            return in_bounds(p) and self.map[x, y] == 0

        open_heap = []
        gscore = {start: 0}
        fscore = {start: min(abs(start[0]-gx) + abs(start[1]-gy) for gx, gy in goals)}
        heapq.heappush(open_heap, (fscore[start], start))
        came_from = {}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current in goals:
                # reconstruct path
                path = [current]
                while path[-1] in came_from:
                    path.append(came_from[path[-1]])
                path.reverse()
                return path

            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if not passable(neighbor):
                    continue
                tentative_g = gscore[current] + 1
                if neighbor not in gscore or tentative_g < gscore[neighbor]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g
                    # heuristic: distance to closest goal
                    hval = min(abs(neighbor[0]-gx) + abs(neighbor[1]-gy) for gx, gy in goals)
                    fscore[neighbor] = tentative_g + hval
                    heapq.heappush(open_heap, (fscore[neighbor], neighbor))

        return None

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
        # First pass: compute desired moves (ignore inter-agent conflicts)
        desired: list[tuple[int, int]] = []

        for i, (x, y) in enumerate(self.agents):
            cluster = self.clusters[i] if i < len(self.clusters) else []

            # 4-neighborhood plus current position (allow staying still)
            neighbors = [(x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
            candidates = neighbors + [(x, y)]

            # Prefer immediate candidates inside the agent's assigned cluster
            cluster_candidates = [c for c in candidates if c in cluster]
            if cluster_candidates:
                chosen = self._pick_best((x, y), cluster_candidates)
                desired.append(chosen)
                continue

            # Otherwise attempt A* towards nearest cluster cell
            if cluster:
                goals = set(cluster)
                path = self._astar_to_nearest((x, y), goals)
                if path and len(path) >= 2:
                    # next step along the path
                    desired.append(path[1])
                    continue

            # Fallback: choose based on idleness among neighbors+stay
            chosen = self._pick_best((x, y), candidates)
            desired.append(chosen)

        # Second pass: prioritized planning to avoid cycles and reduce deadlocks.
        n = len(self.agents)
        final: list[tuple[int, int]] = [None] * n

        # Map of current positions to agent index for quick lookup
        pos_to_agent = {pos: idx for idx, pos in enumerate(self.agents)}

        # Reservation sets (cells and directed edges) to prevent collisions/swaps
        reserved_cells = set()
        reserved_edges = set()

        # Build processing order with rotating priority to avoid starvation
        order = list(range(n))
        if n > 0:
            offset = getattr(self, "_priority_offset", 0) % n
            order = order[offset:] + order[:offset]

        for idx in order:
            cur = self.agents[idx]
            # Candidate list: desired first, then neighbors sorted by idleness, then stay
            neigh = [(cur[0] + dx, cur[1] + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
            neighbors = [p for p in neigh if 0 <= p[0] < self.map.shape[0] and 0 <= p[1] < self.map.shape[1] and self.map[p[0], p[1]] == 0]
            # sort remaining neighbors by idleness desc
            neighbors_sorted = sorted(neighbors, key=lambda c: self.idleness[c[0], c[1]] if 0 <= c[0] < self.idleness.shape[0] and 0 <= c[1] < self.idleness.shape[1] else -1, reverse=True)
            fallback_list = neighbors_sorted + [cur]

            preferred = desired[idx]
            candidates = [preferred] + [c for c in fallback_list if c != preferred]

            chosen = None
            for cand in candidates:
                # must be in bounds and passable
                x, y = cand
                if not (0 <= x < self.map.shape[0] and 0 <= y < self.map.shape[1]):
                    continue
                if self.map[x, y] != 0:
                    continue

                # cell already reserved by higher-priority agent?
                if cand in reserved_cells:
                    continue

                # edge conflict (swap): if some earlier agent reserved edge cand->cur, disallow cur->cand
                if (cand, cur) in reserved_edges:
                    continue

                # Accept candidate
                chosen = cand
                reserved_cells.add(chosen)
                reserved_edges.add((cur, chosen))
                break

            if chosen is None:
                # No allowed move -> stay
                chosen = cur
                reserved_cells.add(chosen)
                reserved_edges.add((cur, chosen))

            final[idx] = chosen

        return final

    def run_step(self) -> None:
        """Perform a simulation step.

        The method computes proposed moves (via `compute_move_agents`) and
        forwards them to the base class `run_step` which is expected to handle
        updates such as movement application, collision resolution and
        idleness bookkeeping.
        """
        new_pos = self.compute_move_agents()
        super().run_step(new_pos)