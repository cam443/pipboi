import pygame
import requests
import io
import numpy as np
from config import *

class Map:
    def __init__(self, width, height, focus, zoom, map_type, api_key):
        self.width = width
        self.height = height
        self.focus = list(focus)  # Convert to list for mutability
        self.zoom = zoom
        self.map_type = map_type
        self.api_key = api_key
        self.surface = pygame.Surface((self.width, self.height))
        self.offset_x = 0
        self.offset_y = 0
        self.update_map()

    def fetch_map(self):
        lat, long = str(self.focus[0]), str(self.focus[1])
        url = (f"https://api.mapbox.com/styles/v1/seenrender/clzu78tql00i801r5a3wzb9rs/static/"
               f"{long},{lat},{self.zoom},0/{self.width}x{self.height}?access_token={self.api_key}")
        
        print(f"Fetching map from URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except Exception as e:
            print(f"Failed to load map image: {e}")
            return None

    def update_map(self):
        map_image = self.fetch_map()
        if map_image:
            try:
                self.surface = pygame.image.load(map_image).convert()
#                self.apply_color_filter()
                print(f"Loaded image of size: {self.surface.get_size()}")
            except Exception as e:
                print(f"Error converting image to surface: {e}")

#    def apply_color_filter(self):
#        # Convert surface to a 3D array
#        arr = pygame.surfarray.array3d(self.surface)
#
#        # Convert to grayscale
#        gray = np.dot(arr[...,:3], [0.2989, 0.5870, 0.1140])
#
#        # Normalize to 0-1
#        gray = gray / 255.0
#
#        # Invert the grayscale
#        gray = 1 - gray
#        gray = np.clip(gray, 0, 1)  # Ensure values stay in the 0-1 range
#
#        # Create color map
#        #color_map = [
#        #    (0, (100, 100, 100)),
#        #    (0.1, (0, 0, 0)),
#        #    (0.2, (0, 0, 0)),
#        #    (0.3, (255, 255, 255)),
#        #    (0.4, (255, 255, 255)),
#        #    (0.5, (100, 100, 100)),
#        #    (0.6, (255, 255, 255)),
#        #    (0.7, (255, 255, 255)),
#        #    (0.8, (255, 255, 255)),
#        #    (0.9, (255, 255, 255)),
#        #    (1.0, (255, 255, 255))
#        #]
#        color_map = [
#            (0, (255, 0, 0)),       # Red
#            (0.03, (0, 0, 255)),
#            (0.1, (0, 255, 0)),     # Green
#            (0.2, (0, 0, 255)),     # Blue
#            (0.3, (255, 255, 0)),   # Yellow
#            (0.4, (0, 255, 255)),   # Cyan
#            (0.5, (255, 0, 255)),   # Magenta
#            (0.6, (192, 192, 192)), # Silver
#            (0.7, (128, 0, 0)),     # Maroon
#            (0.8, (0, 128, 0)),     # Dark Green
#            (0.9, (0, 0, 128)),     # Navy
#            (1.0, (255, 255, 255))  # White
#        ]
#
#        # Apply color mapping
#        mapped = np.zeros_like(arr)
#        for i in range(len(color_map) - 1):
#            mask = (gray >= color_map[i][0]) & (gray < color_map[i+1][0])
#            t = (gray[mask] - color_map[i][0]) / (color_map[i+1][0] - color_map[i][0])
#            mapped[mask] = np.outer(1-t, color_map[i][1]) + np.outer(t, color_map[i+1][1])
#
#        mapped = mapped.astype(np.uint8)
#
#        # Convert back to surface
#        pygame.surfarray.blit_array(self.surface, mapped)

    def pan(self, dx, dy):
        # Hardcoded pan sensitivity for each zoom level
        pan_sensitivity = {
            1: 0.5,
            2: 0.4,
            3: 0.3,
            4: 0.25,
            5: 0.2,
            6: 0.15,
            7: 0.1,
            8: 0.08,
            9: 0.06,
            10: 0.05,
            11: 0.03,
            12: 0.01,
            13: 0.005,
            14: 0.0025,
            15: 0.0015,
            16: 0.001,
            17: 0.0005,
            18: 0.00025,
            19: 0.0001,
            20: 0.00005,
            21: 0.000025
        }.get(self.zoom, 0.00001)  # Default to 0.01 if zoom level is out of range

        # Move the focus point by a certain delta
        self.focus[0] -= dy * (pan_sensitivity * 1.5)  # Latitude changes (invert y-axis)
        self.focus[1] += dx * (pan_sensitivity * 1.5)  # Longitude changes
        self.update_map()
        self.offset_x = 0
        self.offset_y = 0

    def zoom_in(self):
        if self.zoom < 21:
            self.zoom += 1
            self.update_map()

    def zoom_out(self):
        if self.zoom > 0:
            self.zoom -= 1
            self.update_map()

class MapPage:
    def __init__(self, width, height, focus, zoom, map_type, api_key):
        self.map = Map(SCREEN_WIDTH, SCREEN_HEIGHT - 50, focus, zoom, map_type, api_key)
        self.container = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 50), pygame.SRCALPHA)
        self.container_rect = self.container.get_rect(top=50)  # Position below the tab underline
        self.feather_mask = self.create_feather_mask(SCREEN_WIDTH, SCREEN_HEIGHT - 50)

    def create_feather_mask(self, width, height, edge_width=50):
        mask = pygame.Surface((width, height), pygame.SRCALPHA)
        for x in range(width):
            for y in range(height):
                alpha = 255
                if x < edge_width:
                    alpha = int(255 * ((x / edge_width) ** 2))
                elif x > width - edge_width:
                    alpha = int(255 * (((width - x) / edge_width) ** 2))
                if y < edge_width:
                    alpha = min(alpha, int(255 * ((y / edge_width) ** 2)))
                elif y > height - edge_width:
                    alpha = min(alpha, int(255 * (((height - y) / edge_width) ** 2)))
                mask.set_at((x, y), (255, 255, 255, alpha))
        return mask

    def draw(self, surface, font, color):
        # Clear the container
        self.container.fill((0, 0, 0, 0))  # Fill with transparent color
        
        # Create a copy of the map surface and apply the color overlay
        colored_map = self.map.surface.copy()
        colored_map.fill(color, special_flags=pygame.BLEND_MULT)
        
        # Draw the colored map onto the container
        self.container.blit(colored_map, (0, 0))
        
        # Apply the feather mask to the container
        self.container.blit(self.feather_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw the container onto the main surface
        surface.blit(self.container, self.container_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # Zoom in
                self.map.zoom_in()
            elif event.key == pygame.K_MINUS:  # Zoom out
                self.map.zoom_out()
            elif event.key == pygame.K_LEFT:  # Pan left
                self.map.pan(-1, 0)
            elif event.key == pygame.K_RIGHT:  # Pan right
                self.map.pan(1, 0)
            elif event.key == pygame.K_UP:  # Pan up
                self.map.pan(0, -1)
            elif event.key == pygame.K_DOWN:  # Pan down
                self.map.pan(0, 1)