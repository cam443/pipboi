import pygame
import pygame.freetype
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
from config import *

# Initialize Pygame
pygame.init()

# Screen setup
screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
pygame.display.set_caption("Pip-Boy Interface")

# Font setup
font = FreeTechMono[30]
small_font = FreeTechMono[24]

# Pages
pages = ["STAT", "RADIO", "MAP", "DATA"]
page_objects = [StatPage(), RadioPage(), MapPage(), DataPage()]
current_page = 0

# Initialize overlay
overlay = Overlay('images/overlay.png', SCREEN_WIDTH, SCREEN_HEIGHT, strength=1, scale_factor=2)
underlay = Overlay('images/overlay_dark.png', SCREEN_WIDTH, SCREEN_HEIGHT, strength=1, scale_factor=2)

# Initialize scanline
scanline = Scanline('images/scanline.png', SCREEN_WIDTH, 60, SCREEN_HEIGHT, speed=3, delay=1.05)

def draw_centered_text(text, font_size, color, surface, rect, font_type='RobotoB'):
    font = globals()[font_type][font_size]
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(rect.centerx, rect.centery))
    surface.blit(textobj, textrect)

def draw_tabs(surface):
    tab_width = SCREEN_WIDTH // len(pages)
    for i, page in enumerate(pages):
        tab_color = BRIGHT if i == current_page else BLACK
        text_color = BLACK if i == current_page else BRIGHT
        rect = pygame.Rect(i * tab_width, 0, tab_width, 50)
        pygame.draw.rect(surface, tab_color, rect)
        draw_centered_text(page, 30, text_color, surface, rect, 'RobotoB')

def draw_interface(surface):
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    temp_surface.fill((0, 0, 0, 0))  # Fully transparent background
    
    draw_tabs(temp_surface)
    pygame.draw.line(temp_surface, BRIGHT, (0, 50), (SCREEN_WIDTH, 50), 2)
    current_page_object = page_objects[current_page]
    current_page_object.draw(temp_surface, RobotoR[24], BRIGHT)
    
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

        # Create a canvas to render the game screen
        canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        canvas.fill(BLACK)  # Fill canvas with black before drawing UI elements

        # Render the overlay on the canvas first (as a background)
        overlay.render(canvas)

        # Draw the UI elements on the game screen
        game_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_screen.fill(BLACK)
        draw_interface(game_screen)

        # Apply overlay (scanlines) on the game screen
        overlay.render(game_screen)

        # Update and render scanline on the game screen
        scanline.update()
        scanline.render(game_screen)

        # Apply CRT shader on the game screen
        crt_screen = crt_shader.apply(game_screen.copy())

        # Blit the CRT screen onto the canvas with the offset
        canvas.blit(crt_screen, (OFFSET_X, OFFSET_Y))

        # Display the canvas
        screen.blit(canvas, (0, 0))
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()