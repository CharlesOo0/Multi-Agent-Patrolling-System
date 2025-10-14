from abc import ABC, abstractmethod
import numpy as np
import random
from typing import List, Tuple

class Algorithm(ABC):
    """
    Abstract base class for multi-agent patrolling algorithms.
    Defines the common interface and shared functionality for all patrolling algorithms.
    """

    def __init__(self, map: np.ndarray, num_agents: int, **kwargs):
        """
        Initialize the algorithm with basic parameters.
        
        Args:
            map: 2D numpy array representing the patrol area
            num_agents: Number of agents in the system
            **kwargs: Additional algorithm-specific parameters
        """
        self.map = map
        self.num_agents = num_agents
        self.width, self.height = map.shape
        self.idleness = np.zeros((self.width, self.height))

        # Initialize agent positions
        self.agents = self._initialize_agent_positions()
        
        # Tracking variables
        self.step_count = 0
        self.total_coverage = 0.0
        self.visited_cells = set()
    
    @abstractmethod
    def run_step(self) -> None:
        """
        Execute one step of the algorithm.
        This method must be implemented by each specific algorithm.
        """
        # Update idleness for all cells
        self.idleness += 0.1
        self.step_count += 1
    
    def _initialize_agent_positions(self) -> List[Tuple[int, int]]:
        """
        Randomly initialize agent positions within the map boundaries.
        
        Returns:
            List of tuples representing initial positions of agents.
        """
        # Check if there are enough cells for all agents
        if self.num_agents > self.width * self.height:
            # Fallback: reduce agents to fit in the grid
            self.num_agents = self.width * self.height
            print(f"Warning: Reduced number of agents to {self.num_agents} to fit in the grid.")

        positions = []

        for _ in range(self.num_agents):
            # Make sure agents dont start on the same cell
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if (x, y) not in positions:
                    positions.append((x, y))
                    break

        return positions     