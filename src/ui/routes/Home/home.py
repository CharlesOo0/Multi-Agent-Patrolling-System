from __future__ import annotations

import pygame
from typing import Optional, Callable

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.routes.base import Page


class HomePage(Page):
    def __init__(self, go_to_sim: Callable[[], None], go_to_settings: Callable[[], None]):
        self.utils = viz_utils()
        self.font = pygame.font.SysFont(None, 52)
        self.small = pygame.font.SysFont(None, 28)
        self._buttons_ready = False
        self._btn_sim: Button | None = None
        self._btn_settings: Button | None = None
        self.go_to_sim = go_to_sim
        self.go_to_settings = go_to_settings

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._buttons_ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _ensure_buttons(self, screen: pygame.Surface) -> None:
        if self._buttons_ready:
            return
        w, h = screen.get_size()
        bw, bh, gap = 240, 60, 20
        cx = w // 2 - bw // 2
        cy = h // 2
        self._btn_sim = Button(cx, cy - bh - gap, bw, bh, "Lancer simulation", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_settings = Button(cx, cy + gap, bw, bh, "Paramètres", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._buttons_ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_sim and self._btn_sim.is_clicked(pos, event):
                self.go_to_sim()
            if self._btn_settings and self._btn_settings.is_clicked(pos, event):
                self.go_to_settings()
        # hover cursors
        for b in (self._btn_sim, self._btn_settings):
            if b:
                b.hover_property(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_buttons(screen)
        screen.fill(self.utils.WHITE)
        title = self.font.render("Multi-Agent Patrolling", True, self.utils.BLACK)
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 120))

        subtitle = self.small.render("Page d'accueil", True, self.utils.BLACK)
        screen.blit(subtitle, (screen.get_width() // 2 - subtitle.get_width() // 2, 180))

        if self._btn_sim:
            self._btn_sim.draw(screen)
        if self._btn_settings:
            self._btn_settings.draw(screen)
