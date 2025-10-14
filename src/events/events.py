from __future__ import annotations

import enum
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np


class EventType(enum.Enum):
    """Types of CS:GO-like events that can influence idleness.

    - BOMB_PLANTED: Increase urgency in a local area (idleness drops strongly).
    - ALLY_DOWN: Increase urgency moderately near the incident.
    - ENEMY_DOWN: Slightly reduce urgency (idleness) around the event.
    """

    BOMB_PLANTED = "bomb_planted"
    ALLY_DOWN = "ally_down"
    ENEMY_DOWN = "enemy_down"


@dataclass
class Event:
    """An event occurring at a free cell location that affects idleness.

    Attributes:
        type: The type of the event.
        position: (x, y) location on the grid where event occurs.
        radius: Manhattan radius of influence for this event.
        magnitude: A signed value to add to idleness (negative lowers idleness).
        ttl: Number of steps the event remains active (>=1). Each step decrements.
    """

    type: EventType
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


class EventManager:
    """Generate and manage random events on free cells and apply effects.

    Usage pattern:
        - Call maybe_spawn_event(map) each algorithm step to stochastically add an event.
        - Call apply_events(idleness) to apply cumulative effects to the idleness grid.
        - Events have limited TTL and will be removed when expired.
    """

    def __init__(self,
                 spawn_prob: float = 0.05,
                 bomb_cfg: Optional[Dict] = None,
                 ally_cfg: Optional[Dict] = None,
                 enemy_cfg: Optional[Dict] = None) -> None:
        self.spawn_prob = spawn_prob
        self.active: List[Event] = []

        # Default configurations per event type
        self.bomb_cfg = bomb_cfg or {"radius": 4, "magnitude": 5.0, "ttl": 10}
        self.ally_cfg = ally_cfg or {"radius": 3, "magnitude": 3.0, "ttl": 6}
        self.enemy_cfg = enemy_cfg or {"radius": 2, "magnitude": -1.5, "ttl": 4}

    def _random_free_cell(self, map_arr: np.ndarray) -> Optional[Tuple[int, int]]:
        """Return a random free-cell coordinate (x, y), or None if none exist."""
        xs, ys = map_arr.shape
        free_cells = [(x, y) for x in range(xs) for y in range(ys) if map_arr[x, y] == 0]
        if not free_cells:
            return None
        return random.choice(free_cells)

    def maybe_spawn_event(self, map_arr: np.ndarray) -> Optional[Event]:
        """Stochastically spawn a new event on a random free cell.

        Args:
            map_arr: 2D numpy map where 0=free and 1=obstacle.

        Returns:
            The created Event or None if no event spawned.
        """
        if random.random() > self.spawn_prob:
            return None

        pos = self._random_free_cell(map_arr)
        if pos is None:
            return None

        etype = random.choices(
            [EventType.BOMB_PLANTED, EventType.ALLY_DOWN, EventType.ENEMY_DOWN],
            weights=[0.2, 0.4, 0.4],
            k=1,
        )[0]

        if etype is EventType.BOMB_PLANTED:
            cfg = self.bomb_cfg
        elif etype is EventType.ALLY_DOWN:
            cfg = self.ally_cfg
        else:
            cfg = self.enemy_cfg

        ev = Event(
            type=etype,
            position=pos,
            radius=int(cfg.get("radius", 3)),
            magnitude=float(cfg.get("magnitude", -2.0)),
            ttl=int(cfg.get("ttl", 5)),
        )
        self.active.append(ev)
        return ev

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
