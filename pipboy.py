import pygame
import sys
import time
import random
from stats import StatPage
from data import DataPage
from map import MapPage
from radio import RadioPage

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 320
FPS = 30

# Colors
BLACK = (0, 0, 0)
BRIGHT = (0, 230, 0)
LIGHT = (0, 170, 0)
MID = (0, 120, 0)
DIM = (0, 70, 0)
DARK = (0, 40, 0)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pip-Boy Interface")

# Font setup
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Pages
pages = ["STAT", "DATA", "MAP", "RADIO"]
page_objects = [StatPage(), DataPage(), MapPage(), RadioPage()]
current_page = 0

# Overlay class
class Overlay:
    def __init__(self, image_path, width, height):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
    
    def render(self, surface):
        temp_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
        temp_surface.blit(self.image, (0, 0))
        surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_ADD)

# Scanline class
class Scanline:
    def __init__(self, image_path, width, height, speed=5, delay=2):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.speed = speed
        self.delay = delay
        self.last_move_time = time.time()
        self.rect.y = -height

    def update(self):
        current_time = time.time()
        if current_time - self.last_move_time > self.delay:
            self.rect.y += self.speed
            if self.rect.y >= SCREEN_HEIGHT:
                self.rect.y = -self.rect.height
                self.last_move_time = current_time

    def render(self, surface):
        surface.blit(self.image, self.rect, special_flags=pygame.BLEND_ADD)

# Initialize overlay
overlay = Overlay('images/overlay.png', SCREEN_WIDTH, SCREEN_HEIGHT)

# Initialize scanline
scanline = Scanline('images/scanline.png', SCREEN_WIDTH, 60, speed=2, delay=1.05)  # Increased height to 20

def draw_centered_text(text, font, color, surface, rect):
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect(center=(rect.centerx, rect.centery))
    surface.blit(textobj, textrect)

def draw_tabs(surface):
    tab_width = SCREEN_WIDTH // len(pages)
    for i, page in enumerate(pages):
        tab_color = BRIGHT if i == current_page else BLACK
        text_color = BLACK if i == current_page else BRIGHT
        rect = pygame.Rect(i * tab_width, 0, tab_width, 50)
        pygame.draw.rect(surface, tab_color, rect)
        draw_centered_text(page, font, text_color, surface, rect)

def draw_interface(surface):
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    temp_surface.fill((0, 0, 0, 0))  # Fully transparent background
    
    draw_tabs(temp_surface)
    pygame.draw.line(temp_surface, BRIGHT, (0, 50), (SCREEN_WIDTH, 50), 2)
    current_page_object = page_objects[current_page]
    current_page_object.draw(temp_surface, small_font, BRIGHT)
    
    # Blit the UI elements onto the main surface
    surface.blit(temp_surface, (0, 0))

def main():
    global current_page
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_page = (current_page - 1) % len(pages)
                elif event.key == pygame.K_RIGHT:
                    current_page = (current_page + 1) % len(pages)

        # Draw the UI elements
        screen.fill(BLACK)  # Fill screen with black before drawing UI elements
        draw_interface(screen)

        # Apply overlay (scanlines)
        overlay.render(screen)

        # Update and render scanline
        scanline.update()
        scanline.render(screen)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()