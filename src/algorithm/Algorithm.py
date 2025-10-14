from abc import ABC, abstractmethod
import numpy as np
import random
from typing import List, Tuple
from events import EventManager

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
                - event_spawn_prob: Probability of spawning an event each step (default 0.05).
                - simulation_speed: Speed multiplier for event effects (default 1.0).

        """
        self.map = map
        self.num_agents = num_agents
        self.width, self.height = map.shape
        self.idleness = np.zeros((self.width, self.height))

        # Initialize agent positions
        self.agents = self._initialize_agent_positions()
        
        # Simulation speed and events configuration
        self.simulation_speed: float = float(kwargs.get("simulation_speed", 1.0))
        self.base_event_spawn_prob: float = float(kwargs.get("event_spawn_prob", 0.05))

        # Events manager (CS:GO-like) to influence idleness each step
        # Scale spawn probability inverse to simulation speed so real-time rate stays stable
        self.events = EventManager(
            spawn_prob=self.base_event_spawn_prob / max(self.simulation_speed, 0.1)
        )
        
        # Tracking variables
        self.step_count = 0
        self.total_coverage = 0.0
        self.visited_cells = set()

        # History for visualization logs panel
        self.event_history: List[dict] = []

    def _run_event_step(self) -> None:
        """Handle event spawning and apply their effects on idleness."""
        spawned = self.events.maybe_spawn_event(self.map)
        if spawned is not None:
            # Log event with metadata
            self.event_history.append({
                "step": self.step_count,
                "type": spawned.type,
                "position": spawned.position,
                "magnitude": float(spawned.magnitude),
                "radius": int(spawned.radius),
                "ttl": int(spawned.ttl),
            })
        self.events.apply_events(self.idleness)
    
    @abstractmethod
    def run_step(self) -> None:
        """Execute one step, increasing idleness and step count.

        Subclasses should call 'super().run_step()' first, then apply their
        movement/coordination logic and any additional state updates.
        """
        # Update idleness for all cells
        self.idleness += 0.1
        self.step_count += 1
        
        # Apply events effects
        self._run_event_step()

    def reset(self) -> None:
        """Reset algorithm internal state for a fresh run (used by UI Reset)."""
        self.idleness = np.zeros((self.width, self.height))
        self.agents = self._initialize_agent_positions()
        # Recreate EventManager with spawn prob matching current simulation speed
        self.events = EventManager(
            spawn_prob=self.base_event_spawn_prob / max(self.simulation_speed, 0.1)
        )
        self.step_count = 0
        self.total_coverage = 0.0
        self.visited_cells.clear()
        self.event_history.clear()
    
    def set_simulation_speed(self, speed: float) -> None:
        """Update simulation speed and adjust event spawn rate accordingly.

        Args:
            speed: Desired ticks per second (>0). Values are clamped to [0.1, +inf).
        """
        self.simulation_speed = max(0.1, float(speed))
        # Keep roughly constant events per real second by inversely scaling per-tick prob
        self.events.spawn_prob = self.base_event_spawn_prob / self.simulation_speed

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