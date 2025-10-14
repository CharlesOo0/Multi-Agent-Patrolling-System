from abc import ABC, abstractmethod
import numpy as np
import random
from typing import List, Tuple, Optional, Dict, Any

class Algorithm(ABC):
    """
    Abstract base class for multi-agent patrolling algorithms.
    Defines the common interface and shared functionality for all patrolling algorithms.
    """
    
    def __init__(self, map_size: Tuple[int, int], num_agents: int, **kwargs):
        """
        Initialize the algorithm with basic parameters.
        
        Args:
            map_size: Tuple representing (width, height) of the patrol area
            num_agents: Number of agents in the system
            **kwargs: Additional algorithm-specific parameters
        """
        self.map_size = map_size
        self.num_agents = num_agents
        self.width, self.height = map_size
        self.idleness = np.zeros(map_size)
        
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
        self.update_idleness()
    
    def _initialize_agent_positions(self) -> List[Tuple[int, int]]:
        """
        Randomly initialize agent positions within the map boundaries.
        
        Returns:
            List of tuples representing initial positions of agents.
        """
        positions = []
        for _ in range(self.num_agents):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            positions.append((x, y))
        return positions
    
    def update_idleness(self):
        """
        Increment the idleness of all cells in the map.
        """
        self.idleness += 0.1
        self.step_count += 1