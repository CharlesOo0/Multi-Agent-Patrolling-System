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

        # Algo-specific controls (ACO)
        self._aco_evap: Stepper | None = None
        self._aco_alpha: Stepper | None = None
        self._aco_beta: Stepper | None = None
        self._aco_exploration_rate: Stepper | None = None
        self._aco_tabu_length: Stepper | None = None

        # Data
        self._map_names: list[str] = []

        # Instance
        self._instance_selector: CycleSelector | None = None

        # Layout info (pour garder la même géométrie entre _ensure_ui et render)
        self._layout: dict | None = None

        # Scrolling state
        self._y_offset: int = 0
        self._scroll_speed: int = 40
        self._content_height: int | None = None

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

        # Layout de base
        x0, y0 = 60, 150
        row_h = 58
        ctrl_w = 360
        ctrl_h = 40
        x_left = x0 + 220
        section_gap = 40  # espace entre Environment et Alg. Parameters

        # ------- ENVIRONMENT CONTROLS (colonne verticale) -------
        y = y0

        # Algorithm selector
        self._algo_selector = CycleSelector(
            x_left, y, ctrl_w, ctrl_h,
            options=sim_config.algo_display_options(),
            value=sim_config.internal_to_display(sim_config.algorithm),
            on_change=self._on_algo_change,
        )
        y += row_h

        # Map selector
        map_value = sim_config.map_name if sim_config.map_name in self._map_names else (
            self._map_names[0] if self._map_names else "DEFAULT_MAP"
        )
        self._map_selector = CycleSelector(
            x_left, y, ctrl_w, ctrl_h,
            options=self._map_names,
            value=map_value,
            on_change=self._on_map_change,
        )
        y += row_h

        # Instance selector (below Map)
        inst_opts = []
        try:
            inst_opts = sim_config.instance_manager.names(map_value)
        except Exception:
            inst_opts = ["no instance"]

        self._instance_selector = CycleSelector(
            x_left, y, ctrl_w, ctrl_h,
            options=inst_opts,
            value=sim_config.instance_name,
            on_change=self._on_instance_change,
        )
        y += row_h

        # Number of agents
        self._agents_stepper = Stepper(
            x_left, y, ctrl_w, ctrl_h,
            value=float(sim_config.num_agents),
            step=1.0,
            min_value=1.0,
            max_value=50.0,
            fmt="{:.0f}",
            on_change=lambda v: self._set_num_agents(int(v)),
        )
        y += row_h

        # Spawn rate (probability per step)
        self._spawn_stepper = Stepper(
            x_left, y, ctrl_w, ctrl_h,
            value=float(sim_config.spawn_prob),
            step=0.01,
            min_value=0.0,
            max_value=1.0,
            fmt="{:.2f}",
            on_change=self._set_spawn_prob,
        )
        y += row_h

        # Iddleness growth rate
        self._iddleness_stepper = Stepper(
            x_left, y, ctrl_w, ctrl_h,
            value=float(sim_config.iddleness_growth),
            step=0.001,
            min_value=0.0,
            max_value=1.0,
            fmt="{:.3f}",
            on_change=self._set_iddleness_growth,
        )
        y += row_h

        # Point de départ de la section Alg. Parameters
        alg_y0 = y + section_gap

        # ------- ALGO-SPECIFIC CONTROLS (ACO) EN DESSOUS, MÊME COLONNE -------
        aco = sim_config.algo_params.get("AntColony", {})
        if not aco:
            aco = sim_config.algo_params.get("AntColonyLecture", {})

        self._aco_evap = Stepper(
            x_left, alg_y0 + 0 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("evaporation_rate", 0.1)),
            step=0.01,
            min_value=0.0,
            max_value=1.0,
            fmt="{:.2f}",
            on_change=lambda v: self._set_aco_param("evaporation_rate", float(v)),
        )
        self._aco_alpha = Stepper(
            x_left, alg_y0 + 1 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("alpha", 1.0)),
            step=0.1,
            min_value=0.0,
            max_value=5.0,
            fmt="{:.1f}",
            on_change=lambda v: self._set_aco_param("alpha", float(v)),
        )
        self._aco_beta = Stepper(
            x_left, alg_y0 + 2 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("beta", 2.0)),
            step=0.1,
            min_value=0.0,
            max_value=5.0,
            fmt="{:.1f}",
            on_change=lambda v: self._set_aco_param("beta", float(v)),
        )
        self._aco_exploration_rate = Stepper(
            x_left, alg_y0 + 3 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("exploration_rate", 0.15)),
            step=0.01,
            min_value=0.0,
            max_value=1.0,
            fmt="{:.2f}",
            on_change=lambda v: self._set_aco_param("exploration_rate", float(v)),
        )
        self._aco_tabu_length = Stepper(
            x_left, alg_y0 + 4 * row_h, ctrl_w, ctrl_h,
            value=float(aco.get("tabu_length", 15)),
            step=1.0,
            min_value=1.0,
            max_value=100.0,
            fmt="{:.0f}",
            on_change=lambda v: self._set_aco_param("tabu_length", int(v)),
        )

        # Sauvegarde layout pour le render
        self._layout = {
            "x0": x0,
            "y0": y0,
            "row_h": row_h,
            "ctrl_w": ctrl_w,
            "x_left": x_left,
            "alg_y0": alg_y0,
        }

        # Initialize disabled state according to currently selected instance
        try:
            self._on_instance_change(sim_config.instance_name)
        except Exception:
            pass

        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        # Mouse wheel (pygame 2+)
        if event.type == pygame.MOUSEWHEEL:
            # event.y > 0 means scroll up
            self._y_offset = max(0, self._y_offset - int(event.y * self._scroll_speed))
            max_offset = max(0, (self._content_height or 0) - (pygame.display.get_surface().get_height()))
            self._y_offset = min(self._y_offset, max_offset)
            return

        # Older pygame mouse wheel emulation: button 4(up)/5(down)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            delta = 1 if event.button == 4 else -1
            # button 4 is scroll up -> decrease offset
            self._y_offset = max(0, self._y_offset - int(delta * self._scroll_speed))
            max_offset = max(0, (self._content_height or 0) - (pygame.display.get_surface().get_height()))
            self._y_offset = min(self._y_offset, max_offset)
            return

        # Translate mouse pos into content coordinates for hit-testing
        def _translate_event(e: pygame.event.Event) -> pygame.event.Event:
            try:
                data = dict(e.dict)
            except Exception:
                data = {}
            if 'pos' in data:
                x, y = data['pos']
                data['pos'] = (x, y + self._y_offset)
            elif hasattr(e, 'pos'):
                x, y = e.pos
                data['pos'] = (x, y + self._y_offset)
            return pygame.event.Event(e.type, data)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            content_pos = (pos[0], pos[1] + self._y_offset)
            # Create a translated event for the controls
            t_event = _translate_event(event)
            if self._btn_back and self._btn_back.is_clicked(content_pos, t_event):
                self.go_back()

        if self._btn_back:
            # forward a translated event for hover checks
            try:
                hover_event = _translate_event(event)
            except Exception:
                hover_event = event
            self._btn_back.hover_property(hover_event)

        # Forward translated events to controls (so their internal pos checks use content coords)
        try:
            f_event = _translate_event(event)
        except Exception:
            f_event = event

        if self._instance_selector:
            self._instance_selector.handle_event(f_event)
        if self._algo_selector:
            self._algo_selector.handle_event(f_event)
        if self._map_selector:
            self._map_selector.handle_event(f_event)
        if self._agents_stepper:
            self._agents_stepper.handle_event(f_event)
        if self._spawn_stepper:
            self._spawn_stepper.handle_event(f_event)
        if self._iddleness_stepper:
            self._iddleness_stepper.handle_event(f_event)

        if self._is_aco():
            self._aco_evap and self._aco_evap.handle_event(f_event)
            self._aco_alpha and self._aco_alpha.handle_event(f_event)
            self._aco_beta and self._aco_beta.handle_event(f_event)
            self._aco_exploration_rate and self._aco_exploration_rate.handle_event(f_event)
            self._aco_tabu_length and self._aco_tabu_length.handle_event(f_event)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        # We'll render the entire content to a taller surface (content_surf)
        # and blit a viewport defined by self._y_offset onto the provided screen.
        layout = self._layout or {}
        x0 = layout.get("x0", 60)
        y0 = layout.get("y0", 150)
        row_h = layout.get("row_h", 58)
        ctrl_w = layout.get("ctrl_w", 360)
        x_left = layout.get("x_left", x0 + 220)
        alg_y0 = layout.get("alg_y0", y0 + 6 * row_h + 40)

        w, h = screen.get_size()

        # Estimate content height based on layout and algorithm parameter rows
        algo_key = sim_config.algorithm
        algo_params = sim_config.algo_params.get(algo_key, {})
        if self._is_aco():
            algo_rows = 5
        else:
            algo_rows = max(1, len(algo_params)) if algo_params else 1

        content_height = alg_y0 + algo_rows * row_h + 120
        content_height = max(content_height, h)
        self._content_height = content_height

        content_surf = pygame.Surface((w, content_height))
        content_surf.fill(self.utils.WHITE)

        title = self.font.render("Settings", True, self.utils.BLACK)
        content_surf.blit(title, (40, 90))

        # Labels de la section Environment
        default_labels = [
            "Algorithm",
            "Map",
            "Instance",
            "Number of Agents",
            "Events spawn rate (0-1)",
            "Idleness growth rate (0-1)",
        ]
        for i, text in enumerate(default_labels):
            y = y0 + i * row_h
            surf = self.small.render(text, True, self.utils.BLACK)
            content_surf.blit(surf, (x0, y + 8))

        # Section headers
        hdr_font = pygame.font.SysFont(None, 28)
        env_hdr = hdr_font.render("Environment", True, self.utils.BLACK)
        content_surf.blit(env_hdr, (x_left, y0 - 32))

        alg_hdr = hdr_font.render("Alg. Parameters", True, self.utils.BLACK)
        content_surf.blit(alg_hdr, (x_left, alg_y0 - 32))

        # Dessin des contrôles Environment onto content_surf (controls assume content coords)
        if self._algo_selector:
            self._algo_selector.draw(content_surf)
        if self._map_selector:
            self._map_selector.draw(content_surf)
        if self._instance_selector:
            self._instance_selector.draw(content_surf)
        if self._agents_stepper:
            self._agents_stepper.draw(content_surf)
        if self._spawn_stepper:
            self._spawn_stepper.draw(content_surf)
        if self._iddleness_stepper:
            self._iddleness_stepper.draw(content_surf)

        # ------- ALGO PARAMETERS (section sous Environment) -------
        # Algo parameters already retrieved above for content height
        if not algo_params:
            no_txt = self.small.render("No alg. parameters available", True, self.utils.BLACK)
            content_surf.blit(no_txt, (x_left, alg_y0))
        else:
            if self._is_aco():
                # ACO : steppers + labels alignés verticalement à partir de alg_y0
                self._draw_label(content_surf, "Evaporation (pheromone decay)", x_left, alg_y0 + 0 * row_h)
                self._aco_evap and self._aco_evap.draw(content_surf)

                self._draw_label(content_surf, "Alpha (pheromone weight)", x_left, alg_y0 + 1 * row_h)
                self._aco_alpha and self._aco_alpha.draw(content_surf)

                self._draw_label(content_surf, "Beta (heuristic weight)", x_left, alg_y0 + 2 * row_h)
                self._aco_beta and self._aco_beta.draw(content_surf)

                self._draw_label(content_surf, "Exploration Rate (randomness)", x_left, alg_y0 + 3 * row_h)
                self._aco_exploration_rate and self._aco_exploration_rate.draw(content_surf)

                self._draw_label(content_surf, "Tabu Length (memory)", x_left, alg_y0 + 4 * row_h)
                self._aco_tabu_length and self._aco_tabu_length.draw(content_surf)
            else:
                # Générique : simple liste label + valeur
                i = 0
                for key, val in algo_params.items():
                    label = f"{key}"
                    value_text = f"{val}"
                    y = alg_y0 + i * row_h
                    self._draw_label(content_surf, label, x_left, y)
                    txt = self.small.render(value_text, True, self.utils.BLACK)
                    content_surf.blit(txt, (x_left + ctrl_w + 20, y + 8))
                    i += 1

        if self._btn_back:
            self._btn_back.draw(content_surf)

        # Blit viewport from content_surf to screen
        view_rect = pygame.Rect(0, self._y_offset, w, h)
        screen.blit(content_surf, (0, 0), area=view_rect)

        # Draw a simple scrollbar on the right
        if content_height > h:
            bar_w = 10
            bar_x = w - bar_w - 8
            bar_y = 8
            bar_h = h - 16
            pygame.draw.rect(screen, self.utils.LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            max_offset = content_height - h
            thumb_h = max(30, int(h * (h / content_height)))
            track_h = bar_h - thumb_h
            thumb_y = bar_y + int((self._y_offset / max_offset) * track_h) if max_offset > 0 else bar_y
            pygame.draw.rect(screen, self.utils.GRAY, (bar_x, thumb_y, bar_w, thumb_h), border_radius=4)

    # Helpers
    def _draw_label(self, screen: pygame.Surface, text: str, x: int, y: int) -> None:
        surf = self.small.render(text, True, self.utils.BLACK)
        screen.blit(surf, (x, y + 8))

    def _is_aco(self) -> bool:
        return sim_config.algorithm in ("AntColony", "AntColonyLecture")

    # Callbacks
    def _on_instance_change(self, name: str) -> None:
        sim_config.instance_name = name
        if name != "no instance":
            inst = sim_config.instance_manager.get(name)
            num_agents = inst.nb_agent if inst is not None else 1

            if self._agents_stepper:
                self._agents_stepper.value = num_agents
            self._set_num_agents(num_agents)

            # Apply instance-specific idleness growth rate to config and UI
            if inst is not None:
                sim_config.iddleness_growth = float(
                    getattr(inst, "idleness_growth", sim_config.iddleness_growth)
                )
                if self._iddleness_stepper:
                    self._iddleness_stepper.value = float(sim_config.iddleness_growth)

            # Disable steppers that are governed by the instance
            if self._agents_stepper:
                self._agents_stepper.set_disabled(True)
            if self._iddleness_stepper:
                self._iddleness_stepper.set_disabled(True)
            if self._spawn_stepper:
                self._spawn_stepper.set_disabled(True)
        else:
            # No instance selected: allow editing
            if self._agents_stepper:
                self._agents_stepper.set_disabled(False)
            if self._iddleness_stepper:
                self._iddleness_stepper.set_disabled(False)
            if self._spawn_stepper:
                self._spawn_stepper.set_disabled(False)

    def _on_algo_change(self, name: str) -> None:
        sim_config.algorithm = sim_config.display_to_internal(name)

    def _on_map_change(self, name: str) -> None:
        sim_config.map_name = name

        try:
            new_opts = sim_config.instance_manager.names(name)
        except Exception:
            new_opts = ["no instance"]

        if self._instance_selector:
            self._instance_selector.options = new_opts
            self._instance_selector.index = 0

        if new_opts:
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
