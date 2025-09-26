import pygame
import sys
import time
import numpy as np
from aco import PatrollingACO
from visualization import draw_grid, display_timer

def main():
    # Constants
    WINDOW_SIZE = (600, 600)
    TARGET_STEPS = 900  # 1 minute 30 seconds at 10 steps per second

    # Initialize ACO
    map_size = (20, 20)
    num_agents = 5
    aco = PatrollingACO(map_size, num_agents, evaporation_rate=0.1, alpha=1, beta=2)

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Multi-Agent Patrolling with ACO (2D Grid)")
    font = pygame.font.SysFont(None, 36)
    clock = pygame.time.Clock()
    start_time = time.time()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        aco.run_step()
        screen.fill((255, 255, 255))
        draw_grid(screen, aco, WINDOW_SIZE)

        # Display timer
        elapsed_time = time.time() - start_time
        display_timer(screen, elapsed_time, font)

        pygame.display.flip()
        clock.tick(10)  # 10 steps per second

        # Print average idleness after 1 minute 30 seconds
        if aco.step_count == TARGET_STEPS:
            avg_idleness = np.mean(aco.idleness)
            print(f"Average idleness after 1 minute 30 seconds: {avg_idleness:.2f}")

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
