from __future__ import annotations

from typing import Protocol, Optional
import pygame


class Page(Protocol):
    """Contract for a screen/page in the Pygame app.

    Methods are intentionally simple to fit current loop style.
    """

    def on_enter(self, prev: Optional[str] = None) -> None:
        ...

    def on_exit(self, next: Optional[str] = None) -> None:
        ...

    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    def update(self, dt: float) -> None:
        ...

    def render(self, screen: pygame.Surface) -> None:
        ...


class Router:
    """
    Routes between different pages/screens in a Pygame application.
    """

    def __init__(self, initial: str):
        self._pages: dict[str, Page] = {}
        self.current_key: Optional[str] = None
        self.current_page: Optional[Page] = None
        self.initial = initial

    def register(self, key: str, page: Page) -> None:
        self._pages[key] = page

    def start(self) -> None:
        self.navigate(self.initial)

    def navigate(self, key: str) -> None:
        if key not in self._pages:
            raise KeyError(f"Unknown page '{key}'")
        if self.current_page:
            self.current_page.on_exit(key)
        prev_key = self.current_key
        self.current_key = key
        self.current_page = self._pages[key]
        self.current_page.on_enter(prev_key)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current_page:
            self.current_page.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current_page:
            self.current_page.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        if self.current_page:
            self.current_page.render(screen)
