from __future__ import annotations

import pygame
from typing import List, Callable
from .utils import viz_utils
from .button import Button


class Stepper:
    """Contrôle +/- pour ajuster une valeur numérique (int ou float)."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        value: float,
        step: float = 1.0,
        min_value: float | None = None,
        max_value: float | None = None,
        fmt: str = "{:.2f}",
        on_change: Callable[[float], None] | None = None,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.utils = viz_utils()
        self.value = value
        self.step = step
        self.min_value = min_value
        self.max_value = max_value
        self.on_change = on_change
        self.fmt = fmt

        btn_w = height
        self.btn_dec = Button(x, y, btn_w, height, "-", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.btn_inc = Button(x + width - btn_w, y, btn_w, height, "+", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.font = pygame.font.SysFont(None, 26)

    def _set_value(self, v: float) -> None:
        if self.min_value is not None:
            v = max(self.min_value, v)
        if self.max_value is not None:
            v = min(self.max_value, v)
        if v != self.value:
            self.value = v
            if self.on_change:
                self.on_change(self.value)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.btn_dec.hover_property(event)
        self.btn_inc.hover_property(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self.btn_dec.is_clicked(pos, event):
                self._set_value(self.value - self.step)
            elif self.btn_inc.is_clicked(pos, event):
                self._set_value(self.value + self.step)

    def draw(self, surface: pygame.Surface) -> None:
        # Cadre
        pygame.draw.rect(surface, self.utils.LIGHT_GRAY, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.utils.BLACK, self.rect, 2, border_radius=6)
        # Boutons
        self.btn_dec.draw(surface)
        self.btn_inc.draw(surface)
        # Valeur
        text = self.font.render(self.fmt.format(self.value), True, self.utils.BLACK)
        tx = self.rect.centerx - text.get_width() // 2
        ty = self.rect.centery - text.get_height() // 2
        surface.blit(text, (tx, ty))


class CycleSelector:
    """Sélecteur qui fait défiler une liste de valeurs (ex: algorithme, map)."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        options: List[str],
        value: str,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.utils = viz_utils()
        self.options = options
        self.index = max(0, options.index(value) if value in options else 0)
        self.on_change = on_change
        self.font = pygame.font.SysFont(None, 26)

        btn_w = height
        self.btn_prev = Button(x, y, btn_w, height, "<", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.btn_next = Button(x + width - btn_w, y, btn_w, height, ">", self.utils.GRAY, self.utils.LIGHT_GRAY)

    @property
    def value(self) -> str:
        return self.options[self.index]

    def _notify(self) -> None:
        if self.on_change:
            self.on_change(self.value)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.btn_prev.hover_property(event)
        self.btn_next.hover_property(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self.btn_prev.is_clicked(pos, event):
                self.index = (self.index - 1) % len(self.options)
                self._notify()
            elif self.btn_next.is_clicked(pos, event):
                self.index = (self.index + 1) % len(self.options)
                self._notify()

    def draw(self, surface: pygame.Surface) -> None:
        # Cadre
        pygame.draw.rect(surface, self.utils.LIGHT_GRAY, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.utils.BLACK, self.rect, 2, border_radius=6)
        # Boutons
        self.btn_prev.draw(surface)
        self.btn_next.draw(surface)
        # Valeur
        text = self.font.render(self.value, True, self.utils.BLACK)
        tx = self.rect.centerx - text.get_width() // 2
        ty = self.rect.centery - text.get_height() // 2
        surface.blit(text, (tx, ty))
