import sys
import pygame
from .utils import viz_utils

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        """Create a clickable UI button.

        Args:
            x: X-coordinate of the top-left corner.
            y: Y-coordinate of the top-left corner.
            width: Button width in pixels.
            height: Button height in pixels.
            text: Label to display.
            color: Default background color.
            hover_color: Background color when hovered.
        """
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
        """Draw the button on the given surface with appropriate hover state."""
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
        """Update hover state based on current mouse position.

        Args:
            pos: Current mouse position tuple (x, y).

        Returns:
            True if the cursor is inside the button rect, else False.
        """
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        """Return True if the left mouse button clicked inside the button.

        Args:
            pos: Mouse position tuple (x, y) at click time.
            event: Pygame event object.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False
    
    def quit_button_event(self,event):
        """Handle events for a Quit button: hover cursor and exit on click."""
        self.hover_property(event)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.is_clicked(mouse_pos, event):
                pygame.quit()
                sys.exit()
                
    def hover_property(self,event):
        """Change the mouse cursor depending on hover state."""
        if self.check_hover(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            
        if not self.check_hover(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)