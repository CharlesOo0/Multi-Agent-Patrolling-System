import pygame
import sys
import time
from typing import Tuple, List, Dict, Any, Optional, Callable
from ui.components.button import Button
from ui.components.utils import viz_utils
from algorithm import Algorithm
import numpy as np

class Visualization:
    def __init__(self, WINDOW_SIZE: Tuple[int, int], map: np.ndarray) -> None:
        """Initialize the visualization window and layout for the grid.

        Args:
            WINDOW_SIZE: Desired window size (width, height) in pixels.
            map: 2D numpy array where 0=free cell and 1=obstacle.
        """
        pygame.init()

        # Map and grid parameters
        self.CELL_SIZE: int = 20
        self.MARGIN: int = 2
        self.map: np.ndarray = map

        # Colors and utils
        self.utils: viz_utils = viz_utils()

        # Layout parameters
        self.PADDING: int = 10
        self.BOTTOM_BAR_H: int = 60
        self.LOG_PANEL_W: int = 325

        rows, cols = self.map.shape
        # Dimensions of the grid in pixels
        self.grid_width: int = cols * (self.CELL_SIZE + self.MARGIN) + self.MARGIN
        self.grid_height: int = rows * (self.CELL_SIZE + self.MARGIN) + self.MARGIN

        # Minimum window size to contain grid + right log panel + bottom bar
        min_content_w = self.grid_width + self.LOG_PANEL_W + self.PADDING * 3
        min_content_h = self.grid_height + self.BOTTOM_BAR_H + self.PADDING * 3
        win_w = max(WINDOW_SIZE[0], min_content_w)
        win_h = max(WINDOW_SIZE[1], min_content_h)

        self.screen: pygame.Surface = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption("Multi-Agent Patrolling with algorithm (2D Grid)")
        self.font: pygame.font.Font = pygame.font.SysFont(None, 36)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.start_time: float = time.time()
        # Simulation timing: speed (ticks/sec) and simulated time accumulator
        self.sim_speed_tps: float = 10.0
        self.speed_multiplier: float = 1.0
        self.base_speed: float = self.sim_speed_tps * self.speed_multiplier  # reference to scale simulated time
        self.min_speed: float = 1.0
        self.max_speed: float = 15.0
        self.sim_time: float = 0.0

        # Compute layout rects (grid centered in left content area)
        self._recompute_layout(win_w, win_h)

        # Buttons
        self.quit_button: Button | None = None
        self.reset_button: Button | None = None
        self.speed_dec_button: Button | None = None
        self.speed_inc_button: Button | None = None
        # Callback appelé quand l'utilisateur termine la simulation via le bouton
        self.on_finish = None

    def _recompute_layout(self, win_w: int, win_h: int) -> None:
        """Recompute layout rectangles and grid origin based on window size."""
        # Left content area width (for grid): exclude padding and right log panel
        content_w = win_w - 2 * self.PADDING - self.LOG_PANEL_W
        content_h = win_h - 3 * self.PADDING - self.BOTTOM_BAR_H

        # Center grid within left content area
        grid_x = self.PADDING + max(0, (content_w - self.grid_width) // 2)
        grid_y = self.PADDING + max(0, (content_h - self.grid_height) // 2)
        self.grid_origin: tuple[int, int] = (grid_x, grid_y)

        # Bottom bar spans full width (minus side paddings)
        self.bottom_bar_rect: pygame.Rect = pygame.Rect(
            self.PADDING,
            win_h - self.PADDING - self.BOTTOM_BAR_H,
            win_w - 2 * self.PADDING,
            self.BOTTOM_BAR_H,
        )

        # Right logs panel rect
        self.logs_rect: pygame.Rect = pygame.Rect(
            win_w - self.PADDING - self.LOG_PANEL_W,
            self.PADDING,
            self.LOG_PANEL_W,
            win_h - 3 * self.PADDING - self.BOTTOM_BAR_H,
        )

    def draw_grid(self, algorithm: Algorithm) -> None:
        """Draw the map cells colored by idleness and overlay agent positions.

        Args:
            algorithm: The running algorithm instance providing idleness and agents.
        """
        idleness: np.ndarray = algorithm.idleness
        max_idle: float = float(idleness.max()) if idleness.size > 0 else 0.0

        # use_pheromone: bool = algorithm.__class__.__name__ == "AntColony" and hasattr(algorithm, "pheromone")
        # if use_pheromone:
        #     pheromone: np.ndarray = algorithm.pheromone  # type: ignore[attr-defined]
        #     max_pher: float = float(pheromone.max()) if pheromone.size > 0 else 0.0

        base_x = self.grid_origin[0]
        base_y = self.grid_origin[1]
        for x in range(self.map.shape[0]):
            for y in range(self.map.shape[1]):
                

                if self.map[x, y] == 1:  # Obstacle
                    idleness_color = self.utils.BLACK
                else: # Free cell
                    cell_idle: float = float(idleness[x, y])
                    ratio = min(1.0, cell_idle / 10.0)

                    red = 255
                    green_blue = int(255 * (1 - ratio))
                    idleness_color = (red, green_blue, green_blue)

                pygame.draw.rect(
                    self.screen,
                    idleness_color,
                    [
                        base_x + (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN,
                        base_y + (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    ],
                )

                # Grid lines
                pygame.draw.rect(
                    self.screen,
                    (0, 0, 0),
                    [
                        base_x + (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN,
                        base_y + (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    ],
                    1
                )
                # if use_pheromone:
                #     cell_pher: float = float(pheromone[x, y])
                #     pher_ratio: float = (cell_pher / max_pher) if max_pher > 0 else 0.0
                #     pher_ratio = max(0.0, min(1.0, pher_ratio))
                #     blue_val: int = int(255 * pher_ratio)
                #     pheromone_color: tuple[int, int, int] = (0, 0, blue_val)
                #     pygame.draw.circle(
                #         self.screen,
                #         pheromone_color,
                #         [
                #             (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN + self.CELL_SIZE // 2,
                #             (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN + self.CELL_SIZE // 2,
                #         ],
                #         self.CELL_SIZE // 3,
                #     )

        # Agents
        for (ax, ay) in algorithm.agents:
            pygame.draw.circle(
                self.screen,
                self.utils.BLUE,
                [
                    base_x + (self.MARGIN + self.CELL_SIZE) * ay + self.MARGIN + self.CELL_SIZE // 2,
                    base_y + (self.MARGIN + self.CELL_SIZE) * ax + self.MARGIN + self.CELL_SIZE // 2,
                ],
                self.CELL_SIZE // 3,
            )

    def display_timer(self, elapsed_time: float) -> None:
        """Render and display the simulated elapsed time in the bottom bar.

        Args:
            elapsed_time: Wall-clock seconds since visualization start.
        """
        # Show simulated time (scaled by sim_speed_tps) in mm:ss
        sim_secs = int(self.sim_time)
        mm = sim_secs // 60
        ss = sim_secs % 60
        timer_text = self.font.render(f"Temps (x{self.speed_multiplier:.1f}): {mm:02d}:{ss:02d}", True, self.utils.BLACK)
        # Positionné dans la barre inférieure (aligné à gauche, centré verticalement)
        x = self.bottom_bar_rect.left + 10
        y = self.bottom_bar_rect.centery - timer_text.get_height() // 2
        self.screen.blit(timer_text, (x, y))

    def update_visuals(self, algorithm: Algorithm) -> None:
        """Redraw the entire screen: grid centered, logs, timer, buttons, then flip."""
        self.screen.fill((255, 255, 255))
        self.draw_grid(algorithm)
        self.display_timer(time.time() - self.start_time)
        self.display_logs_panel(algorithm)
        self.display_buttons()
        pygame.display.flip()

    def advance_sim_time_per_tick(self) -> None:
        """Advance simulated time by a fixed amount per tick based on base speed.

        With increment 1/base_speed, the simulated seconds per real second
        become sim_speed_tps/base_speed when running one tick per frame.
        """
        """Avancer le temps simulé d'une seconde par 'tick' logique.

        Dans notre schéma actuel, un 'tick' correspond à 1 seconde simulée,
        déclenchée lorsque l'accumulateur atteint 1.0 dans SimPage.update().
        """
        self.sim_time += 1.0

    def terminate(self) -> None:
        """Terminate pygame and exit the process cleanly."""
        pygame.quit()
        sys.exit()

    def display_buttons(self) -> None:
        """Create and draw speed controls, Reset and Finish buttons in the bottom bar."""
        BUTTON_HEIGHT: int = 40
        BUTTON_WIDTH: int = 150
        GAP: int = 10
        SMALL_W: int = 48

        # Finish button (right)
        qx = self.bottom_bar_rect.right - BUTTON_WIDTH - GAP
        by = self.bottom_bar_rect.centery - BUTTON_HEIGHT // 2
        self.quit_button = Button(
            qx,
            by,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Terminer",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.quit_button.draw(self.screen)

        # Reset button (left of quit)
        rx = qx - BUTTON_WIDTH - GAP
        self.reset_button = Button(
            rx,
            by,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Reset",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.reset_button.draw(self.screen)

        # Speed controls group placed to the left of Reset button
        label_font = pygame.font.SysFont(None, 28)
        label = label_font.render(f"Vitesse: {self.speed_multiplier:.1f}", True, self.utils.BLACK)
        group_width = SMALL_W + 8 + SMALL_W + 16 + label.get_width()
        sx = rx - GAP - group_width

        self.speed_dec_button = Button(
            sx,
            by,
            SMALL_W,
            BUTTON_HEIGHT,
            "-",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.speed_dec_button.draw(self.screen)

        self.speed_inc_button = Button(
            sx + SMALL_W + 8,
            by,
            SMALL_W,
            BUTTON_HEIGHT,
            "+",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.speed_inc_button.draw(self.screen)

        # Speed label showing current ticks per second
        self.screen.blit(label, (sx + 2 * SMALL_W + 16, by + (BUTTON_HEIGHT - label.get_height()) // 2))

    def display_logs_panel(self, algorithm: Algorithm) -> None:
        """Draw the event logs panel on the right side with colored entries."""
        # Panel background and border
        pygame.draw.rect(self.screen, self.utils.LIGHT_GRAY, self.logs_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.utils.BLACK, self.logs_rect, 2, border_radius=6)

        # Title
        title_font = pygame.font.SysFont(None, 28)
        title_surf = title_font.render("Événements", True, self.utils.BLACK)
        self.screen.blit(title_surf, (self.logs_rect.left + 10, self.logs_rect.top + 8))

        # Entries
        log_font = pygame.font.SysFont(None, 24)
        # Last N events
        history: List[Dict[str, Any]] = getattr(algorithm, "event_history", [])
        lines = history
        y = self.logs_rect.top + 8 + title_surf.get_height() + 6
        for ev in lines:
            magnitude = float(ev.get("magnitude", 0.0))
            color = self.utils.RED if magnitude > 0 else self.utils.BLUE
            step = ev.get("step", 0)
            etype = str(ev.get("type", "?")).replace("EventType.", "")
            pos = ev.get("position", ("-", "-"))
            text = f"t{step}: {etype} ({magnitude:+.1f}) @ {pos}"
            surf = log_font.render(text, True, color)
            if y + surf.get_height() <= self.logs_rect.bottom - 8:
                self.screen.blit(surf, (self.logs_rect.left + 10, y))
                y += surf.get_height() + 4
            else:
                break

    def buttons_event(self, event: pygame.event.Event, algorithm: Algorithm) -> None:
        """Handle hover and clicks for Reset, Finish and Speed buttons."""
        # Window resize handling
        if event.type == pygame.VIDEORESIZE:
            new_size = (event.w, event.h)
            self.screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
            self._recompute_layout(event.w, event.h)
            return

        # Hover cursor for all buttons
        for btn in (self.reset_button, self.quit_button, self.speed_dec_button, self.speed_inc_button):
            if btn:
                btn.hover_property(event)

        # Click handling
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.reset_button and self.reset_button.is_clicked(mouse_pos, event):
                self.reset_simulation(algorithm)
            if self.quit_button and self.quit_button.is_clicked(mouse_pos, event):
                # Appel du callback fourni par la page de simulation
                if callable(self.on_finish):
                    self.on_finish()
                else:
                    # Par sécurité, on termine l'application si aucun callback n'est défini
                    self.terminate()
            if self.speed_dec_button and self.speed_dec_button.is_clicked(mouse_pos, event):
                self._adjust_speed(-1.0, algorithm)
            if self.speed_inc_button and self.speed_inc_button.is_clicked(mouse_pos, event):
                self._adjust_speed(+1.0, algorithm)

    def reset_simulation(self, algorithm: Algorithm) -> None:
        """Reset algorithm state, timer, and clear logs."""
        if hasattr(algorithm, "reset"):
            algorithm.reset()
        self.start_time = time.time()
        self.sim_time = 0.0

    def _adjust_speed(self, delta: float, algorithm: Algorithm) -> None:
        """Increment/decrement simulation speed with clamping, update algorithm.

        Args:
            delta: Signed increment in ticks per second (e.g., -1 or +1).
            algorithm: Algorithm instance to synchronize speed-dependent params.
        """
        new_speed = max(self.min_speed, min(self.max_speed, self.speed_multiplier + delta))
        # Snap to 0.5 steps for finer control
        new_speed = round(new_speed * 2) / 2.0
        self.speed_multiplier = new_speed
        