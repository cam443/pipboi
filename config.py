# config.py
import pygame
import pygame.freetype
from settings import settings

# Colors
BLACK = (0, 0, 0)
COLOR_SCHEMES = {
    'GREEN': {'BRIGHT': (0, 230, 0), 'LIGHT': (0, 170, 0), 'MID': (0, 120, 0), 'DIM': (0, 70, 0), 'DARK': (0, 40, 0)},
    'CYAN': {'BRIGHT': (0, 230, 230), 'LIGHT': (0, 170, 170), 'MID': (0, 120, 120), 'DIM': (0, 70, 70), 'DARK': (0, 40, 40)},
    'PURPLE': {'BRIGHT': (230, 0, 230), 'LIGHT': (170, 0, 170), 'MID': (120, 0, 120), 'DIM': (70, 0, 70), 'DARK': (40, 0, 40)},
    'RED': {'BRIGHT': (230, 0, 0), 'LIGHT': (170, 0, 0), 'MID': (120, 0, 0), 'DIM': (70, 0, 0), 'DARK': (40, 0, 0)},
    'YELLOW': {'BRIGHT': (230, 230, 0), 'LIGHT': (170, 170, 0), 'MID': (120, 120, 0), 'DIM': (70, 70, 0), 'DARK': (40, 40, 0)}
}

def get_color(color_name):
    current_scheme = settings.get('ui_color')
    return COLOR_SCHEMES[current_scheme][color_name]

BRIGHT = property(lambda: get_color('BRIGHT'))
LIGHT = property(lambda: get_color('LIGHT'))
MID = property(lambda: get_color('MID'))
DIM = property(lambda: get_color('DIM'))
DARK = property(lambda: get_color('DARK'))

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
CANVAS_WIDTH, CANVAS_HEIGHT = 800, 480
OFFSET_X, OFFSET_Y = 80, 0  # Configurable offset values
FPS = 30
FULLSCREEN = False

# Map Stuff
WIDTH, HEIGHT = 400, 280  # Adjust these values to your desired map size
MAP_ZOOM = 14
LOCAL_ZOOM = 18
MAP_TYPE = "hybrid"
MAP_FOCUS = [34.0861534, -117.8854141]  # Example coordinates (San Francisco)
#API_KEY = "AIzaSyBGLrr7j1P_pMknv1vRbKD4X7xMScWxnzM"  # Replace with your Google Maps API key
API_KEY = "pk.eyJ1Ijoic2VlbnJlbmRlciIsImEiOiJjbHpzejFwaG4xMmRhMnJwdzNoZjYzMmhjIn0.9iqKEORppuPyqQomr44Szg"  # Replace with your MapBox API key 

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