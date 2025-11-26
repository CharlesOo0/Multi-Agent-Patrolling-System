from typing import Tuple
import numpy as np
from algorithm import Algorithm
import random

class Heuristic(Algorithm):
    """Simple heuristic-based multi-agent patrolling algorithm.

    Agents greedily select an adjacent cell with the highest idleness within the
    valid neighborhood, avoiding obstacles.
    """
    def __init__(self, map: np.ndarray, num_agents: int, **kwargs):
        """Initialize the heuristic algorithm and precompute clusters.

        Args:
            map: 2D numpy array where 0=free cell and 1=obstacle.
            num_agents: Number of patrolling agents.
        """
        super().__init__(map, num_agents, **kwargs)
        self.clusters = self._map_clustering()


    def _map_clustering(self):
        """Partition the map into coarse clusters and assign them to agents.

        Returns:
            A list of clusters described as tuples (x, y, width, height).
            Note: This is a placeholder; clusters are naive and may overlap.
        """
        # Cluster the map into regions and assign agents to clusters
        clusters = []
        cluster_size = (self.map.shape[0] // self.num_agents, self.map.shape[1] // self.num_agents)
        
        for i in range(self.num_agents):
            cluster = (i * cluster_size[0], i * cluster_size[1], cluster_size[0], cluster_size[1])
            clusters.append(cluster)

        return clusters

    def compute_move_agents(self) -> list[tuple[int, int]]:
        """Move each agent to the adjacent cell with the highest idleness.

        The move respects map bounds and obstacles. Idleness at the chosen cell is reset.

        Returns:
            The new positions of the agents after movement.
        """
        new_positions = []

        # Compute new positions for each agent sequentially but the agents can't see each others moves
        for i, (x, y) in enumerate(self.agents):
            # Get the cluster boundaries
            neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]

            max_idleness = -1
            best_pos = (x, y)
            for nx, ny in neighbors:
                # Safeguard against out-of-bounds
                try:
                    val = self.idleness[nx, ny]
                except IndexError:
                    continue

                if val > max_idleness:
                    max_idleness = val
                    best_pos = (nx, ny)

            # If no valid moves found, pick a random neighbor
            if max_idleness < 0:
                best_pos = random.choice(neighbors)

            new_positions.append(best_pos)

        return new_positions

    def run_step(self) -> None:
        """Run one step: update idleness, then move agents using the heuristic."""
        new_pos = self.compute_move_agents()
        super().run_step(new_pos)