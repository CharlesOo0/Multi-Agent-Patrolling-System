import pygame
import time

from ui.routes.base import Router
from ui import HomePage, SimPage, SettingsPage, StatsPage,MapEditorPage


def run_with_router():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
    pygame.display.set_caption("AI50 - Multi-agents patrolling simulation")
    clock = pygame.time.Clock()

    router = Router(initial="home")

    def go_home():
        router.navigate("home")

    # Stats page instance is created first to be able to inject results later
    stats_page = StatsPage(go_home=go_home, go_sim=lambda: router.navigate("sim"))

    def go_sim():
        router.navigate("sim")

    def go_settings():
        router.navigate("settings")

    def go_map_editor():
        router.navigate("map_editor")

    def go_stats(results: dict) -> None:
        stats_page.set_results(results)
        router.navigate("stats")

    router.register("home", HomePage(go_to_sim=go_sim, go_to_settings=go_settings, go_to_map_editor=go_map_editor))
    router.register("sim", SimPage(go_home=go_home, go_stats=go_stats))
    router.register("settings", SettingsPage(go_back=go_home))
    router.register("map_editor", MapEditorPage(go_back=go_home))
    router.register("stats", stats_page)

    router.start()

    running = True
    last = time.time()
    while running:
        now = time.time()
        dt = now - last
        last = now
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            router.handle_event(event)

        router.update(dt)
        screen.fill((255, 255, 255))
        router.render(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run_with_router()
