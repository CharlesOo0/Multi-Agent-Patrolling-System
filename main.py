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

# Constants
CELL_SIZE = 20
MARGIN = 2
WINDOW_SIZE = (600, 600)
NOISE_LEVEL = 0.01
INITIAL_EVAPORATION_RATE = 0.1
EVAPORATION_INCREASE = 0.0005
TABU_TENURE = 5
ELITISM_FACTOR = 2.0
RANDOM_MOVE_PROB = 0.05  # Probability of making a random move

class PatrollingACO:
    def __init__(self, map_size, num_agents, evaporation_rate=INITIAL_EVAPORATION_RATE, alpha=1, beta=2):
        self.map_size = map_size
        self.num_agents = num_agents
        self.evaporation_rate = evaporation_rate
        self.alpha = alpha  # Pheromone importance
        self.beta = beta    # Idleness importance (increased to prioritize high-idleness areas)
        self.pheromone = np.ones(map_size)
        self.idleness = np.zeros(map_size)
        self.agents = [(random.randint(0, map_size[0]-1), random.randint(0, map_size[1]-1)) for _ in range(num_agents)]
        self.tabu_lists = [[] for _ in range(num_agents)]
        self.step_count = 0

    def update_idleness(self):
        self.idleness += 0.1  # Increase idleness for all cells

    def update_pheromone(self):
        # Dynamic evaporation rate
        self.evaporation_rate = min(self.evaporation_rate + EVAPORATION_INCREASE, 0.5)
        self.pheromone *= (1 - self.evaporation_rate)
        # Add small random noise
        self.pheromone += np.random.uniform(0, NOISE_LEVEL, self.pheromone.shape)

    def move_agents(self):
        for i, (x, y) in enumerate(self.agents):
            # Random move with small probability
            if random.random() < RANDOM_MOVE_PROB:
                neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
                neighbors = [(nx, ny) for nx, ny in neighbors
                             if 0 <= nx < self.map_size[0] and 0 <= ny < self.map_size[1]]
                if neighbors:
                    new_pos = random.choice(neighbors)
                    self.agents[i] = new_pos
                    self.pheromone[new_pos] += 1
                    self.idleness[new_pos] = 0
                    # Update tabu list
                    self.tabu_lists[i].append(new_pos)
                    if len(self.tabu_lists[i]) > TABU_TENURE:
                        self.tabu_lists[i].pop(0)
                continue

            # Normal movement based on pheromone and idleness
            neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]]
            neighbors = [(nx, ny) for nx, ny in neighbors
                         if 0 <= nx < self.map_size[0] and 0 <= ny < self.map_size[1]
                         and (nx, ny) not in self.tabu_lists[i]]

            if not neighbors:
                self.tabu_lists[i] = []
                continue

            probs = []
            for nx, ny in neighbors:
                pheromone_effect = self.pheromone[nx, ny] ** self.alpha
                idleness_effect = (self.idleness[nx, ny] + 1) ** self.beta  # Prioritize high-idleness areas
                probs.append(pheromone_effect * idleness_effect)

            total_prob = sum(probs)
            if total_prob == 0:
                probs = [1/len(probs)] * len(probs)
            else:
                probs = [p / total_prob for p in probs]

            new_pos = random.choices(neighbors, weights=probs, k=1)[0]
            self.agents[i] = new_pos

            # Elitism: deposit extra pheromone if this move significantly reduces idleness
            if self.idleness[new_pos] > np.mean(self.idleness):
                self.pheromone[new_pos] += ELITISM_FACTOR
            else:
                self.pheromone[new_pos] += 1

            self.idleness[new_pos] = 0

            # Update tabu list
            self.tabu_lists[i].append(new_pos)
            if len(self.tabu_lists[i]) > TABU_TENURE:
                self.tabu_lists[i].pop(0)

    def run_step(self):
        self.update_idleness()
        self.move_agents()
        self.update_pheromone()
        self.step_count += 1

def draw_grid(screen, aco):
    for x in range(aco.map_size[0]):
        for y in range(aco.map_size[1]):
            idleness_color = (min(aco.idleness[x, y] * 10, 255), 0, 0)
            pygame.draw.rect(screen, idleness_color, [(MARGIN + CELL_SIZE) * y + MARGIN, (MARGIN + CELL_SIZE) * x + MARGIN, CELL_SIZE, CELL_SIZE])
            pheromone_color = (0, 0, min(aco.pheromone[x, y] * 10, 255))
            pygame.draw.circle(screen, pheromone_color, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 3)

    for (x, y) in aco.agents:
        pygame.draw.circle(screen, GREEN, [(MARGIN + CELL_SIZE) * y + MARGIN + CELL_SIZE // 2, (MARGIN + CELL_SIZE) * x + MARGIN + CELL_SIZE // 2], CELL_SIZE // 2)

def main():
    map_size = (20, 20)
    num_agents = 5
    aco = PatrollingACO(map_size, num_agents, evaporation_rate=INITIAL_EVAPORATION_RATE, alpha=1, beta=2)

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
        clock.tick(10)

if __name__ == "__main__":
    main()
