import pygame
import numpy as np
import sys
import time
import random
from stats import StatPage
from data import DataPage
from map import MapPage
from radio import RadioPage
from effects import CRTShader
from effects import Overlay
from effects import Scanline

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480 # 400, 320
FPS = 30
FULLSCREEN = False

# Colors
BLACK = (0, 0, 0)
BRIGHT = (0, 230, 0)
LIGHT = (0, 170, 0)
MID = (0, 120, 0)
DIM = (0, 70, 0)
DARK = (0, 40, 0)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
pygame.display.set_caption("Pip-Boy Interface")

# Font setup
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Pages
pages = ["STAT", "RADIO", "MAP", "DATA"]
page_objects = [StatPage(), RadioPage(), MapPage(), DataPage()]
current_page = 0

# Initialize overlay
overlay = Overlay('images/overlay.png', SCREEN_WIDTH, SCREEN_HEIGHT)

# Initialize scanline
scanline = Scanline('images/scanline.png', SCREEN_WIDTH, 60, SCREEN_HEIGHT, speed=2, delay=1.05)

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
    crt_shader = CRTShader((SCREEN_WIDTH, SCREEN_HEIGHT))
    
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

        # Apply CRT shader
        crt_screen = crt_shader.apply(screen.copy())
        
        # Display the CRT screen
        screen.blit(crt_screen, (0, 0))
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()