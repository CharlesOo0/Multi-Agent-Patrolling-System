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
                - event_spawn_prob: Probability of spawning an event each step (default 0.10).

        """
        self.map = map
        self.num_agents = num_agents
        self.width, self.height = map.shape
        self.idleness = np.zeros((self.width, self.height))

        # Initialize agent positions
        self.agents = self._initialize_agent_positions()

        # Simulation speed and events configuration
        self.base_event_spawn_prob: float = float(kwargs.get("event_spawn_prob", 1))
        self.idleness_growth: float = float(kwargs.get("iddleness_growth", 0.01))

        # Events manager (CS:GO-like) to influence idleness each step
        # Scale spawn probability inverse to simulation speed so real-time rate stays stable
        self.events = EventManager(spawn_prob=self.base_event_spawn_prob)

        # Tracking variables
        self.step_count = 0
        self.total_coverage_history: List[float] = []
        self.visited_cells = set()
        self.coverage_by_agent_history: List[List[float]] = [
            [] for _ in range(self.num_agents)
        ]
        self.average_idleness_history: List[float] = []
        self.maximum_idleness_history: List[float] = []
        self.agentswork_history: List[List[float]] = [
            [] for _ in range(self.num_agents)
        ]

        # History for visualization logs panel
        self.event_history: List[dict] = []

    def _run_event_step(self) -> None:
        """Handle event spawning and apply their effects on idleness."""
        spawned = self.events.maybe_spawn_event(self.map)
        if spawned is not None:
            # Log event with metadata
            self.event_history.append(
                {
                    "step": self.step_count,
                    "type": spawned.type,
                    "position": spawned.position,
                    "magnitude": float(spawned.magnitude),
                    "radius": int(spawned.radius),
                    "ttl": int(spawned.ttl),
                }
            )
        self.events.apply_events(self.idleness)

    def _update_statistics(self) -> None:
        """
        Update all the statistics tracked by the algorithm.
        This includes total coverage, average idleness, and per-agent coverage history.
        """
        for agent_pos in self.agents:
            self.visited_cells.add(agent_pos)

        total_free_cells = np.sum(self.map == 0)
        visited_cells_count = len(self.visited_cells)
        print(visited_cells_count, total_free_cells)
        self.total_coverage_history.append(
            visited_cells_count / total_free_cells if total_free_cells > 0 else 0.0
        )

        # Convert visited set to a list for deterministic enumeration and assign
        # visited cells to agents in a round-robin fashion to compute per-agent metrics.
        visited_list = list(self.visited_cells)

        for i in range(self.num_agents):
            agent_visited = {
                pos
                for idx, pos in enumerate(visited_list)
                if idx % self.num_agents == i
            }
            coverage = (
                len(agent_visited) / total_free_cells if total_free_cells > 0 else 0.0
            )
            self.coverage_by_agent_history[i].append(coverage)

        for i in range(self.num_agents):
            # Sum idleness of the visited cells assigned to this agent this step
            current_sum = sum(
                float(self.idleness[pos])
                for idx, pos in enumerate(visited_list)
                if idx % self.num_agents == i
            )
            # Accumulate on top of the previous cumulative value (or start at 0.0)
            prev_cumulative = (
                self.agentswork_history[i][-1] if self.agentswork_history[i] else 0.0
            )
            self.agentswork_history[i].append(prev_cumulative + current_sum)

        average_idleness = np.mean(
            self.idleness[self.map == 0]
        )  # Only consider free cells
        self.average_idleness_history.append(average_idleness)
        maximum_idleness = np.max(
            self.idleness[self.map == 0]
        )  # Only consider free cells
        self.maximum_idleness_history.append(maximum_idleness)

        # Print latest per-agent coverage values (None if agent has no history)
        coverage_last = [
            hist[-1] if hist else None for hist in self.coverage_by_agent_history
        ]
        print(
            f"Step {self.step_count}:, Avg Idleness={average_idleness:.3f}, Max Idleness={maximum_idleness:.3f}, coverage_by_agent={coverage_last}"
        )
        # Print last value of each agent's work history (None if empty)
        last_values = [hist[-1] if hist else None for hist in self.agentswork_history]
        print(f"Agents' last work values: {last_values}")

    @abstractmethod
    def run_step(self) -> None:
        """Execute one step, increasing idleness and step count.

        Subclasses should call 'super().run_step()' first, then apply their
        movement/coordination logic and any additional state updates.
        """
        # Update idleness for all cells
        self.idleness += self.idleness_growth
        self.step_count += 1

        # Apply events effects
        self._run_event_step()
        # Update statistics
        self._update_statistics()

    def reset(self) -> None:
        """Reset algorithm internal state for a fresh run (used by UI Reset)."""
        self.idleness = np.zeros((self.width, self.height))
        self.agents = self._initialize_agent_positions()
        # Recreate EventManager with spawn prob matching current simulation speed
        self.events = EventManager(spawn_prob=self.base_event_spawn_prob)
        self.step_count = 0
        self.total_coverage_history = []
        self.coverage_by_agent_history = [[] for _ in range(self.num_agents)]
        self.average_idleness_history = []
        self.maximum_idleness_history = []
        self.agentswork_history = [[] for _ in range(self.num_agents)]
        self.visited_cells.clear()
        self.event_history.clear()

    def _initialize_agent_positions(self) -> List[Tuple[int, int]]:
        """Randomly initialize unique agent positions on free cells within bounds.

        Returns:
            List of (x, y) tuples representing initial positions of agents.
        """
        # Check if there are enough cells for all agents
        if self.num_agents > self.width * self.height:
            # Fallback: reduce agents to fit in the grid
            self.num_agents = self.width * self.height
            print(
                f"Warning: Reduced number of agents to {self.num_agents} to fit in the grid."
            )

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
