import pygame
import sys
import time
from typing import Tuple
from .button import Button
from .utils import viz_utils
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

        rows, cols = self.map.shape
        # Dimensions of the grid in pixels
        self.grid_width: int = cols * (self.CELL_SIZE + self.MARGIN) + self.MARGIN
        self.grid_height: int = rows * (self.CELL_SIZE + self.MARGIN) + self.MARGIN

        # Minimum window size to contain grid + bottom bar
        min_w = self.grid_width + self.PADDING * 2
        min_h = self.grid_height + self.BOTTOM_BAR_H + self.PADDING * 3
        win_w = max(WINDOW_SIZE[0], min_w)
        win_h = max(WINDOW_SIZE[1], min_h)

        self.screen: pygame.Surface = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption("Multi-Agent Patrolling with algorithm (2D Grid)")
        self.font: pygame.font.Font = pygame.font.SysFont(None, 36)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.start_time: float = time.time()

        # Origin of the grid (top-left corner)
        self.grid_origin: tuple[int, int] = (self.PADDING, self.PADDING)

        # Rect of the bottom bar (below the grid)
        self.bottom_bar_rect: pygame.Rect = pygame.Rect(
            self.PADDING,
            self.grid_origin[1] + self.grid_height + self.PADDING,
            self.grid_width,
            self.BOTTOM_BAR_H,
        )

        self.quit_button: Button | None = None

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
                        (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN,
                        (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    ],
                )

                # Grid lines
                pygame.draw.rect(
                    self.screen,
                    (0, 0, 0),
                    [
                        (self.MARGIN + self.CELL_SIZE) * y + self.MARGIN,
                        (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN,
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
                    (self.MARGIN + self.CELL_SIZE) * ay + self.MARGIN + self.CELL_SIZE // 2,
                    (self.MARGIN + self.CELL_SIZE) * ax + self.MARGIN + self.CELL_SIZE // 2,
                ],
                self.CELL_SIZE // 3,
            )

    def display_timer(self, elapsed_time: float) -> None:
        """Render and display the elapsed time in the bottom bar.

        Args:
            elapsed_time: Time in seconds since visualization start.
        """
        timer_text = self.font.render(f"Time: {elapsed_time:.1f}s", True, self.utils.BLACK)
        # Positionné dans la barre inférieure (aligné à gauche, centré verticalement)
        x = self.bottom_bar_rect.left + 10
        y = self.bottom_bar_rect.centery - timer_text.get_height() // 2
        self.screen.blit(timer_text, (x, y))

    def update_visuals(self, algorithm: Algorithm) -> None:
        """Redraw the entire screen: grid, timer, and interactive button, then flip."""
        self.screen.fill((255, 255, 255))
        self.draw_grid(algorithm)
        self.display_timer(time.time() - self.start_time)
        self.display_button()
        pygame.display.flip()

    def terminate(self) -> None:
        """Terminate pygame and exit the process cleanly."""
        pygame.quit()
        sys.exit()

    def display_button(self) -> None:
        """Create and draw the bottom-bar Quit button."""
        BUTTON_HEIGHT: int = 40
        BUTTON_WIDTH: int = 150

        # Bouton aligné à droite dans la barre inférieure
        x = self.bottom_bar_rect.right - BUTTON_WIDTH - 10
        y = self.bottom_bar_rect.centery - BUTTON_HEIGHT // 2

        self.quit_button = Button(
            x,
            y,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Quitter",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.quit_button.draw(self.screen)

    def buttons_event(self, event: pygame.event.Event) -> None:
        """Dispatch pygame events to on-screen buttons (e.g., Quit)."""
        if self.quit_button:
            self.quit_button.quit_button_event(event)