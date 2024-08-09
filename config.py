# config.py
import pygame
import pygame.freetype

# Colors
BLACK = (0, 0, 0)
BRIGHT = (0, 230, 0)
LIGHT = (0, 170, 0)
MID = (0, 120, 0)
DIM = (0, 70, 0)
DARK = (0, 40, 0)

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
CANVAS_WIDTH, CANVAS_HEIGHT = 800, 480
OFFSET_X, OFFSET_Y = 80, 0  # Configurable offset values
FPS = 30
FULLSCREEN = False

pygame.font.init()
pygame.freetype.init()

RobotoB = {}
RobotoR = {}
TechMono = {}
FreeRobotoB = {}
FreeRobotoR = {}
FreeTechMono = {}

for x in range(10, 40):  # Increased range to include larger sizes
    RobotoB[x] = pygame.font.Font('fonts/RobotoCondensed-Bold.ttf', x)
    RobotoR[x] = pygame.font.Font('fonts/RobotoCondensed-Regular.ttf', x)
    TechMono[x] = pygame.font.Font('fonts/TechMono.ttf', x)
    FreeRobotoB[x] = pygame.freetype.Font('fonts/RobotoCondensed-Bold.ttf', x)
    FreeRobotoR[x] = pygame.freetype.Font('fonts/RobotoCondensed-Regular.ttf', x)
    FreeTechMono[x] = pygame.freetype.Font('fonts/TechMono.ttf', x)