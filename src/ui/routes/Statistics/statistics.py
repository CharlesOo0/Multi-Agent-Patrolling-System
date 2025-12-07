from __future__ import annotations

from typing import Optional, Callable, Dict, Any, List
import pygame
import numpy as np
import csv
from datetime import datetime

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.routes.base import Page
import json


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
        self._btn_export: Button | None = None
        self._ready = False
        self.results: Dict[str, Any] | None = None

    def set_results(self, results: Dict[str, Any]) -> None:
        self.results = results

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _export_to_json(self) -> None:

        if not self.results:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stats_export_{timestamp}.json"

        export_data = {
            "general_information": {
                "algorithm": self.results.get("algorithm_name", "?"),
                "steps": self.results.get("steps", 0),
                "events": self.results.get("event_count", 0),
                "map_shape": self.results.get("map_shape", (0, 0)),
            },
            "average_idleness_history": self.results.get("average_idleness_history", [])
            or [],
            "maximum_idleness_history": self.results.get("maximum_idleness_history", [])
            or [],
            "total_coverage_history": self.results.get("total_coverage_history", [])
            or [],
            "coverage_by_agent_history": self.results.get(
                "coverage_by_agent_history", []
            )
            or [],
            "agentswork_history": self.results.get("agentswork_history", []) or [],
        }

        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

        print(f"Statistics exported to {filename}")

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        if self._ready:
            return
        w, h = screen.get_size()
        bw, bh, gap = 160, 46, 12
        self._btn_home = Button(
            20, 20, 160, 46, "Accueil", self.utils.GRAY, self.utils.LIGHT_GRAY
        )
        self._btn_rerun = Button(
            20 + 160 + gap,
            20,
            bw,
            bh,
            "Relancer",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self._btn_export = Button(
            20 + 2 * (160 + gap),
            20,
            bw,
            bh,
            "Exporter",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
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
            if self._btn_export and self._btn_export.is_clicked(pos, event):
                self._export_to_json()

    def update(self, dt: float) -> None:
        pass

    # --- Simple graph helpers (pygame-based) ---
    def _draw_axes(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, self.utils.BLACK, rect, 1)
        # Axes
        pygame.draw.line(
            surface,
            self.utils.BLACK,
            (rect.left + 40, rect.bottom - 30),
            (rect.right - 10, rect.bottom - 30),
            2,
        )
        pygame.draw.line(
            surface,
            self.utils.BLACK,
            (rect.left + 40, rect.top + 10),
            (rect.left + 40, rect.bottom - 30),
            2,
        )

    def _plot_line(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: List[float],
        color=(30, 144, 255),
    ) -> None:
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

    def _plot_bars(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        bars: List[float],
        color=(100, 149, 237),
    ) -> None:
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

        title = self.font.render(
            "Statistiques de la simulation", True, self.utils.BLACK
        )
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 20))

        # Boutons
        if self._btn_home:
            self._btn_home.draw(screen)
        if self._btn_rerun:
            self._btn_rerun.draw(screen)
        if self._btn_export:
            self._btn_export.draw(screen)

        if not self.results:
            msg = self.small.render(
                "Aucune donnée de simulation.", True, self.utils.BLACK
            )
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
        avg = self.results.get("average_idleness_history", []) or []
        g1_rect = pygame.Rect(50, 250, (screen.get_width() - 100) / 2, 180)
        self._draw_axes(screen, g1_rect)
        self._plot_line(screen, g1_rect, avg)
        # labels
        x_lbl = self.small.render("Pas exécutés", True, self.utils.BLACK)
        screen.blit(
            x_lbl,
            (
                g1_rect.left + g1_rect.width // 2 - x_lbl.get_width() // 2,
                g1_rect.bottom - 18,
            ),
        )
        y_lbl_surf = self.small.render("Valeur", True, self.utils.BLACK)
        y_lbl = pygame.transform.rotate(y_lbl_surf, 90)
        screen.blit(
            y_lbl,
            (
                g1_rect.left + 8,
                g1_rect.top + g1_rect.height // 2 - y_lbl.get_height() // 2,
            ),
        )
        last_avg = f"{avg[-1]:.2f}" if avg else "n/a"
        g1_label = self.small.render(
            f"Moyenne d'oisiveté: {last_avg} points", True, self.utils.BLACK
        )
        screen.blit(g1_label, (g1_rect.left, g1_rect.top - 20))

        # Graphique 2: maximum d'oisiveté dans le temps
        max_hist = self.results.get("maximum_idleness_history", []) or []
        g2_rect = pygame.Rect(
            50 + (screen.get_width() - 100) / 2,
            250,
            (screen.get_width() - 100) / 2,
            180,
        )
        self._draw_axes(screen, g2_rect)
        # use a different color for the max line
        self._plot_line(screen, g2_rect, max_hist, color=(220, 20, 60))
        # labels
        x_lbl2 = self.small.render("Pas exécutés", True, self.utils.BLACK)
        screen.blit(
            x_lbl2,
            (
                g2_rect.left + g2_rect.width // 2 - x_lbl2.get_width() // 2,
                g2_rect.bottom - 18,
            ),
        )
        y_lbl2_surf = self.small.render("Valeur", True, self.utils.BLACK)
        y_lbl2 = pygame.transform.rotate(y_lbl2_surf, 90)
        screen.blit(
            y_lbl2,
            (
                g2_rect.left + 8,
                g2_rect.top + g2_rect.height // 2 - y_lbl2.get_height() // 2,
            ),
        )
        last_max = f"{max_hist[-1]:.2f}" if max_hist else "n/a"
        g2_label = self.small.render(
            f"Maximum d'oisiveté: {last_max} points", True, self.utils.BLACK
        )
        screen.blit(g2_label, (g2_rect.left, g2_rect.top - 20))

        # Graphique 3: couverture totale dans le temps
        total_cov = self.results.get("total_coverage_history", []) or []
        g3_rect = pygame.Rect(
            50, g2_rect.bottom + 50, (screen.get_width() - 100) / 2, 180
        )
        self._draw_axes(screen, g3_rect)
        # use a different color for the total coverage line
        self._plot_line(screen, g3_rect, total_cov, color=(220, 20, 60))
        # labels
        x_lbl3 = self.small.render("Pas exécutés", True, self.utils.BLACK)
        screen.blit(
            x_lbl3,
            (
                g3_rect.left + g3_rect.width // 2 - x_lbl3.get_width() // 2,
                g3_rect.bottom - 18,
            ),
        )
        y_lbl3_surf = self.small.render("Couverture", True, self.utils.BLACK)
        y_lbl3 = pygame.transform.rotate(y_lbl3_surf, 90)
        screen.blit(
            y_lbl3,
            (
                g3_rect.left + 8,
                g3_rect.top + g3_rect.height // 2 - y_lbl3.get_height() // 2,
            ),
        )
        last_total = f"{total_cov[-1]:.2f}" if total_cov else "n/a"
        g3_label = self.small.render(
            f"Couverture totale: {last_total}", True, self.utils.BLACK
        )
        screen.blit(g3_label, (g3_rect.left, g3_rect.top - 20))

        # Graphique 4: Coverage par agent
        cov_hist = self.results.get("coverage_by_agent_history", []) or []
        g4_rect = pygame.Rect(
            50 + (screen.get_width() - 100) / 2,
            g2_rect.bottom + 50,
            (screen.get_width() - 100) / 2,
            180,
        )
        g4_label = self.small.render("Couverture par agent", True, self.utils.BLACK)
        screen.blit(g4_label, (g4_rect.left, g4_rect.top - 20))
        self._draw_axes(screen, g4_rect)
        # labels
        x_lbl4 = self.small.render("Pas exécutés", True, self.utils.BLACK)
        screen.blit(
            x_lbl4,
            (
                g4_rect.left + g4_rect.width // 2 - x_lbl4.get_width() // 2,
                g4_rect.bottom - 18,
            ),
        )
        y_lbl4_surf = self.small.render("Couverture", True, self.utils.BLACK)
        y_lbl4 = pygame.transform.rotate(y_lbl4_surf, 90)
        screen.blit(
            y_lbl4,
            (
                g4_rect.left + 8,
                g4_rect.top + g4_rect.height // 2 - y_lbl4.get_height() // 2,
            ),
        )
        # Palette of colors to cycle through for each agent
        palette = [
            (30, 144, 255),  # dodger blue
            (220, 20, 60),  # crimson
            (34, 139, 34),  # forest green
            (255, 140, 0),  # dark orange
            (148, 0, 211),  # dark violet
            (255, 105, 180),  # hot pink
            (70, 130, 180),  # steel blue
        ]
        for i, agent_hist in enumerate(cov_hist):
            color = palette[i % len(palette)]
            self._plot_line(screen, g4_rect, agent_hist or [], color=color)
            # draw a small legend for each agent above the graph
