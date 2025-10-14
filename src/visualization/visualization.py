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
        """Initialise la fenêtre de visualisation."""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Multi-Agent Patrolling with algorithm (2D Grid)")
        self.font: pygame.font.Font = pygame.font.SysFont(None, 36)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.start_time: float = time.time()
        # Colors / utils
        self.utils: viz_utils = viz_utils()
        button = Button(300, 250, 200, 50, "Quitter", self.utils.GRAY, self.utils.LIGHT_GRAY)
        button.draw(self.screen)
        pygame.display.flip()
        # Constants
        self.CELL_SIZE: int = 20
        self.MARGIN: int = 2
        self.map: np.ndarray = map
        self.quit_button: Button | None = None

    def draw_grid(self, algorithm: Algorithm) -> None:
        idleness: np.ndarray = algorithm.idleness
        max_idle: float = float(idleness.max()) if idleness.size > 0 else 0.0

        # use_pheromone: bool = algorithm.__class__.__name__ == "AntColony" and hasattr(algorithm, "pheromone")
        # if use_pheromone:
        #     pheromone: np.ndarray = algorithm.pheromone  # type: ignore[attr-defined]
        #     max_pher: float = float(pheromone.max()) if pheromone.size > 0 else 0.0

        for x in range(self.map.shape[0]):
            for y in range(self.map.shape[1]):
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
                self.utils.GREEN,
                [
                    (self.MARGIN + self.CELL_SIZE) * ay + self.MARGIN + self.CELL_SIZE // 2,
                    (self.MARGIN + self.CELL_SIZE) * ax + self.MARGIN + self.CELL_SIZE // 2,
                ],
                self.CELL_SIZE // 2,
            )

    def display_timer(self, elapsed_time: float) -> None:
        timer_text = self.font.render(f"Time: {elapsed_time:.1f}s", True, self.utils.BLACK)
        self.screen.blit(timer_text, (10, 450))

    def update_visuals(self, algorithm: Algorithm) -> None:
        self.screen.fill((255, 255, 255))
        self.draw_grid(algorithm)
        self.display_timer(time.time() - self.start_time)
        self.display_button()
        pygame.display.flip()

    def terminate(self) -> None:
        pygame.quit()
        sys.exit()

    def display_button(self) -> None:
        BUTTON_HEIGHT: int = 40
        BUTTON_WIDTH: int = 150
        self.quit_button = Button(
            self.map.shape[0] * self.CELL_SIZE + 40 - BUTTON_WIDTH,
            self.map.shape[1] * self.CELL_SIZE + BUTTON_HEIGHT + 10,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Quitter",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self.quit_button.draw(self.screen)

    def buttons_event(self, event: pygame.event.Event) -> None:
        if self.quit_button:
            self.quit_button.quit_button_event(event)