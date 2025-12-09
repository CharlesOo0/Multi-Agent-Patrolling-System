from __future__ import annotations

import pygame
from typing import Optional, Callable

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.components.inputs import Stepper, CycleSelector
from ui.routes.base import Page
from ui.config import sim_config
from maps.MapLoader import MapLoader


class SettingsPage(Page):
    def __init__(self, go_back: Callable[[], None]):
        self.utils = viz_utils()
        self.font = pygame.font.SysFont(None, 42)
        self.small = pygame.font.SysFont(None, 26)
        self.go_back = go_back
        self._btn_back: Button | None = None
        self._ready = False
        # UI controls
        self._algo_selector: CycleSelector | None = None
        self._map_selector: CycleSelector | None = None
        self._agents_stepper: Stepper | None = None
        self._spawn_stepper: Stepper | None = None
        self._iddleness_stepper: Stepper | None = None
        # Algo-specific controls
        self._aco_evap: Stepper | None = None
        self._aco_alpha: Stepper | None = None
        self._aco_beta: Stepper | None = None
        self._aco_exploration_rate: Stepper | None = None
        self._aco_tabu_length: Stepper | None = None
        # Data
        self._map_names: list[str] = []
        # Instance
        self._instance_selector: CycleSelector | None = None

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        if self._ready:
            return
        w, h = screen.get_size()
        self._btn_back = Button(20, 20, 140, 44, "Back", self.utils.GRAY, self.utils.LIGHT_GRAY)
        # Discover maps dynamically by scanning the maps folder for .json files
        loader = MapLoader()
        try:
            self._map_names = [p.stem for p in loader.base_dir.glob("*.json")]
            self._map_names.sort()
        except Exception:
            # Fallback list
            self._map_names = ["DEFAULT_MAP", "DUST2"]

        # Controls layout
        x0, y0 = 60, 150
        row_h = 58
        ctrl_w = 360
        ctrl_h = 40
        x_left = x0 + 220
        x_right = x_left + ctrl_w + 40

        # Algorithm selector
        self._algo_selector = CycleSelector(
            x_left, y0, ctrl_w, ctrl_h,
            options=sim_config.algo_display_options(),
            value=sim_config.internal_to_display(sim_config.algorithm),
            on_change=self._on_algo_change,
        )

        # Map selector
        self._map_selector = CycleSelector(
            x_left, y0 + row_h, ctrl_w, ctrl_h,
            options=self._map_names,
            value=sim_config.map_name if sim_config.map_name in self._map_names else self._map_names[0],
            on_change=self._on_map_change,
        )

        # Instance selector (placed below Map)
        self._instance_selector = CycleSelector(
            x_left, y0 + 2 * row_h, ctrl_w, ctrl_h,
            options=sim_config.instance_manager.names(self._map_names[0]),
            value=sim_config.instance_name,
            on_change=self._on_instance_change,
        )

        # Number of agents
        self._agents_stepper = Stepper(
            x_left, y0 + 3 * row_h, ctrl_w, ctrl_h,
            value=float(sim_config.num_agents), step=1.0, min_value=1.0, max_value=50.0, fmt="{:.0f}",
            on_change=lambda v: self._set_num_agents(int(v)),
        )

        # Spawn rate (probability per step)
        self._spawn_stepper = Stepper(
            x_left, y0 + 4 * row_h, ctrl_w, ctrl_h,
            value=float(sim_config.spawn_prob), step=0.01, min_value=0.0, max_value=1.0, fmt="{:.2f}",
            on_change=self._set_spawn_prob,
        )

        # Iddleness growth rate
        self._iddleness_stepper = Stepper(
            x_left, y0 + 5 * row_h, ctrl_w, ctrl_h,
            value=float(sim_config.iddleness_growth), step=0.001, min_value=0.0, max_value=1.0, fmt="{:.3f}",
            on_change=self._set_iddleness_growth,
        )
        
        # ACO specific controls placed on the right column
        aco = sim_config.algo_params.get("AntColony", {})
        aco = sim_config.algo_params.get("AntColonyLecture", {}) if not aco else aco
        self._aco_evap = Stepper(
            x_right, y0 + 0 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("evaporation_rate", 0.1)), step=0.01, min_value=0.0, max_value=1.0, fmt="{:.2f}",
            on_change=lambda v: self._set_aco_param("evaporation_rate", float(v)),
        )
        self._aco_alpha = Stepper(
            x_right, y0 + 1 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("alpha", 1.0)), step=0.1, min_value=0.0, max_value=5.0, fmt="{:.1f}",
            on_change=lambda v: self._set_aco_param("alpha", float(v)),
        )
        self._aco_beta = Stepper(
            x_right, y0 + 2 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("beta", 2.0)), step=0.1, min_value=0.0, max_value=5.0, fmt="{:.1f}",
            on_change=lambda v: self._set_aco_param("beta", float(v)),
        )
        self._aco_exploration_rate = Stepper(
            x_right, y0 + 3 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("exploration_rate", 0.15)), step=0.01, min_value=0.0, max_value=1.0, fmt="{:.2f}",
            on_change=lambda v: self._set_aco_param("exploration_rate", float(v)),
        )
        self._aco_tabu_length = Stepper(
            x_right, y0 + 4 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("tabu_length", 15)), step=1.0, min_value=1.0, max_value=100.0, fmt="{:.0f}",
            on_change=lambda v: self._set_aco_param("tabu_length", int(v)),
        )
        # Initialize disabled state according to currently selected instance
        try:
            self._on_instance_change(sim_config.instance_name)
        except Exception:
            pass
        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_back and self._btn_back.is_clicked(pos, event):
                self.go_back()
        if self._btn_back:
            self._btn_back.hover_property(event)
        # Forward to controls
        if self._instance_selector:
            self._instance_selector.handle_event(event)
        if self._algo_selector:
            self._algo_selector.handle_event(event)
        if self._map_selector:
            self._map_selector.handle_event(event)
        if self._agents_stepper:
            self._agents_stepper.handle_event(event)
        if self._spawn_stepper:
            self._spawn_stepper.handle_event(event)
        if self._iddleness_stepper:
            self._iddleness_stepper.handle_event(event)
        if self._is_aco():
            self._aco_evap and self._aco_evap.handle_event(event)
            self._aco_alpha and self._aco_alpha.handle_event(event)
            self._aco_beta and self._aco_beta.handle_event(event)
            self._aco_exploration_rate and self._aco_exploration_rate.handle_event(event)
            self._aco_tabu_length and self._aco_tabu_length.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        screen.fill(self.utils.WHITE)
        title = self.font.render("Settings", True, self.utils.BLACK)
        screen.blit(title, (40, 90))

        # Labels
        x0, y0 = 60, 150
        row_h = 58
        ctrl_w = 360
        x_left = x0 + 220
        x_right = x_left + ctrl_w + 40
        # Left column labels (instance placed below Map)
        labels = [
            ("Algorithm", y0),
            ("Map", y0 + row_h),
            ("Instance", y0 + 2 * row_h),
            ("Number of Agents", y0 + 3 * row_h),
            ("Events spawn rate (0-1)", y0 + 4 * row_h),
            ("Idleness growth rate (0-1)", y0 + 5 * row_h),
        ]
        for text, y in labels:
            surf = self.small.render(text, True, self.utils.BLACK)
            screen.blit(surf, (x0, y + 8))

        if self._algo_selector:
            self._algo_selector.draw(screen)
        if self._map_selector:
            self._map_selector.draw(screen)
        if self._instance_selector:
            self._instance_selector.draw(screen)
        if self._agents_stepper:
            self._agents_stepper.draw(screen)
        if self._spawn_stepper:
            self._spawn_stepper.draw(screen)
        if self._iddleness_stepper:
            self._iddleness_stepper.draw(screen)

        # Section spécifique ACO
        if self._is_aco():
            # Right column labels for algorithm-specific parameters
            self._draw_label(screen, "Evaporation", x_right, y0 + 0 * row_h)
            self._aco_evap and self._aco_evap.draw(screen)
            self._draw_label(screen, "Alpha", x_right, y0 + 1 * row_h)
            self._aco_alpha and self._aco_alpha.draw(screen)
            self._draw_label(screen, "Beta", x_right, y0 + 2 * row_h)
            self._aco_beta and self._aco_beta.draw(screen)
            self._draw_label(screen, "Exploration Rate", x_right, y0 + 3 * row_h)
            self._aco_exploration_rate and self._aco_exploration_rate.draw(screen)
            self._draw_label(screen, "Tabu Length", x_right, y0 + 4 * row_h)
            self._aco_tabu_length and self._aco_tabu_length.draw(screen)

        if self._btn_back:
            self._btn_back.draw(screen)

    # Helpers
    def _draw_label(self, screen: pygame.Surface, text: str, x: int, y: int) -> None:
        surf = self.small.render(text, True, self.utils.BLACK)
        screen.blit(surf, (x, y + 8))

    def _is_aco(self) -> bool:
        return sim_config.algorithm == "AntColony" or sim_config.algorithm == "AntColonyLecture"

    # Callbacks
    def _on_instance_change(self, name: str) -> None:
        sim_config.instance_name = name
        if name != "no instance":
            inst = sim_config.instance_manager.get(name)
            num_agents = inst.nb_agent if inst is not None else 1
            self._agents_stepper.value = num_agents
            self._set_num_agents(num_agents)
            # Apply instance-specific idleness growth rate to config and UI
            if inst is not None:
                sim_config.iddleness_growth = float(getattr(inst, "idleness_growth", sim_config.iddleness_growth))
                # update UI control if exists
                if self._iddleness_stepper:
                    self._iddleness_stepper.value = float(sim_config.iddleness_growth)
            # Disable steppers that are governed by the instance
            if self._agents_stepper:
                self._agents_stepper.set_disabled(True)
            if self._iddleness_stepper:
                self._iddleness_stepper.set_disabled(True)
        else:
            # No instance selected: allow editing
            if self._agents_stepper:
                self._agents_stepper.set_disabled(False)
            if self._iddleness_stepper:
                self._iddleness_stepper.set_disabled(False)
    
    
    def _on_algo_change(self, name: str) -> None:
        sim_config.algorithm = sim_config.display_to_internal(name)

    def _on_map_change(self, name: str) -> None:
        sim_config.map_name = name
        
        new_opts = sim_config.instance_manager.names(name)
        self._instance_selector.options= new_opts
        self._instance_selector.index=0
        self._on_instance_change(new_opts[0])

    def _set_num_agents(self, n: int) -> None:
        sim_config.num_agents = max(1, int(n))

    def _set_spawn_prob(self, v: float) -> None:
        sim_config.spawn_prob = max(0.0, min(1.0, float(v)))

    def _set_aco_param(self, key: str, v: float) -> None:
        p = sim_config.algo_params.setdefault("AntColony", {})
        p[key] = v

    def _set_iddleness_growth(self, v: float) -> None:
        sim_config.iddleness_growth = max(0.0, min(1.0, float(v)))
