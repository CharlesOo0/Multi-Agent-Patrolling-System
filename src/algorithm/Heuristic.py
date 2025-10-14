from typing import Tuple
import numpy as np
from algorithm import Algorithm

class Heuristic(Algorithm):
    """
    A simple heuristic-based multi-agent patrolling algorithm.
    This class implements a basic heuristic approach for agent movement and patrolling.
    """
    def __init__(self, map: np.ndarray, num_agents: int):
        super().__init__(map, num_agents)
        self.clusters = self._map_clustering()


    def _map_clustering(self):
        """
        Implement a simple clustering heuristic for agent movement.
        This is a placeholder for the actual heuristic logic.
        """
        # Cluster the map into regions and assign agents to clusters
        clusters = []
        cluster_size = (self.map.shape[0] // self.num_agents, self.map.shape[1] // self.num_agents)
        
        for i in range(self.num_agents):
            cluster = (i * cluster_size[0], i * cluster_size[1], cluster_size[0], cluster_size[1])
            clusters.append(cluster)

        return clusters

    def move_agents(self):
        """
        Move agents based on the clustering heuristic.
        This is a placeholder for the actual movement logic.
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
        """
        Execute one step of the heuristic algorithm.
        This method must be implemented by the heuristic algorithm.
        """
        super().run_step()
        self.move_agents()