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
        self.world_map = Map(SCREEN_WIDTH, SCREEN_HEIGHT - 70, focus, zoom, map_type, api_key)
        self.local_map = Map(SCREEN_WIDTH, SCREEN_HEIGHT - 70, focus, zoom + 3, map_type, api_key)
        self.container = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 70), pygame.SRCALPHA)
        self.container_rect = self.container.get_rect(top=70)  # Position below the tab underline
        self.feather_mask = self.create_feather_mask(SCREEN_WIDTH, SCREEN_HEIGHT - 70)
        self.sub_tabs = ["WORLD MAP", "LOCAL MAP"]
        self.current_sub_tab = 0
        self.local_map_focus = [37.7749, -122.4194]  # Hardcoded GPS coordinates 
        self.local_map_needs_update = True
        self.player_indicator = self.create_player_indicator()
        self.player_direction = 0  # 0 degrees is North, 90 is East, 180 is South, 270 is West

    def create_player_indicator(self):
        indicator = pygame.Surface((33, 49), pygame.SRCALPHA)
        arrow = pygame.image.load('images/icons/Player_Marker.png').convert_alpha()
        indicator.blit(arrow, (0, 0))
        return indicator
    
    def rotate_player_indicator(self):
        return pygame.transform.rotate(self.player_indicator, -self.player_direction)

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

    def draw_sub_tabs(self, surface, font, color):
        tab_width = SCREEN_WIDTH // 4.5  # Adjust this value to change the spacing between tabs
        for i, tab in enumerate(self.sub_tabs):
            x = 20 + i * tab_width  # Start 20 pixels from the left edge
            y = 60  # Keep the vertical position the same

            if i == self.current_sub_tab:
                text_color = get_color('BRIGHT')
                tab_font = RobotoB[24]
            else:
                text_color = get_color('DIM')
                tab_font = RobotoR[24]

            text_surface = tab_font.render(tab, True, text_color)
            text_rect = text_surface.get_rect(left=x, top=y)
            surface.blit(text_surface, text_rect)

    def draw(self, surface, font, color):
        self.draw_sub_tabs(surface, font, color)
        
        # Clear the container
        self.container.fill((0, 0, 0, 0))  # Fill with transparent color
        
        if self.current_sub_tab == 0:  # World Map
            current_map = self.world_map
        else:  # Local Map
            current_map = self.local_map
            if self.local_map_needs_update:
                self.local_map.focus = self.local_map_focus
                self.local_map.update_map()
                self.local_map_needs_update = False
        
        # Draw the map onto the container
        self.container.blit(current_map.surface, (0, 0))
        
        # Draw player indicator on local map
        if self.current_sub_tab == 1:  # Local Map
            rotated_indicator = self.rotate_player_indicator()
            indicator_pos = (self.container.get_width() // 2 - rotated_indicator.get_width() // 2,
                             self.container.get_height() // 2 - rotated_indicator.get_height() // 2)
            self.container.blit(rotated_indicator, indicator_pos)
        
        # Apply the color overlay to the entire container
        self.container.fill(color, special_flags=pygame.BLEND_MULT)
        
        # Apply the feather mask to the container
        self.container.blit(self.feather_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw the container onto the main surface
        surface.blit(self.container, self.container_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.current_sub_tab = 0
                print("Switched to World Map tab")  # Debug print
            elif event.key == pygame.K_2:
                self.current_sub_tab = 1
                self.local_map_needs_update = True
                print("Switched to Local Map tab")  # Debug print
            
            if self.current_sub_tab == 0:  # World Map tab
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # Zoom in
                    self.world_map.zoom_in()
                elif event.key == pygame.K_MINUS:  # Zoom out
                    self.world_map.zoom_out()
                elif event.key == pygame.K_LEFT:  # Pan left
                    self.world_map.pan(-1, 0)
                elif event.key == pygame.K_RIGHT:  # Pan right
                    self.world_map.pan(1, 0)
                elif event.key == pygame.K_UP:  # Pan up
                    self.world_map.pan(0, -1)
                elif event.key == pygame.K_DOWN:  # Pan down
                    self.world_map.pan(0, 1)
            elif self.current_sub_tab == 1:  # Local Map tab
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # Zoom in
                    self.local_map.zoom_in()
                elif event.key == pygame.K_MINUS:  # Zoom out
                    self.local_map.zoom_out()
                elif event.key == pygame.K_LEFT:  # Rotate left
                    self.update_player_direction(self.player_direction - 15)
                elif event.key == pygame.K_RIGHT:  # Rotate right
                    self.update_player_direction(self.player_direction + 15)

        print(f"Current sub-tab: {self.current_sub_tab}")  # Debug print

    #To update coords, use: map_page.update_local_map_focus([new_latitude, new_longitude])
    def update_local_map_focus(self, new_focus):
        self.local_map_focus = new_focus
        self.local_map_needs_update = True
    def update_player_direction(self, new_direction):
        self.player_direction = new_direction
        # Ensure the direction is between 0 and 359
        self.player_direction %= 360