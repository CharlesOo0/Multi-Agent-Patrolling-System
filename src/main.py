import pygame
import time
import numpy as np
from algorithm import AntColony, Heuristic
from visualization import Visualization
from maps.maps import DUST2

"""Entry point for running the multi-agent patrolling visualization demo.

This module initializes a map, an algorithm (Heuristic or ACO), and a Pygame
window to render agent movement and idleness heatmap in real time.
"""

def main():
    """Run the main application loop: init, step algorithm, and render frames."""

    # Parameters
    SIMULATION_SPEED = 10  # Steps per second

    # Initialize Visualization
    DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    viz = Visualization(DISPLAYSURF.get_size(), DUST2)

    # Initialize Algorithm
    num_agents = 4
    # algorithm = AntColony(MAP, num_agents, evaporation_rate=0.1, alpha=1, beta=2)
    algorithm = Heuristic(DUST2, num_agents, simulation_speed=SIMULATION_SPEED, event_spawn_prob=0.1)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                viz.buttons_event(event, algorithm)

        algorithm.run_step()
        viz.update_visuals(algorithm)

        viz.clock.tick(SIMULATION_SPEED) # Control the frame rate

    viz.terminate()

if __name__ == "__main__":
    main()