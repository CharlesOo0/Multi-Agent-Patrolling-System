import numpy as np
import random
import pygame
import sys

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Constants
CELL_SIZE = 20
MARGIN = 2
WINDOW_SIZE = (600, 600)
NOISE_LEVEL = 0.01  # Small noise to break ties and encourage exploration
TABU_TENURE = 3     # Number of steps an agent cannot revisit a cell

class PatrollingACO:
    def __init__(self, map_size, num_agents, evaporation_rate=0.1, alpha=1, beta=1):
        self.map_size = map_size  # (rows, cols)
        self.num_agents = num_agents
        self.evaporation_rate = evaporation_rate
        self.alpha = alpha
        self.beta = beta
        self.pheromone = np.ones(map_size)
        self.idleness = np.zeros(map_size)
        self.agents = [(random.randint(0, map_size[0]-1), random.randint(0, map_size[1]-1)) for _ in range(num_agents)]
        self.tabu_lists = [[] for _ in range(num_agents)]  # Tabu list for each agent

    def update_idleness(self):
        self.idleness += 0.1  # Increase idleness for all cells

    def update_pheromone(self):
        self.pheromone *= (1 - self.evaporation_rate)  # Evaporate pheromone
        # Add small random noise to pheromone
        self.pheromone += np.random.uniform(0, NOISE_LEVEL, self.pheromone.shape)

    def move_agents(self):
        for i, (x, y) in enumerate(self.agents):
            # Get neighboring cells (4-directional movement)
            neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
            # Filter out invalid positions and tabu cells
            neighbors = [(nx, ny) for nx, ny in neighbors
                         if 0 <= nx < self.map_size[0] and 0 <= ny < self.map_size[1]
                         and (nx, ny) not in self.tabu_lists[i]]

            if not neighbors:
                # If no valid neighbors, clear tabu list for this agent
                self.tabu_lists[i] = []
                continue

            # Calculate probabilities for each neighbor
            probs = []
            for nx, ny in neighbors:
                pheromone_effect = self.pheromone[nx, ny] ** self.alpha
                idleness_effect = (1 / (self.idleness[nx, ny] + 1e-6)) ** self.beta
                probs.append(pheromone_effect * idleness_effect)

            # Normalize probabilities
            total_prob = sum(probs)
            if total_prob == 0:
                probs = [1/len(probs)] * len(probs)  # Uniform distribution if all probabilities are zero
            else:
                probs = [p / total_prob for p in probs]

            # Probabilistic selection
            new_pos = random.choices(neighbors, weights=probs, k=1)[0]
            self.agents[i] = new_pos
            self.pheromone[new_pos] += 1
            self.idleness[new_pos] = 0

            # Update tabu list
            self.tabu_lists[i].append(new_pos)
            if len(self.tabu_lists[i]) > TABU_TENURE:
                self.tabu_lists[i].pop(0)  # Remove oldest entry

    def run_step(self):
        self.update_idleness()
        self.move_agents()
        self.update_pheromone()

def draw_grid(screen, aco):
    for x in range(aco.map_size[0]):
        for y in range(aco.map_size[1]):
            # Draw idleness as background color
            idleness_color = (min(aco.idleness[x, y] * 10, 255), 0, 0)
            pygame.draw.rect(screen, idleness_color, [(MARGIN + CELL_SIZE) * y + MARGIN, (MARGIN + CELL_SIZE) * x + MARGIN, CELL_SIZE, CELL_SIZE])
            # Draw pheromone as a circle
            pheromone_color = (0, 0, min(aco.pheromone[x, y] * 10, 255))
            pygame.draw.circle(screen, pheromone_color, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 3)

    # Draw agents
    for (x, y) in aco.agents:
        pygame.draw.circle(screen, GREEN, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 2)

def main():
    map_size = (20, 20)  # (rows, cols)
    num_agents = 5
    aco = PatrollingACO(map_size, num_agents, evaporation_rate=0.1, alpha=1, beta=1)

    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Multi-Agent Patrolling with ACO (2D Grid)")

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        aco.run_step()
        screen.fill(WHITE)
        draw_grid(screen, aco)
        pygame.display.flip()
        clock.tick(10)  # Control the speed of the simulation

if __name__ == "__main__":
    main()
