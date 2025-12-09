from __future__ import annotations

import enum
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np
import copy


@dataclass
class Event:
    """An event occurring at a free cell location that affects idleness.

    Attributes:
        name: Name of the event type.
        position: (x, y) location on the grid where event occurs.
        radius: Manhattan radius of influence for this event.
        magnitude: A signed value to add to idleness (negative lowers idleness).
        ttl: Number of steps the event remains active (>=1). Each step decrements.
    """
    name: str
    position: Tuple[int, int]
    radius: int
    magnitude: float
    ttl: int = 1

    def is_active(self) -> bool:
        """Return True if the event still has time-to-live remaining."""
        return self.ttl > 0

    def tick(self) -> None:
        """Decrease event TTL by one step."""
        self.ttl -= 1

DEFAULT_EVENTS_CONFIG: List[Event] = [
    Event(name="Bomb exploded", position=(0, 0), radius=3, magnitude=-2.0, ttl=5),
    Event(name="Ennemy spotted", position=(0, 0), radius=5, magnitude=1.5, ttl=10),
    Event(name="Ally down", position=(0, 0), radius=4, magnitude=2.0, ttl=8),
]

class EventManager:
    """Generate and manage random events on free cells and apply effects.

    Usage pattern:
        - Call maybe_spawn_event(map) each algorithm step to stochastically add an event.
        - Call apply_events(idleness) to apply cumulative effects to the idleness grid.
        - Events have limited TTL and will be removed when expired.
    """

    def __init__(
            self,
            spawn_prob: float = 0.05,
            events_config: Optional[List[Event]] = None,
            events_scenario: Optional[Dict[int, Dict]] = None,           
        ) -> None:
        print(f"spawn_prob={spawn_prob}")
        self.spawn_prob = spawn_prob
        self.active: List[Event] = []
        # Default configurations per event type (use a list copy)
        self.events = events_config if events_config is not None else list(DEFAULT_EVENTS_CONFIG)
        self.events_scenario = events_scenario if events_scenario else None

    def _random_free_cell(self, map_arr: np.ndarray) -> Optional[Tuple[int, int]]:
        """Return a random free-cell coordinate (x, y), or None if none exist."""
        xs, ys = map_arr.shape
        free_cells = [(x, y) for x in range(xs) for y in range(ys) if map_arr[x, y] == 0]
        if not free_cells:
            return None
        return random.choice(free_cells)
    
    def _is_in_bounds(self, pos: Tuple[int, int], map_arr: np.ndarray) -> bool:
        """Check if a position is within the bounds of the map array."""
        x, y = pos
        xs, ys = map_arr.shape
        return 0 <= x < xs and 0 <= y < ys

    def maybe_spawn_event(self, map_arr: np.ndarray, step: int) -> Optional[Event]:
        """Stochastically spawn a new event on a random free cell. Or follow a scenario

        Args:
            map_arr: 2D numpy map where 0=free and 1=obstacle.
            step: Current simulation step for scenario-based spawning.

        Returns:
            The created Event or None if no event spawned.
        """
        if self.events_scenario is not None:
            # If scenario provided but no event scheduled for this step, do nothing
            if str(step) not in self.events_scenario.keys():
                print(f"No event scheduled for step {step}.")
                return None

            event_info = self.events_scenario.get(str(step), None)
            if event_info is None:
                print(f"Error: Missing event info for step {step} in scenario.")
                return None

            if not self._is_in_bounds(event_info.get("position", (-1, -1)), map_arr):
                print("Error: Position out of bounds for event scenario.")
                return None

            event = Event(
                name=event_info["name"],
                position=event_info["position"],
                radius=event_info["radius"],
                magnitude=event_info["magnitude"],
                ttl=event_info["ttl"],
            )

        else:
            r = random.random()
            # print(f"random={r} spawn_prob={self.spawn_prob}")
            if  r > self.spawn_prob:
                return None

            pos = self._random_free_cell(map_arr)
            if pos is None:
                return None

            # Choose an event template and deepcopy it so we don't mutate the template
            event_template = random.choice(self.events)
            event = copy.deepcopy(event_template)
            event.position = pos
            self.active.append(event)
            
        return event

    def apply_events(self, idleness: np.ndarray) -> None:
        """Apply all active events to the idleness grid and decay their TTL.

        Effects are applied additively within the given Manhattan radius. The
        idleness value is clipped at a minimum of 0 to avoid negative values.
        """
        xs, ys = idleness.shape
        remaining: List[Event] = []
        for ev in self.active:
            if not ev.is_active():
                continue
            cx, cy = ev.position

            for x in range(max(0, cx - ev.radius), min(xs, cx + ev.radius + 1)):
                for y in range(max(0, cy - ev.radius), min(ys, cy + ev.radius + 1)):
                    if abs(x - cx) + abs(y - cy) <= ev.radius:
                        idleness[x, y] = max(0.0, idleness[x, y] + ev.magnitude)

            ev.tick()
            if ev.is_active():
                remaining.append(ev)

        # Remove expired events
        self.active = remaining
