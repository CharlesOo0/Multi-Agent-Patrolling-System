from __future__ import annotations

import pygame
from typing import Optional, Callable

from .components.button import Button
from .components.utils import viz_utils
from .base import Page


class SettingsPage(Page):
    def __init__(self, go_back: Callable[[], None]):
        self.utils = viz_utils()
        self.font = pygame.font.SysFont(None, 42)
        self.small = pygame.font.SysFont(None, 26)
        self.go_back = go_back
        self._btn_back: Button | None = None
        self._ready = False

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        if self._ready:
            return
        w, h = screen.get_size()
        self._btn_back = Button(20, 20, 140, 44, "Retour", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_back and self._btn_back.is_clicked(pos, event):
                self.go_back()
        if self._btn_back:
            self._btn_back.hover_property(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        screen.fill(self.utils.WHITE)
        title = self.font.render("Paramètres", True, self.utils.BLACK)
        screen.blit(title, (40, 90))

        info = [
            "Ici, vous pouvez déplacer progressivement vos réglages",
            "- Nombre d'agents",
            "- Carte à charger",
            "- Vitesse par défaut",
            "- Algorithme (Heuristic / ACO)",
        ]
        y = 150
        for line in info:
            surf = self.small.render(line, True, self.utils.BLACK)
            screen.blit(surf, (40, y))
            y += surf.get_height() + 8

        if self._btn_back:
            self._btn_back.draw(screen)
