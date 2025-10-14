import pygame
import time
import numpy as np
from algorithm import AntColony
from visualization import Visualization

def main():

    # Parameters
    MAP_SIZE = (20, 20)
    SPEED = 10  # Steps per second

    # Initialize Visualization
    DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    viz = Visualization(DISPLAYSURF.get_size(), MAP_SIZE)

    # Initialize ACO
    num_agents = 7
    aco = AntColony(MAP_SIZE, num_agents, evaporation_rate=0.1, alpha=1, beta=2)

    # Main loop
    running = True
    while running:
        aco.run_step()
        viz.update_visuals(aco)
        # Display timer
        elapsed_time = time.time() - viz.start_time
        viz.display_timer(elapsed_time)

        pygame.display.flip() # Update the full display
        viz.clock.tick(SPEED) # Control the frame rate

        for event in pygame.event.get():
            viz.buttons_event(event)
            if event.type == pygame.QUIT:
                running = False
    
    viz.terminate()

if __name__ == "__main__":
    main()