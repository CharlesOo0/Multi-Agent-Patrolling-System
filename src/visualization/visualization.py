import pygame
import sys
import time
from .button import Button
from.utils import viz_utils

class Visualization:
    def __init__(self, WINDOW_SIZE, map_size):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Multi-Agent Patrolling with ACO (2D Grid)")
        self.font = pygame.font.SysFont(None, 36)
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        # Colors
        self.utils = viz_utils()
        button = Button(300, 250, 200, 50, "Quitter", self.utils.GRAY, self.utils.LIGHT_GRAY)
        button.draw(self.screen)
        pygame.display.flip()
        # Constants
        self.CELL_SIZE = 20
        self.MARGIN = 2
        self.map_size = map_size

    def draw_grid(self, aco):
        for x in range(aco.map_size[0]):
            for y in range(aco.map_size[1]):
                idleness_color = (min(aco.idleness[x, y] * 10, 255), 0, 0)
                pygame.draw.rect(self.screen, idleness_color, [(self.MARGIN + self.CELL_SIZE) * y + self.MARGIN, (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN, self.CELL_SIZE, self.CELL_SIZE])
                pheromone_color = (0, 0, min(aco.pheromone[x, y] * 10, 255))
                pygame.draw.circle(self.screen, pheromone_color, [(self.MARGIN + self.CELL_SIZE) * y + self.MARGIN + self.CELL_SIZE // 2, (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN + self.CELL_SIZE // 2], self.CELL_SIZE // 3)

        for (x, y) in aco.agents:
            pygame.draw.circle(self.screen, self.utils.GREEN, [(self.MARGIN + self.CELL_SIZE) * y + self.MARGIN + self.CELL_SIZE // 2, (self.MARGIN + self.CELL_SIZE) * x + self.MARGIN + self.CELL_SIZE // 2], self.CELL_SIZE // 2)

    def display_timer(self, elapsed_time):
        timer_text = self.font.render(f"Time: {elapsed_time:.1f}s", True, self.utils.BLACK)
        self.screen.blit(timer_text, (10, 450))

    def update_visuals(self, aco):
        self.screen.fill((255, 255, 255))
        self.draw_grid(aco)
        self.display_timer(time.time() - self.start_time)
        self.display_button()
        pygame.display.flip()
    def terminate(self):
        pygame.quit()
        sys.exit()
        
    def display_button(self):
        BUTTON_HEIGHT = 40
        BUTTON_WIDTH = 150
        self.quit_button = Button(self.map_size[0] * self.CELL_SIZE + 40 - BUTTON_WIDTH, self.map_size[1] * self.CELL_SIZE + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT, "Quitter", self.utils.GRAY, self.utils.LIGHT_GRAY)
        self.quit_button.draw(self.screen)
        
    def buttons_event(self,event):
        # Liste des différents boutons
        self.quit_button.quit_button_event(event)        