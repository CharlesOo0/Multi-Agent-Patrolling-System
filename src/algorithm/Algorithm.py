from abc import ABC, abstractmethod
import numpy as np
import random
from typing import List, Tuple

class Algorithm(ABC):
    """Abstract base class for multi-agent patrolling algorithms.

    Provides shared state such as the map, agent positions, and idleness grid,
    along with a template method 'run_step' that increments idleness each step.
    Subclasses must implement their movement/update logic in 'run_step'.
    """

    def __init__(self, map: np.ndarray, num_agents: int, **kwargs):
        """Initialize the base algorithm with common state.

        Args:
            map: 2D numpy array representing the patrol area (0=free, 1=obstacle).
            num_agents: Number of agents in the system.
            **kwargs: Additional algorithm-specific parameters (ignored by base).
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
        """Execute one step, increasing idleness and step count.

        Subclasses should call 'super().run_step()' first, then apply their
        movement/coordination logic and any additional state updates.
        """
        # Update idleness for all cells
        self.idleness += 0.1
        self.step_count += 1
    
    def _initialize_agent_positions(self) -> List[Tuple[int, int]]:
        """Randomly initialize unique agent positions on free cells within bounds.

        Returns:
            List of (x, y) tuples representing initial positions of agents.
        """
        # Check if there are enough cells for all agents
        if self.num_agents > self.width * self.height:
            # Fallback: reduce agents to fit in the grid
            self.num_agents = self.width * self.height
            print(f"Warning: Reduced number of agents to {self.num_agents} to fit in the grid.")

        positions = []

        for _ in range(self.num_agents):
            # Make sure agents dont start on the same cell or on an obstacle
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if (x, y) not in positions and self.map[x, y] == 0:
                    positions.append((x, y))
                    break

        return positions     