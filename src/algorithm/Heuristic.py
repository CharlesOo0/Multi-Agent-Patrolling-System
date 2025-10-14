from typing import Tuple
import numpy as np
from algorithm import Algorithm

class Heuristic(Algorithm):
    """Simple heuristic-based multi-agent patrolling algorithm.

    Agents greedily select an adjacent cell with the highest idleness within the
    valid neighborhood, avoiding obstacles.
    """
    def __init__(self, map: np.ndarray, num_agents: int):
        """Initialize the heuristic algorithm and precompute clusters.

        Args:
            map: 2D numpy array where 0=free cell and 1=obstacle.
            num_agents: Number of patrolling agents.
        """
        super().__init__(map, num_agents)
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

    def move_agents(self):
        """Move each agent to the adjacent cell with the highest idleness.

        The move respects map bounds and obstacles. Idleness at the chosen cell is reset.
        """
        # Make each agent move to the adjacent biggest idleness cell in their cluster and not out of it
        for i, (x, y) in enumerate(self.agents):
            # Get the cluster boundaries
            neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
            neighbors = [(nx, ny) for nx, ny in neighbors
                         if 0 <= nx < self.map.shape[0] and 0 <= ny < self.map.shape[1] and self.map[nx, ny] == 0]

            if not neighbors:
                continue

            max_idleness = -1
            best_pos = (x, y)
            for nx, ny in neighbors:
                if self.idleness[nx, ny] > max_idleness:
                    max_idleness = self.idleness[nx, ny]
                    best_pos = (nx, ny)

            self.agents[i] = best_pos
            self.idleness[best_pos] = 0

    def run_step(self) -> None:
        """Run one step: update idleness, then move agents using the heuristic."""
        super().run_step()
        self.move_agents()