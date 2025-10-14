from typing import Tuple
from algorithm import Algorithm

class Heuristic(Algorithm):
    def __init__(self, map_size: Tuple[int, int], num_agents: int):
        super().__init__(map_size, num_agents)
    
    def run_step(self) -> None:
        """
        Execute one step of the heuristic algorithm.
        This method must be implemented by the heuristic algorithm.
        """
        self.update_idleness()
        # Implement heuristic logic here
        pass