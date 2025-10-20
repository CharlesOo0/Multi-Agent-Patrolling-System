from __future__ import annotations

import pygame
import json
from typing import Optional, Callable

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.components.inputs import Stepper, CycleSelector
from ui.routes.base import Page
from ui.config import sim_config
from maps.MapLoader import MapLoader


class MapEditorPage(Page):
    def __init__(self, go_back: Callable[[], None]):
        self.utils = viz_utils()
        self.font = pygame.font.SysFont(None, 42)
        self.small = pygame.font.SysFont(None, 26)
        self.go_back = go_back
        self._btn_back: Button | None = None
        self._ready = False
        # UI controls
        self._map_selector: CycleSelector | None = None
        # Data
        self._map_names: list[str] = []
        # Print Utils
        self.map = None
        self.grid_origin = (500, 150)
        #Grid
        self.CELL_SIZE = 20
        self.MARGIN = 1
        self.grid_width = 1600
        self.grid_height = 1600
        self.background_image = None
        self.screen = None

        #offset and buttons
        self.map_offset_x = 0
        self.map_offset_y = 0
        self._btn_left: Button | None = None
        self._btn_right: Button | None = None
        self._btn_up: Button | None = None
        self._btn_bottom: Button | None = None

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        self.screen = screen
        if self._ready:
            return
        w, h = screen.get_size()
        self._btn_back = Button(20, 20, 140, 44, "Retour", self.utils.GRAY, self.utils.LIGHT_GRAY)
        # Discover maps dynamically by scanning the maps folder for .json files
        loader = MapLoader()
        try:
            self._map_names = [p.stem for p in loader.base_dir.glob("*.png")]
            self._map_names.sort()
        except Exception:
            # Fallback list
            self._map_names = ["DUST2"]

        # Controls layout
        x0, y0 = 60, 80
        row_h = 58
        ctrl_w = 360
        ctrl_h = 40

        # Map selector
        self._map_selector = CycleSelector(
            x0 + 300, y0, ctrl_w, ctrl_h,
            options=self._map_names,
            value=sim_config.map_name if sim_config.map_name in self._map_names else self._map_names[0],
            on_change=self._on_map_change,
        )
        
        cross_x = x0  # left of map
        cross_y = y0 + 300  # vertically centered-ish

        size = 44
        gap = 10
        self._btn_up = Button(cross_x + size + gap, cross_y - size - gap, size, size, "U", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_bottom = Button(cross_x + size + gap, cross_y + size + gap, size, size, "D", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_left = Button(cross_x, cross_y, size, size, "R", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_right = Button(cross_x + (size + gap) * 2, cross_y, size, size, "L", self.utils.GRAY, self.utils.LIGHT_GRAY)


        self._on_map_change(self._map_selector.value)

        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_back and self._btn_back.is_clicked(pos, event):
                self.go_back()

            if self._btn_left and self._btn_left.is_clicked(pos, event):
                self.map_offset_x -= 5
                self._save_map_offset(self._map_selector.value,'x')

            if self._btn_right and self._btn_right.is_clicked(pos, event):
                self.map_offset_x += 5                
                self._save_map_offset(self._map_selector.value,'x')

            if self._btn_bottom and self._btn_bottom.is_clicked(pos, event):
                self.map_offset_y += 5
                self._save_map_offset(self._map_selector.value,'y')

            if self._btn_up and self._btn_up.is_clicked(pos, event):
                self.map_offset_y -= 5
                self._save_map_offset(self._map_selector.value,'y')
            if self.map is not None:
                base_x, base_y = self.grid_origin
                base_x -= 100
                x_rel = pos[0] - base_x - self.map_offset_x
                y_rel = pos[1] - base_y - self.map_offset_y

                cell_size = self.CELL_SIZE + self.MARGIN
                i = y_rel // cell_size
                j = x_rel // cell_size

                if 0 <= i < self.map.shape[0] and 0 <= j < self.map.shape[1]:
                    self.map[i, j] = 0 if self.map[i, j] == 1 else 1
                    self._save_map_to_json(i, j, self.map[i, j])


        if self._btn_back:
            self._btn_back.hover_property(event)
            
        if self._map_selector:
            self._map_selector.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        screen.fill(self.utils.WHITE)
        base_x,base_y = self.grid_origin
        base_x -= 100
        # Draw background image
        if self.background_image is not None:
            screen.blit(self.background_image, (base_x, base_y))

        # Draw overlay grid
        if self.map is not None:
            overlay = pygame.Surface((self.grid_width, self.grid_height), pygame.SRCALPHA)
            for x in range(self.map.shape[0]):
                for y in range(self.map.shape[1]):
                    if self.map[x, y] == 1:
                        color = (*self.utils.BLACK, 128)
                    else:
                        color = (*self.utils.WHITE, 128)
                    pygame.draw.rect(
                        overlay,
                        color,
                        [
                            (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN + self.map_offset_x,
                            (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN + self.map_offset_y,
                            self.CELL_SIZE,
                            self.CELL_SIZE,
                        ],
                    )
            screen.blit(overlay, (base_x, base_y))

        # UI elements
        title = self.font.render("Editeur de Carte", True, self.utils.BLACK)
        screen.blit(title, (40, 90))

        if self._map_selector:
            self._map_selector.draw(screen)

        if self._btn_back:
            self._btn_back.draw(screen)

        if self._btn_left:
            self._btn_left.draw(screen)

        if self._btn_right:
            self._btn_right.draw(screen)

        if self._btn_bottom:
            self._btn_bottom.draw(screen)

        if self._btn_up:
            self._btn_up.draw(screen)


    # Helpers
    def _draw_label(self, screen: pygame.Surface, text: str, x: int, y: int) -> None:
        surf = self.small.render(text, True, self.utils.BLACK)
        screen.blit(surf, (x, y + 8))

    def _on_map_change(self, name: str) -> None:
        try:
            loader = MapLoader()
            self.background_image = pygame.image.load(loader._resolve_path(name, "png")).convert_alpha()
            self.map = loader.load(name)
            
            #Load offset from json
            json_path = loader._resolve_path(name, "json")
            with open(json_path, "r") as f:
                data = json.load(f)
            self.map_offset_x = data.get("map_offset_x", 0)
            self.map_offset_y = data.get("map_offset_y", 0)
        except Exception as e:
            print(f"Failed to load map preview for {name}: {e}")
            self._map_preview = None

    def _save_map_offset(self, name: str, axis : str) -> None:
        try:
            loader = MapLoader()
            json_path = loader._resolve_path(name, "json")
            with open(json_path, "r") as f:
                data = json.load(f)
            if axis == "x":
                data["map_offset_x"] = self.map_offset_x
            else :
                data["map_offset_y"] = self.map_offset_y

            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save map offset for {name}: {e}")

    def _save_map_to_json(self, i: int, j: int, value: int) -> None:
        """Save a single cell to the map JSON."""
        try:
            loader = MapLoader()
            json_path = loader._resolve_path(self._map_selector.value, "json")

            # Load existing JSON
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ensure 'map' exists and is a list of lists
            if "grid" not in data or not isinstance(data["grid"], list):
                data["grid"] = self.map.astype(int).tolist()
            else:
                # Convert individual value to int
                data["grid"][i][j] = int(value)

            # Write back to JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"Failed to save cell ({i}, {j}) for map {self._map_selector.value}: {e}")
