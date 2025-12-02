from __future__ import annotations

import pygame
import time
from typing import Optional, Callable

import numpy as np

from ui.components.utils import viz_utils
from ui.routes.Simulation.visualization import Visualization
from maps.MapLoader import MapLoader
from algorithm import Heuristic, AntColony  # default; user can extend later
from ui.config import sim_config

from ui.routes.base import Page


class SimPage(Page):
    """Simulation page embedding the existing Visualization UI."""

    def __init__(
        self,
        go_home: Callable[[], None],
        go_stats: Callable[[dict], None] | None = None,
    ):
        self.utils = viz_utils()
        self.go_home = go_home
        self.go_stats = go_stats
        self.viz: Visualization | None = None
        self.algorithm = None
        # Accumulateur de temps simulé pour déclencher les steps à 1 Hz simulé
        self._sim_accum: float = 0.0

    def on_enter(self, prev: Optional[str] = None) -> None:
        screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        # Load default map
        loader = MapLoader()
        MAP = loader.load(sim_config.map_name)
        PNG_MAP = loader.load_png(sim_config.map_name)
        offset_x,offset_y,nbr_rows,nbr_cols,map_scale = loader.load_parameters(sim_config.map_name)
        self.viz = Visualization(screen.get_size(), MAP, PNG_MAP, offset_x,offset_y,nbr_rows,nbr_cols,map_scale,self.go_home)

        # Perform any finalization when simulation ends
        def _finish():
            if not (self.viz and self.algorithm):
                return
            results = {
                "algorithm_name": type(self.algorithm).__name__,
                "steps": int(getattr(self.algorithm, "step_count", 0)),
                "average_idleness_history": list(
                    getattr(self.algorithm, "average_idleness_history", [])
                ),
                "maximum_idleness_history": list(
                    getattr(self.algorithm, "maximum_idleness_history", [])
                ),
                "coverage_by_agent": list(
                    getattr(self.algorithm, "coverage_by_agent", [])
                ),
                "agent_work_history": list(
                    getattr(self.algorithm, "agentswork_history", [])
                ),
                "coverage_by_agent_history": list(
                    getattr(self.algorithm, "coverage_by_agent_history", [])
                ),
                "total_coverage_history": list(
                    getattr(self.algorithm, "total_coverage_history", [])
                ),
                "event_count": int(len(getattr(self.algorithm, "event_history", []))),
                "map_shape": (
                    tuple(self.algorithm.map.shape)
                    if hasattr(self.algorithm, "map")
                    else (0, 0)
                ),
            }
            if callable(self.go_stats):
                self.go_stats(results)

        self.viz.on_finish = _finish
        # Algorithm from settings
        algo_name = sim_config.algorithm
        num_agents = int(sim_config.num_agents)
        spawn_prob = float(sim_config.spawn_prob)
        if algo_name == "AntColony":
            p = sim_config.algo_params.get("AntColony", {})
            self.algorithm = AntColony(
                MAP,
                num_agents,
                evaporation_rate=float(p.get("evaporation_rate", 0.1)),
                alpha=float(p.get("alpha", 1.0)),
                beta=float(p.get("beta", 2.0)),
                event_spawn_prob=spawn_prob,
                iddleness_growth=float(sim_config.iddleness_growth),
            )
        else:
            self.algorithm = Heuristic(MAP, num_agents, event_spawn_prob=spawn_prob)

        self._sim_accum = 0.0

    def on_exit(self, next: Optional[str] = None) -> None:
        # Let Visualization clean up Pygame subsystems only when quitting whole app
        # Here we just drop references; router controls the main window.
        self.viz = None
        self.algorithm = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_home
            return
        if self.viz and self.algorithm:
            # forward UI events to existing Visualization for speed/reset/quit etc.
            self.viz.buttons_event(event, self.algorithm)

    def update(self, dt: float) -> None:
        if not (self.viz and self.algorithm):
            return
        # Appliquer seulement le multiplicateur UI sur le temps réel
        # x1.0 => secondes simulées ~= secondes réelles
        sim_dt = dt * float(self.viz.speed_multiplier)
        self._sim_accum += sim_dt
        # Exécuter un step par seconde simulée écoulée
        while self._sim_accum >= 1.0:
            self.algorithm.run_step()
            self.viz.advance_sim_time_per_tick()
            self._sim_accum -= 1.0

    def render(self, screen: pygame.Surface) -> None:
        if not (self.viz and self.algorithm):
            return
        # Visualization renders onto its own screen surface; ensure same reference
        self.viz.screen = screen
        self.viz.update_visuals(self.algorithm)

