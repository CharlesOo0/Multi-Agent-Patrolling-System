import sys
import pygame
from.utils import viz_utils

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.height = height
        self.width = width
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.utils = viz_utils()

    def draw(self, surface):
        # Draw button
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, self.utils.BLACK, self.rect, 2, border_radius=5)  # Border

        # Draw text
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(self.text, True, self.utils.BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False
    
    def quit_button_event(self,event):
        if self.check_hover(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            
        if not self.check_hover(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.is_clicked(mouse_pos, event):
                pygame.quit()
                sys.exit()