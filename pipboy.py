import pygame
import pygame.freetype
import numpy as np
import sys
import time
import random
import os
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
pygame.mixer.init()

# Detect if running on a Raspberry Pi
PI = False
if os.name == "posix":
    PI = True
else:
    PI - False

# Screen setup
screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))

if not PI:
    screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

pygame.display.set_caption("Pip-Boy Interface")

# Font setup
font = FreeTechMono[30]
small_font = FreeTechMono[18]

# Pages
pages = ["STAT", "RADIO", "MAP", "DATA"]
page_objects = [
    StatPage(),
    RadioPage(),
    MapPage(WIDTH, HEIGHT, MAP_FOCUS, MAP_ZOOM, MAP_TYPE, API_KEY),
    DataPage()
]
current_page = 0

# Initialize overlay
overlay = Overlay('images/overlay.png', SCREEN_WIDTH, SCREEN_HEIGHT, strength=1, scale_factor=2)
underlay = Overlay('images/overlay_dark.png', SCREEN_WIDTH, SCREEN_HEIGHT, strength=1, scale_factor=2)

# Initialize scanline
scanline = Scanline('images/scanline.png', SCREEN_WIDTH, 60, SCREEN_HEIGHT, speed=1, delay=1.05)

# MOUSE DEBUG
def draw_mouse_position(surface, font, color):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    adjusted_x = mouse_x - OFFSET_X
    adjusted_y = mouse_y - OFFSET_Y
    pos_text = f"X: {adjusted_x}, Y: {adjusted_y}"
    text_surface, _ = small_font.render(pos_text, color)
    surface.blit(text_surface, (10, 10))  # Position the text at the top-left corner
# END MOUSE DEBUG

def draw_centered_text(text, font_size, color, surface, rect, font_type='RobotoB'):
    font = globals()[font_type][font_size]
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(rect.centerx, rect.centery))
    surface.blit(textobj, textrect)

def draw_tabs(surface):
    total_tab_width = SCREEN_WIDTH // 1.25  # Use 80% of the screen width for tabs
    tab_width = total_tab_width // len(pages)
    start_x = (SCREEN_WIDTH - total_tab_width) // 2  # Center the tabs horizontally

    for i, page in enumerate(pages):
        text_color = get_color('BRIGHT')
        rect = pygame.Rect(start_x + i * tab_width, 0, tab_width, 50)
        text_surface = RobotoB[30].render(page, True, text_color)
        text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
        
        surface.blit(text_surface, text_rect)
        
        # Draw underline with arms for the active tab
        if i == current_page:
            # Draw lines to the left and right of the active tab
            pygame.draw.line(surface, get_color('BRIGHT'), (rect.left - 15, 50), (text_rect.left - 12, 50), 3)  # Line to the left of the tab
            pygame.draw.line(surface, get_color('BRIGHT'), (text_rect.right + 12, 50), (rect.right + 15, 50), 3)  # Line to the right of the tab
            # Draw vertical and short horizontal bars for the active tab
            pygame.draw.line(surface, get_color('BRIGHT'), (text_rect.left - 12, 20), (text_rect.left - 12, 50), 3)  # Left vertical bar
            pygame.draw.line(surface, get_color('BRIGHT'), (text_rect.left - 12, 20), (text_rect.left - 4, 20), 3)  # Left short bar
            pygame.draw.line(surface, get_color('BRIGHT'), (text_rect.right + 4, 20), (text_rect.right + 12, 20), 3)  # Right short bar
            pygame.draw.line(surface, get_color('BRIGHT'), (text_rect.right + 12, 20), (text_rect.right + 12, 50), 3)  # Right vertical bar
        else:
            # Draw a simple horizontal line below inactive tabs
            pygame.draw.line(surface, get_color('BRIGHT'), (rect.left, 50), (rect.right, 50), 3)

    # Draw the underline across the entire screen, excluding the active tab area
    if current_page != -1:
        active_rect = pygame.Rect(start_x + current_page * tab_width, 0, tab_width, 50)
        pygame.draw.line(surface, get_color('BRIGHT'), (0, 50), (active_rect.left, 50), 3)
        pygame.draw.line(surface, get_color('BRIGHT'), (active_rect.right, 50), (SCREEN_WIDTH, 50), 3)

def draw_interface(surface):
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    temp_surface.fill((0, 0, 0, 0))  # Fully transparent background
    
    draw_tabs(temp_surface)
    # Remove this line to avoid extra underline
    # pygame.draw.line(temp_surface, get_color('BRIGHT'), (0, 50), (SCREEN_WIDTH, 50), 2)
    current_page_object = page_objects[current_page]
    current_page_object.draw(temp_surface, RobotoR[24], get_color('BRIGHT'))
    
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
                if event.key in [pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4]:
                    current_page = event.key - pygame.K_F1
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    if current_page == pages.index("DATA"):
                        page_objects[current_page].handle_event(event)
                    elif current_page == pages.index("MAP"):
                        page_objects[current_page].handle_event(event)
                elif current_page == pages.index("DATA"):
                    page_objects[current_page].handle_event(event)
                elif current_page == pages.index("RADIO"):
                    page_objects[current_page].handle_event(event)
                elif current_page == pages.index("MAP"):
                    page_objects[current_page].handle_event(event)

        # Check for hacking game result
        if current_page == pages.index("DATA"):
            hacking_result = page_objects[current_page].get_hacking_game_result()
            if hacking_result is True:
                current_page = pages.index("STAT")
            # If hacking_result is False, we stay on the DATA page

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
        scanline.render(game_screen, get_color('BRIGHT'))

        # Apply CRT shader on the game screen
        if not PI:
            #crt_screen = crt_shader.apply(game_screen.copy())
            crt_screen = game_screen
        else:
            crt_screen = game_screen

        # Blit the CRT screen onto the canvas with the offset
        canvas.blit(crt_screen, (OFFSET_X, OFFSET_Y))

        # Display the mouse position for debugging
        draw_mouse_position(canvas, small_font, get_color('BRIGHT'))

        # Display the canvas
        screen.blit(canvas, (0, 0))
        
        pygame.display.flip()

        if current_page == pages.index("RADIO"):
            page_objects[current_page].update()
        
        if current_page == pages.index("DATA"):
            page_objects[current_page].update()
            
        clock.tick(FPS)

if __name__ == "__main__":
    main()