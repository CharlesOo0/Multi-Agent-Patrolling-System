from __future__ import annotations

from typing import Optional, Callable, Dict, Any, List
import pygame
import numpy as np

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.routes.base import Page


class StatsPage(Page):
    """Page d'affichage des statistiques de la simulation avec graphes.

    Attendu: recevoir un dictionnaire 'results' via set_results() contenant
    - 'algorithm_name': str
    - 'steps': int
    - 'average_idleness_history': List[float]
    - 'event_count': int
    - 'map_shape': tuple[int, int]
    """

    def __init__(self, go_home: Callable[[], None], go_sim: Callable[[], None]):
        self.utils = viz_utils()
        self.go_home = go_home
        self.go_sim = go_sim
        self.font = pygame.font.SysFont(None, 38)
        self.small = pygame.font.SysFont(None, 24)
        self._btn_home: Button | None = None
        self._btn_rerun: Button | None = None
        self._ready = False
        self.results: Dict[str, Any] | None = None

    def set_results(self, results: Dict[str, Any]) -> None:
        self.results = results

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        if self._ready:
            return
        w, h = screen.get_size()
        bw, bh, gap = 160, 46, 12
        self._btn_home = Button(20, 20, 160, 46, "Accueil", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._btn_rerun = Button(20 + 160 + gap, 20, bw, bh, "Relancer", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in (self._btn_home, self._btn_rerun):
            if b:
                b.hover_property(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_home and self._btn_home.is_clicked(pos, event):
                self.go_home()
            if self._btn_rerun and self._btn_rerun.is_clicked(pos, event):
                self.go_sim()

    def update(self, dt: float) -> None:
        pass

    # --- Simple graph helpers (pygame-based) ---
    def _draw_axes(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, self.utils.BLACK, rect, 1)
        # Axes
        pygame.draw.line(surface, self.utils.BLACK, (rect.left + 40, rect.bottom - 30), (rect.right - 10, rect.bottom - 30), 2)
        pygame.draw.line(surface, self.utils.BLACK, (rect.left + 40, rect.top + 10), (rect.left + 40, rect.bottom - 30), 2)

    def _plot_line(self, surface: pygame.Surface, rect: pygame.Rect, data: List[float], color=(30, 144, 255)) -> None:
        if not data:
            return
        vals = np.array(data, dtype=float)
        if len(vals) == 1:
            vals = np.concatenate([vals, vals])
        ymin, ymax = float(np.min(vals)), float(np.max(vals))
        if ymax - ymin < 1e-9:
            ymax = ymin + 1.0
        xs = np.linspace(rect.left + 50, rect.right - 14, num=len(vals))
        ys = rect.bottom - 30 - (vals - ymin) / (ymax - ymin) * (rect.height - 50)
        points = list(zip(xs.astype(int), ys.astype(int)))
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, 2)

    def _plot_bars(self, surface: pygame.Surface, rect: pygame.Rect, bars: List[float], color=(100, 149, 237)) -> None:
        if not bars:
            return
        n = len(bars)
        vals = np.array(bars, dtype=float)
        ymax = float(np.max(vals)) if np.max(vals) > 0 else 1.0
        # Compute bar geometry
        gap = 8
        available_w = rect.width - 60 - gap * (n + 1)
        bw = max(10, available_w // max(1, n))
        x = rect.left + 50 + gap
        base_y = rect.bottom - 30
        for v in vals:
            h = int((v / ymax) * (rect.height - 50))
            pygame.draw.rect(surface, color, (x, base_y - h, bw, h))
            x += bw + gap

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        screen.fill(self.utils.WHITE)

        title = self.font.render("Statistiques de la simulation", True, self.utils.BLACK)
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 20))

        # Boutons
        if self._btn_home:
            self._btn_home.draw(screen)
        if self._btn_rerun:
            self._btn_rerun.draw(screen)

        if not self.results:
            msg = self.small.render("Aucune donnée de simulation.", True, self.utils.BLACK)
            screen.blit(msg, (50, 100))
            return

        # Informations générales
        algo = str(self.results.get("algorithm_name", "?"))
        steps = int(self.results.get("steps", 0))
        events = int(self.results.get("event_count", 0))
        map_shape = self.results.get("map_shape", (0, 0))
        info_y = 90
        info_lines = [
            f"Algorithme: {algo}",
            f"Pas exécutés: {steps}",
            f"Événements: {events}",
            f"Taille carte: {map_shape}",
        ]
        for i, line in enumerate(info_lines):
            txt = self.small.render(line, True, self.utils.BLACK)
            screen.blit(txt, (50, info_y + i * 22))

        # Graphique 1: moyenne d'oisiveté dans le temps
        g1_rect = pygame.Rect(50, 200, screen.get_width() - 100, 180)
        self._draw_axes(screen, g1_rect)
        self._plot_line(screen, g1_rect, self.results.get("average_idleness_history", []))
        g1_label = self.small.render("Moyenne d'oisiveté", True, self.utils.BLACK)
        screen.blit(g1_label, (g1_rect.left, g1_rect.top - 20))