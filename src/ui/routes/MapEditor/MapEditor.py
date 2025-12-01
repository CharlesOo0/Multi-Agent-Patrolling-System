from __future__ import annotations

import pygame
import json
from typing import Optional, Callable
import numpy as np

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

        self.MAX_CELL_SIZE = 25
        self.MIN_CELL_SIZE = 15

        #offset and buttons
        self.map_offset_x = 0
        self.map_offset_y = 0
        self._btn_left: Button | None = None
        self._btn_right: Button | None = None
        self._btn_up: Button | None = None
        self._btn_bottom: Button | None = None
        self._btn_add_col: Button | None = None
        self._btn_add_row: Button | None = None
        self._btn_del_col: Button | None = None
        self._btn_del_row: Button | None = None
        self._btn_incr_cell_size: Button | None = None
        self._btn_decr_cell_size: Button | None = None

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
        
        cross_x = x0 + 50  # left of map
        cross_y = y0 + 150  # vertically centered-ish

        menu_x = x0 
        menu_y = cross_y + 150
        menu_size_x = 300
        menu_size_y = 50 

        size = 44
        gap = 10
        self._btn_up = Button(cross_x + size + gap, cross_y - size - gap, size, size, "U", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_bottom = Button(cross_x + size + gap, cross_y + size + gap, size, size, "D", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_left = Button(cross_x, cross_y, size, size, "R", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_right = Button(cross_x + (size + gap) * 2, cross_y, size, size, "L", self.utils.GRAY, self.utils.LIGHT_GRAY)

        self._btn_add_row = Button(menu_x,menu_y,menu_size_x,menu_size_y,"Add Row", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_del_row = Button(menu_x,menu_y + menu_size_y + gap,menu_size_x,menu_size_y,"Delete Row", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_add_col = Button(menu_x,menu_y + (menu_size_y + gap) * 2,menu_size_x,menu_size_y,"Add Column", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_del_col = Button(menu_x,menu_y + (menu_size_y + gap) * 3,menu_size_x,menu_size_y,"Delete Column", self.utils.GRAY, self.utils.LIGHT_GRAY)

        self._btn_incr_cell_size = Button(menu_x,menu_y +  (menu_size_y + gap) * 4 + gap*2,menu_size_x,menu_size_y,"Increase Cell Size", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_decr_cell_size = Button(menu_x,menu_y +  (menu_size_y + gap) * 5 + gap*2,menu_size_x,menu_size_y,"Decrease Cell Size", self.utils.GRAY, self.utils.LIGHT_GRAY)

        self._on_map_change(self._map_selector.value)

        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_back and self._btn_back.is_clicked(pos, event):
                self.go_back()

            if self._btn_left and self._btn_left.is_clicked(pos, event):
                self.map_offset_x -= 5
                self._save_full_map_json(self._map_selector.value)

            if self._btn_right and self._btn_right.is_clicked(pos, event):
                self.map_offset_x += 5                
                self._save_full_map_json(self._map_selector.value)

            if self._btn_bottom and self._btn_bottom.is_clicked(pos, event):
                self.map_offset_y += 5
                self._save_full_map_json(self._map_selector.value)

            if self._btn_up and self._btn_up.is_clicked(pos, event):
                self.map_offset_y -= 5
                self._save_full_map_json(self._map_selector.value)

            if self._btn_add_col and self._btn_add_col.is_clicked(pos, event):
                self.nbr_col += 1
                self.map = np.hstack([self.map, np.ones((self.nbr_row-1, 1), dtype=self.map.dtype)])
                self._save_full_map_json(self._map_selector.value)

            if self._btn_del_col and self._btn_del_col.is_clicked(pos, event):
                if self.nbr_col > 1:
                    self.nbr_col -= 1
                    self.map = self.map[:, :-1]
                    self._save_full_map_json(self._map_selector.value)

            if self._btn_add_row and self._btn_add_row.is_clicked(pos, event):
                self.nbr_row += 1
                new_row = np.ones((1, self.nbr_col), dtype=self.map.dtype)
                self.map = np.vstack([self.map, new_row])
                self._save_full_map_json(self._map_selector.value)

            if self._btn_del_row and self._btn_del_row.is_clicked(pos, event):
                if self.nbr_row > 1:
                    self.nbr_row -= 1
                    self.map = self.map[:-1, :]
                    self._save_full_map_json(self._map_selector.value)

            if self._btn_incr_cell_size and self._btn_incr_cell_size.is_clicked(pos, event):
                if self.CELL_SIZE < self.MAX_CELL_SIZE:
                    self.CELL_SIZE += 1
                    self._save_full_map_json(self._map_selector.value)

            if self._btn_decr_cell_size and self._btn_decr_cell_size.is_clicked(pos, event):
                if self.CELL_SIZE > self.MIN_CELL_SIZE:
                    self.CELL_SIZE -= 1
                    self._save_full_map_json(self._map_selector.value)

            if self.map is not None:
                base_x, base_y = self.grid_origin
                base_x -= 100
                x_rel = pos[0] - base_x
                y_rel = pos[1] - base_y

                cell_size = self.CELL_SIZE + self.MARGIN
                i = y_rel // cell_size
                j = x_rel // cell_size

                if 0 <= i < self.map.shape[0] and 0 <= j < self.map.shape[1]:
                    self.map[i, j] = 0 if self.map[i, j] == 1 else 1
                    self._save_full_map_json(self._map_selector.value)

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
            screen.blit(self.background_image, (base_x+self.map_offset_x, base_y+self.map_offset_y))

        # Draw overlay grid
        if self.map is not None:
            overlay = pygame.Surface((self.grid_width, self.grid_height), pygame.SRCALPHA)
            for x in range(self.nbr_row-1):
                for y in range(self.nbr_col-1):
                    if self.map[x, y] == 1:
                        color = (*self.utils.BLACK, 128)
                    else:
                        color = (*self.utils.WHITE, 128)
                    pygame.draw.rect(
                        overlay,
                        color,
                        [
                            (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN,
                            (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN,
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

        if self._btn_add_row:
            self._btn_add_row.draw(screen)

        if self._btn_del_row:
            self._btn_del_row.draw(screen)

        if self._btn_add_col:
            self._btn_add_col.draw(screen)

        if self._btn_del_col:
            self._btn_del_col.draw(screen)

        if self._btn_incr_cell_size:
            self._btn_incr_cell_size.draw(screen)

        if self._btn_decr_cell_size:
            self._btn_decr_cell_size.draw(screen)

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
            self.nbr_row = data.get("rows", 0)
            self.nbr_col = data.get("cols", 0)
            self.CELL_SIZE = data.get("cell_size",0)

        except Exception as e:
            print(f"Failed to load map preview for {name}: {e}")
            self._map_preview = None

    def _save_full_map_json(self, name: str) -> None:
        """Rewrite the entire map JSON after structural changes."""
        try:
            loader = MapLoader()
            json_path = loader._resolve_path(name, "json")

            data = {
                "map_offset_x": self.map_offset_x,
                "map_offset_y": self.map_offset_y,
                "rows": self.nbr_row,
                "cols": self.nbr_col,
                "cell_size": self.CELL_SIZE,
                "grid": self.map.astype(int).tolist()
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"Failed to save full map JSON for {name}: {e}")
