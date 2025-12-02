from __future__ import annotations

import pygame
import json
from typing import Optional, Callable
import numpy as np

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.components.inputs import Stepper, CycleSelector,TextInput
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
        self.map_scale = 1.0    # scale factor of background PNG

        #Grid
        self.CELL_SIZE = None
        self.MARGIN = 1
        self.grid_width = 630
        self.grid_height = 630
        self.background_image = None
        self.screen = None

        #offset and buttons
        self.map_offset_x = 0
        self.map_offset_y = 0
        self._btn_left: Button | None = None
        self._btn_right: Button | None = None
        self._btn_up: Button | None = None
        self._btn_bottom: Button | None = None
        self._btn_size_plus: Button | None = None
        self._btn_size_down: Button | None = None

        self._btn_add_row_col_: Button | None = None
        self._btn_del_row_col: Button | None = None

        self._btn_create_map : Button | None = None
        self._btn_delete_map : Button | None = None

        #Create Map Pop Up
        self.show_create_popup = False
        self.input_map_name = None
        self.input_png_path = None
        self.btn_popup_create = None
        self.btn_popup_cancel = None

        #Delete Map Pop Up
        self.show_delete_popup = False
        self.btn_delete_yes = None
        self.btn_delete_no = None


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
        self._btn_size_plus = Button(cross_x, cross_y + size + gap, size, size, "+", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_size_down = Button(cross_x + (size + gap) * 2, cross_y + size + gap, size, size, "-", self.utils.GRAY, self.utils.LIGHT_GRAY)


        self._btn_add_row_col = Button(menu_x,menu_y,menu_size_x,menu_size_y,"Add Row/Col", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_del_row_col = Button(menu_x,menu_y + menu_size_y + gap,menu_size_x,menu_size_y,"Delete Row/Col", self.utils.GRAY, self.utils.LIGHT_GRAY)

        self._btn_create_map = Button(menu_x,menu_y+ (menu_size_y+gap)*3,menu_size_x,menu_size_y,"Create Map",self.utils.LIGHT_GRAY,self.utils.LIGHT_GRAY)
        self._btn_delete_map = Button(menu_x,menu_y+ (menu_size_y+gap)*4,menu_size_x,menu_size_y,"Delete Map",self.utils.LIGHT_GRAY,self.utils.LIGHT_GRAY)

        self._on_map_change(self._map_selector.value)

        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        # DELETE MAP POPUP
        if self.show_delete_popup:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()

                if self.btn_delete_no.is_clicked(pos, event):
                    self.show_delete_popup = False
                    return

                if self.btn_delete_yes.is_clicked(pos, event):
                    self._delete_selected_map()
                    self.show_delete_popup = False
                    return

            return

        #Create Map Pop Up
        if self.show_create_popup:
            self.input_map_name.handle_event(event)
            self.input_png_path.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()

                # Browse for PNG file
                if hasattr(self, 'btn_popup_browse') and self.btn_popup_browse.is_clicked(pos, event):
                    try:
                        import tkinter as _tk
                        from tkinter import filedialog as _fd
                        _root = _tk.Tk()
                        _root.withdraw()
                        file_path = _fd.askopenfilename(filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
                        _root.destroy()
                        if file_path:
                            self.input_png_path.text = file_path
                    except Exception as e:
                        print(f"File dialog failed: {e}")
                    return

                if self.btn_popup_cancel.is_clicked(pos, event):
                    self.show_create_popup = False
                    return

                if self.btn_popup_create.is_clicked(pos, event):
                    self._create_new_map(
                        self.input_map_name.text.strip(),
                        self.input_png_path.text.strip()
                    )
                    self.show_create_popup = False
                    return

            return  # prevent clicks behind popup

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

            if self._btn_add_row_col and self._btn_add_row_col.is_clicked(pos, event):
                # Add a new column with 1s
                new_col = np.ones((self.map.shape[0], 1), dtype=self.map.dtype)
                self.map = np.hstack([self.map, new_col])
                self.nbr_col += 1

                # Add a new row with 1s
                new_row = np.ones((1, self.map.shape[1]), dtype=self.map.dtype)
                self.map = np.vstack([self.map, new_row])
                self.nbr_row += 1

                self._save_full_map_json(self._map_selector.value)


            if self._btn_del_row_col and self._btn_del_row_col.is_clicked(pos, event):
                if self.nbr_col > 2 and self.nbr_row > 2:
                    self.nbr_col -= 1
                    self.map = self.map[:, :-1]
                    self._save_full_map_json(self._map_selector.value)
                    self.nbr_row -= 1
                    self.map = self.map[:-1, :]
                    self._save_full_map_json(self._map_selector.value)

            if self._btn_create_map and self._btn_create_map.is_clicked(pos,event):
                self._open_create_popup()

            if self._btn_delete_map and self._btn_delete_map.is_clicked(pos, event):
                self._open_delete_popup()

            if self._btn_size_plus and self._btn_size_plus.is_clicked(pos, event):
                self.map_scale += 0.1
                self._apply_scale()
                self._save_full_map_json(self._map_selector.value)
            if self._btn_size_down and self._btn_size_down.is_clicked(pos, event):
                self.map_scale -= 0.1
                self._apply_scale()
                self._save_full_map_json(self._map_selector.value)

            if self.map is not None:
                base_x, base_y = self.grid_origin
                base_x -= 100
                x_rel = pos[0] - base_x
                y_rel = pos[1] - base_y

                i : int = int(y_rel // (self.CELL_SIZE + self.MARGIN))
                j : int = int(x_rel // (self.CELL_SIZE + self.MARGIN))

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

        if self.show_create_popup:
            self._draw_create_popup(screen)
            return  # don't draw editor behind popup

        if self.show_delete_popup:
            self._draw_delete_popup(screen)
            return

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

        if self._btn_add_row_col:
            self._btn_add_row_col.draw(screen)

        if self._btn_del_row_col:
            self._btn_del_row_col.draw(screen)

        if self._btn_create_map:
            self._btn_create_map.draw(screen)

        if self._btn_delete_map:
            self._btn_delete_map.draw(screen)

        if self._btn_size_plus:
            self._btn_size_plus.draw(screen)

        if self._btn_size_down:
            self._btn_size_down.draw(screen)

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
            self.map_scale = data.get("map_scale", 1.0)

            # Apply scale to loaded image
            w, h = self.background_image.get_size()
            new_w = int(w * self.map_scale)
            new_h = int(h * self.map_scale)
            self.background_image = pygame.transform.smoothscale(self.background_image, (new_w, new_h))

            #Update cell size
            self.CELL_SIZE = self.grid_width/(self.nbr_row+1)

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
                "grid": self.map.astype(int).tolist(),
                "map_scale": self.map_scale
            }


            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            #Update Cell size
            self.CELL_SIZE = self.grid_width/(self.nbr_row+1)
        except Exception as e:
            print(f"Failed to save full map JSON for {name}: {e}")

    def _open_create_popup(self):
        self.show_create_popup = True
        # Popup layout: compute centered position using current screen size
        if self.screen is not None:
            sw, sh = self.screen.get_size()
        else:
            sw, sh = (1280, 720)

        popup_w = 600
        popup_h = 320
        popup_x = (sw - popup_w) // 2
        popup_y = (sh - popup_h) // 2

        # store popup rect for use in drawing
        self._popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)

        # input positions inside popup
        input_x = popup_x + 80
        input_w = popup_w - 200
        self.input_map_name = TextInput(input_x, popup_y + 60, input_w, 40, self.small)
        self.input_png_path = TextInput(input_x, popup_y + 140, input_w, 40, self.small)

        # Buttons positions
        btn_y = popup_y + 220
        self.btn_popup_create = Button(input_x, btn_y, 160, 44, "Create", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.btn_popup_cancel = Button(input_x + 180, btn_y, 160, 44, "Cancel", self.utils.GRAY, self.utils.LIGHT_GRAY)
        # Browse button to pick a PNG from the filesystem (placed next to png input)
        self.btn_popup_browse = Button(input_x + input_w + 10, popup_y + 140, 80, 40, "Browse", self.utils.GRAY, self.utils.LIGHT_GRAY)

    def _draw_create_popup(self, screen):
        # Dark background overlay
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        screen.blit(s, (0,0))
        # Popup box (use rect stored in _open_create_popup or compute centered fallback)
        if hasattr(self, '_popup_rect') and isinstance(self._popup_rect, pygame.Rect):
            rect = self._popup_rect
        else:
            sw, sh = screen.get_size()
            popup_w = 600
            popup_h = 320
            rect = pygame.Rect((sw - popup_w) // 2, (sh - popup_h) // 2, popup_w, popup_h)

        pygame.draw.rect(screen, (245,245,245), rect, border_radius=10)
        pygame.draw.rect(screen, (50,50,50), rect, 3, border_radius=10)

        title = self.font.render("Create New Map", True, (0,0,0))
        screen.blit(title, (rect.x + 40, rect.y + 10))

        lbl1 = self.small.render("Map name :", True, (0,0,0))
        lbl2 = self.small.render("PNG path :", True, (0,0,0))
        screen.blit(lbl1, (rect.x + 40, rect.y + 70))
        screen.blit(lbl2, (rect.x + 40, rect.y + 150))

        # Draw inputs and buttons (positions set in _open_create_popup)
        if self.input_map_name:
            self.input_map_name.draw(screen)
        if self.input_png_path:
            self.input_png_path.draw(screen)

        # Draw browse button next to PNG path input
        if hasattr(self, 'btn_popup_browse') and self.btn_popup_browse:
            self.btn_popup_browse.draw(screen)

        if self.btn_popup_create:
            self.btn_popup_create.draw(screen)
        if self.btn_popup_cancel:
            self.btn_popup_cancel.draw(screen)

    def _create_new_map(self, map_name: str, png_path: str):
        loader = MapLoader()

        # Resolve target paths
        target_png = loader._resolve_path(map_name, "png")
        target_json = loader._resolve_path(map_name, "json")

        # Copy PNG
        try:
            img = pygame.image.load(png_path).convert_alpha()
            img = pygame.transform.smoothscale(img, (630, 630))
            pygame.image.save(img, target_png)
        except Exception as e:
            print(f"Failed to copy/resize PNG: {e}")
            return

        # Create default map grid (10x10 empty)
        default_grid = [[1 for _ in range(10)] for _ in range(10)]

        data = {
            "map_offset_x": 0,
            "map_offset_y": 0,
            "rows": 9,
            "cols": 9,
            "grid": default_grid,
            "map_scale" : 1.0
        }

        # Write JSON
        try:
            with open(target_json, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to write JSON: {e}")
            return

        # Refresh selector
        self._map_names.append(map_name)
        self._map_names.sort()

        self._map_selector.options = self._map_names
        self._map_selector.index = self._map_names.index(map_name)
        self._map_selector._notify()

    def _open_delete_popup(self):
        self.show_delete_popup = True
        self.btn_delete_yes = Button(600, 450, 140, 44, "Yes", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.btn_delete_no = Button(760, 450, 140, 44, "No", self.utils.GRAY, self.utils.LIGHT_GRAY)

    def _draw_delete_popup(self, screen):
        # Dark overlay
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        screen.blit(s, (0,0))

        # Popup box
        pygame.draw.rect(screen, (245,245,245), (550,300,420,220), border_radius=10)
        pygame.draw.rect(screen, (50,50,50), (550,300,420,220), 3, border_radius=10)

        text = self.font.render("Are you sure?", True, (0,0,0))
        screen.blit(text, (610,320))

        self.btn_delete_yes.draw(screen)
        self.btn_delete_no.draw(screen)
        
    def _delete_selected_map(self):
        loader = MapLoader()
        name = self._map_selector.value

        png_path = loader._resolve_path(name, "png")
        json_path = loader._resolve_path(name, "json")

        # Delete files
        import os
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
            if os.path.exists(json_path):
                os.remove(json_path)
        except Exception as e:
            print(f"Failed to delete map files: {e}")
            return

        # Remove from list
        if name in self._map_names:
            self._map_names.remove(name)

        # Update selector
        if len(self._map_names) == 0:
            # fallback: no maps left
            self.background_image = None
            self.map = None
            return

        self._map_selector.options = self._map_names
        self._map_selector.index = 0   # select first available map
        self._map_selector._notify()

    def _apply_scale(self):
        """Rescale background image based on map_scale."""
        if self.background_image is None:
            return

        loader = MapLoader()
        name = self._map_selector.value

        # Reload original image (to avoid quality loss)
        original = pygame.image.load(loader._resolve_path(name, "png")).convert_alpha()

        w, h = original.get_size()
        new_w = int(w * self.map_scale)
        new_h = int(h * self.map_scale)

        self.background_image = pygame.transform.smoothscale(original, (new_w, new_h))
