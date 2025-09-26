import pygame
import sys

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Constants
CELL_SIZE = 20
MARGIN = 2

def draw_grid(screen, aco, window_size):
    for x in range(aco.map_size[0]):
        for y in range(aco.map_size[1]):
            idleness_color = (min(aco.idleness[x, y] * 10, 255), 0, 0)
            pygame.draw.rect(screen, idleness_color, [(MARGIN + CELL_SIZE) * y + MARGIN, (MARGIN + CELL_SIZE) * x + MARGIN, CELL_SIZE, CELL_SIZE])
            pheromone_color = (0, 0, min(aco.pheromone[x, y] * 10, 255))
            pygame.draw.circle(screen, pheromone_color, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 3)

    for (x, y) in aco.agents:
        pygame.draw.circle(screen, GREEN, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 2)

def display_timer(screen, elapsed_time, font):
    timer_text = font.render(f"Time: {elapsed_time:.1f}s", True, BLACK)
    screen.blit(timer_text, (10, 450))
