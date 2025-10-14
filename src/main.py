import pygame
import time
import numpy as np
from src.algorithm import *
from visualization import Visualization

def main():

    map_size = (20, 20)

    # Initialize Visualization
    DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    viz = Visualization(DISPLAYSURF.get_size(), map_size)

    # Initialize ACO
    num_agents = 7
    aco = AntColony(map_size, num_agents, evaporation_rate=0.1, alpha=1, beta=2)

    # Main loop
    running = True
    while running:
        aco.run_step()
        viz.update_visuals(aco)
        # Display timer
        elapsed_time = time.time() - viz.start_time
        viz.display_timer(elapsed_time)

        pygame.display.flip() # Update the full display
        viz.clock.tick(10)  # 10 steps per second

        for event in pygame.event.get():
            viz.buttons_event(event)
            if event.type == pygame.QUIT:
                running = False
    
    viz.terminate()

if __name__ == "__main__":
    main()