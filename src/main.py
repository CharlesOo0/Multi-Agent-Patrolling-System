import pygame
import time
import numpy as np
from aco import PatrollingACO
from visualization import Visualization

def main():
    # Constants
    DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    
    WINDOW_SIZE = (900, 900)
    TARGET_STEPS = 900  # 1 minute 30 seconds at 10 steps per second

    map_size = (20, 20)

    # Initialize Visualization
    viz = Visualization(DISPLAYSURF.get_size(), map_size)

    # Initialize ACO
    num_agents = 7
    aco = PatrollingACO(map_size, num_agents, evaporation_rate=0.1, alpha=1, beta=2)

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

        # Print average idleness after 1 minute 30 seconds
        if aco.step_count == TARGET_STEPS:
            avg_idleness = np.mean(aco.idleness)
            print(f"Average idleness after 1 minute 30 seconds: {avg_idleness:.2f}")
    
        for event in pygame.event.get():
            viz.buttons_event(event)
            if event.type == pygame.QUIT:
                running = False
    
    viz.terminate()

if __name__ == "__main__":
    main()
