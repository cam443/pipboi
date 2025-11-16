import pygame
import requests
import io
import numpy as np
import os
import hashlib
import time
import json
import random
from config import *

class Map:
    def __init__(self, width, height, focus, zoom, map_type, api_key, style):
        self.width = width
        self.height = height
        self.focus = list(focus)  # Convert to list for mutability
        self.zoom = zoom
        self.map_type = map_type
        self.api_key = api_key
        self.style = style
        self.surface = pygame.Surface((self.width, self.height))
        self.offset_x = 0
        self.offset_y = 0
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_cache")
        self.cache_index_file = os.path.join(self.cache_dir, "cache_index.json")
        self.ensure_cache_dir()
        self.cache_index = self.load_cache_index()
        self.update_map()

    def ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            print(f"Created map cache directory: {self.cache_dir}")

    def load_cache_index(self):
        """Load the cache index from disk"""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache index: {e}")
                return {}
        return {}

    def save_cache_index(self):
        """Save the cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f)
        except Exception as e:
            print(f"Error saving cache index: {e}")

    def get_cache_key(self):
        """Generate a unique key for the current map parameters"""
        key_string = f"{self.style}_{self.focus[0]}_{self.focus[1]}_{self.zoom}_{self.width}x{self.height}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_cached_map(self, cache_key):
        """Try to get a map from the cache"""
        if cache_key in self.cache_index:
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'rb') as f:
                        return io.BytesIO(f.read())
                except Exception as e:
                    print(f"Error reading cached map: {e}")
        return None

    def cache_map(self, cache_key, map_data):
        """Save a map to the cache"""
        try:
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")
            with open(cache_path, 'wb') as f:
                f.write(map_data.getvalue())
            
            # Update cache index with timestamp
            self.cache_index[cache_key] = {
                "timestamp": time.time(),
                "focus": self.focus.copy(),
                "zoom": self.zoom,
                "style": self.style,
                "dimensions": f"{self.width}x{self.height}"
            }
            self.save_cache_index()
            print(f"Map cached successfully: {cache_key}")
        except Exception as e:
            print(f"Error caching map: {e}")

    def fetch_map(self):
        lat, long = str(self.focus[0]), str(self.focus[1])
        url = (f"https://api.mapbox.com/styles/v1/seenrender/{self.style}/static/"
               f"{long},{lat},{self.zoom},0/{self.width}x{self.height}?access_token={self.api_key}")
        
        # Generate cache key for this request
        cache_key = self.get_cache_key()
        
        # Try to get from cache first
        cached_map = self.get_cached_map(cache_key)
        if cached_map:
            print(f"Using cached map: {cache_key}")
            return cached_map
        
        # If not in cache, fetch from API
        print(f"Fetching map from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            map_data = io.BytesIO(response.content)
            
            # Cache the fetched map
            self.cache_map(cache_key, map_data)
            
            # Reset position to beginning of BytesIO object
            map_data.seek(0)
            return map_data
        except Exception as e:
            print(f"Failed to load map image: {e}")
            
            # If network error, try to find a nearby cached map
            nearby_map = self.find_nearby_cached_map()
            if nearby_map:
                print(f"Using nearby cached map instead")
                return nearby_map
                
            return None

    def find_nearby_cached_map(self):
        """Find a cached map that's close to the current parameters"""
        if not self.cache_index:
            return None
            
        best_match = None
        best_score = float('inf')
        
        for key, info in self.cache_index.items():
            # Skip if style doesn't match
            if info.get("style") != self.style:
                continue
                
            # Skip if zoom is too different
            if abs(info.get("zoom", 0) - self.zoom) > 1:
                continue
                
            # Calculate distance between focus points
            cached_focus = info.get("focus", [0, 0])
            lat_diff = abs(cached_focus[0] - self.focus[0])
            lon_diff = abs(cached_focus[1] - self.focus[1])
            distance = (lat_diff**2 + lon_diff**2)**0.5
            
            # The lower the distance, the better the match
            if distance < best_score:
                best_score = distance
                best_match = key
        
        # If we found a reasonably close match
        if best_match and best_score < 0.1:  # Threshold for "close enough"
            cache_path = os.path.join(self.cache_dir, f"{best_match}.png")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'rb') as f:
                        return io.BytesIO(f.read())
                except Exception:
                    pass
        
        return None

    def clean_old_cache(self, max_age_days=30, max_size_mb=100):
        """Remove old cached maps to save space"""
        if not self.cache_index:
            return
            
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Calculate total cache size
        total_size = 0
        for key in list(self.cache_index.keys()):
            cache_path = os.path.join(self.cache_dir, f"{key}.png")
            if os.path.exists(cache_path):
                total_size += os.path.getsize(cache_path)
        
        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)
        
        # Remove old entries if needed
        keys_to_remove = []
        for key, info in sorted(self.cache_index.items(), key=lambda x: x[1].get("timestamp", 0)):
            # Remove if too old
            if current_time - info.get("timestamp", 0) > max_age_seconds:
                keys_to_remove.append(key)
                continue
                
            # Remove if we need to reduce cache size
            if total_size_mb > max_size_mb:
                keys_to_remove.append(key)
                cache_path = os.path.join(self.cache_dir, f"{key}.png")
                if os.path.exists(cache_path):
                    total_size_mb -= os.path.getsize(cache_path) / (1024 * 1024)
        
        # Actually remove the files and update the index
        for key in keys_to_remove:
            cache_path = os.path.join(self.cache_dir, f"{key}.png")
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception as e:
                    print(f"Error removing cached file: {e}")
            del self.cache_index[key]
        
        if keys_to_remove:
            self.save_cache_index()
            print(f"Cleaned {len(keys_to_remove)} old cached maps")

    def update_map(self):
        map_image = self.fetch_map()
        if map_image:
            try:
                self.surface = pygame.image.load(map_image).convert()
                print(f"Loaded image of size: {self.surface.get_size()}")
            except Exception as e:
                print(f"Error converting image to surface: {e}")
        
        # Periodically clean old cache entries
        if random.random() < 0.05:  # 5% chance on each map update
            self.clean_old_cache()

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
            print(f"Zoomed in to level {self.zoom}")  # Add debug print

    def zoom_out(self):
        if self.zoom > 0:
            self.zoom -= 1
            self.update_map()
            print(f"Zoomed out to level {self.zoom}")  # Add debug print

class MapPage:
    def __init__(self, width, height, focus, zoom, map_type, api_key):
        self.world_map = Map(SCREEN_WIDTH, SCREEN_HEIGHT - 70, focus, zoom, map_type, api_key, WORLD_STYLE)
        self.local_map = Map(SCREEN_WIDTH, SCREEN_HEIGHT - 70, focus, zoom + 3, map_type, api_key, LOCAL_STYLE)
        self.container = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 70), pygame.SRCALPHA)
        self.container_rect = self.container.get_rect(top=70)  # Position below the tab underline
        self.feather_mask = self.create_feather_mask(SCREEN_WIDTH, SCREEN_HEIGHT - 70)
        self.sub_tabs = ["WORLD MAP", "LOCAL MAP"]
        self.current_sub_tab = 0
        self.local_map_focus = [37.7749, -122.4194]  # Hardcoded GPS coordinates 
        self.local_map_needs_update = True
        self.player_indicator = self.create_player_indicator()
        self.player_direction = 0  # 0 degrees is North, 90 is East, 180 is South, 270 is West
        self.location_update_timer = 0
        self.location_update_interval = 300000
        self.is_caching = False
        self.caching_progress = 0
        self.caching_total = 0
        self.caching_message = ""
        self.cache_queue = []
        self.last_cache_time = 0
        self.cache_delay = 300  # milliseconds between cache requests
        self.cache_complete_time = 0
        self.cache_complete_display_duration = 3000  # Show completion message for 3 seconds

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
        current_time = pygame.time.get_ticks()
        if current_time - self.location_update_timer > self.location_update_interval:
            self.update_location_from_device()
            self.location_update_timer = current_time
        
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
        
        # Process cache queue if active
        if self.is_caching and self.cache_queue and current_time - self.last_cache_time > self.cache_delay:
            self.process_next_cache_item()
            self.last_cache_time = current_time
        
        # Check if we need to hide the completion message
        if self.is_caching and not self.cache_queue and self.cache_complete_time > 0:
            if current_time - self.cache_complete_time > self.cache_complete_display_duration:
                self.is_caching = False
                self.cache_complete_time = 0
        
        # Display caching progress if active
        if self.is_caching:
            self.draw_caching_progress(surface, font)

    def draw_caching_progress(self, surface, font):
        """Draw a progress bar for the caching operation"""
        progress_width = 400
        progress_height = 30
        progress_x = (SCREEN_WIDTH - progress_width) // 2
        progress_y = SCREEN_HEIGHT - 150
        
        # Draw background
        pygame.draw.rect(surface, get_color('DIM'), 
                         (progress_x, progress_y, progress_width, progress_height))
        
        # Draw progress
        if self.caching_total > 0:
            progress_percent = self.caching_progress / self.caching_total
            pygame.draw.rect(surface, get_color('BRIGHT'), 
                            (progress_x, progress_y, 
                             int(progress_width * progress_percent), progress_height))
        
        # Draw text
        progress_text = f"Caching maps: {self.caching_progress}/{self.caching_total}"
        text_surface = RobotoR[16].render(progress_text, True, get_color('BRIGHT'))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, progress_y - 20))
        surface.blit(text_surface, text_rect)
        
        # Draw message
        if self.caching_message:
            msg_surface = RobotoR[14].render(self.caching_message, True, get_color('BRIGHT'))
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, progress_y + 50))
            surface.blit(msg_surface, msg_rect)

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
                    print("Zoom in key pressed")  # Debug print
                    self.world_map.zoom_in()
                elif event.key == pygame.K_MINUS:  # Zoom out
                    print("Zoom out key pressed")  # Debug print
                    self.world_map.zoom_out()
                elif event.key == pygame.K_LEFT:  # Pan left
                    self.world_map.pan(-1, 0)
                elif event.key == pygame.K_RIGHT:  # Pan right
                    self.world_map.pan(1, 0)
                elif event.key == pygame.K_UP:  # Pan up
                    self.world_map.pan(0, -1)
                elif event.key == pygame.K_DOWN:  # Pan down
                    self.world_map.pan(0, 1)
                elif event.key == pygame.K_c:  # Cache current area
                    print("Starting area caching...")
                    self.start_area_caching()
            elif self.current_sub_tab == 1:  # Local Map tab
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # Zoom in
                    print("Zoom in key pressed")  # Debug print
                    self.local_map.zoom_in()
                    # Force redraw after zoom
                    self.local_map.update_map()
                elif event.key == pygame.K_MINUS:  # Zoom out
                    print("Zoom out key pressed")  # Debug print
                    self.local_map.zoom_out()
                    # Force redraw after zoom
                    self.local_map.update_map()
                elif event.key == pygame.K_LEFT:  # Rotate left
                    self.update_player_direction(self.player_direction - 15)
                elif event.key == pygame.K_RIGHT:  # Rotate right
                    self.update_player_direction(self.player_direction + 15)
                elif event.key == pygame.K_c:  # Cache current area
                    print("Starting area caching...")
                    self.start_area_caching()

        print(f"Current sub-tab: {self.current_sub_tab}")  # Debug print

    #To update coords, use: map_page.update_local_map_focus([new_latitude, new_longitude])
    def update_location_from_device(self):
        """Attempt to get the device's current location using available methods."""
        try:
            # Try to import geolocation libraries
            location = self.get_device_location()
            if location:
                lat, lon = location
                print(f"Updated location: {lat}, {lon}")
                self.update_local_map_focus([lat, lon])
            else:
                print("Could not get device location")
        except Exception as e:
            print(f"Error updating location: {e}")
    
    def get_device_location(self):
        """Get the device's location using available methods."""
        # Try different methods to get location
        
        # Method 1: Try using the geolocation module if available
        try:
            import geocoder
            g = geocoder.ip('me')
            if g.latlng:
                return g.latlng
        except ImportError:
            print("geocoder module not available")
        
        # Method 2: Try using the platform-specific location services
        try:
            # For Android (if running with Pygame Subset for Android)
            import android
            droid = android.Android()
            droid.startLocating()
            location = droid.readLocation().result
            droid.stopLocating()
            if 'gps' in location:
                return [location['gps']['latitude'], location['gps']['longitude']]
            elif 'network' in location:
                return [location['network']['latitude'], location['network']['longitude']]
        except (ImportError, AttributeError):
            pass
        
        # Method 3: Try using a web service to get approximate location
        try:
            import requests
            response = requests.get('https://ipinfo.io/json')
            if response.status_code == 200:
                data = response.json()
                if 'loc' in data:
                    lat, lon = data['loc'].split(',')
                    return [float(lat), float(lon)]
        except Exception as e:
            print(f"Error getting location from web service: {e}")
        
        return None  # Return None if all methods fail

    def update_player_direction(self, new_direction):
        self.player_direction = new_direction
        # Ensure the direction is between 0 and 359
        self.player_direction %= 360
        
    def update_local_map_focus(self, new_focus):
        self.local_map_focus = new_focus
        self.local_map_needs_update = True

    def start_area_caching(self):
        """Start caching the area around the current focus point at different zoom levels"""
        print("Entering start_area_caching method")
        
        # Determine which map to use as the source
        current_map = self.world_map if self.current_sub_tab == 0 else self.local_map
        center_focus = current_map.focus.copy()
        center_zoom = current_map.zoom
        
        print(f"Current focus: {center_focus}, zoom: {center_zoom}")
        
        # Clear any existing cache queue
        self.cache_queue = []
        
        # Define the area to cache - current zoom level and two levels up/down
        zoom_levels = [
            max(0, center_zoom - 2), 
            max(0, center_zoom - 1), 
            center_zoom, 
            min(21, center_zoom + 1), 
            min(21, center_zoom + 2)
        ]
        
        # Define a larger grid - 5x5 points around the center
        grid_size = 5
        offsets = []
        for i in range(-grid_size//2, grid_size//2 + 1):
            for j in range(-grid_size//2, grid_size//2 + 1):
                offsets.append((i * 0.05, j * 0.05))
        
        # Add all combinations to the queue
        for zoom in zoom_levels:
            # Scale offsets based on zoom level
            scale_factor = 2 ** (14 - zoom) * 0.1
            
            for lat_offset, lon_offset in offsets:
                # Calculate the focus point for this grid cell
                lat = center_focus[0] + lat_offset * scale_factor
                lon = center_focus[1] + lon_offset * scale_factor
                
                # Add to queue
                self.cache_queue.append({
                    'focus': [lat, lon],
                    'zoom': zoom,
                    'style': current_map.style
                })
        
        # Set up caching state
        self.caching_total = len(self.cache_queue)
        self.caching_progress = 0
        self.is_caching = True
        self.caching_message = f"Caching {self.caching_total} map tiles..."
        self.last_cache_time = 0  # Start immediately
        self.cache_complete_time = 0  # Reset completion timer
        
        print(f"Created cache queue with {self.caching_total} items")

    def process_next_cache_item(self):
        """Process the next item in the cache queue"""
        if not self.cache_queue:
            # Queue is empty, caching is complete
            if self.cache_complete_time == 0:  # Only set this once
                self.cache_complete_time = pygame.time.get_ticks()
                self.caching_message = "Caching completed successfully!"
                print("Map caching completed")
            return
        
        # Get the next item from the queue
        item = self.cache_queue.pop(0)
        
        # Update message
        zoom = item['zoom']
        focus = item['focus']
        self.caching_message = f"Caching zoom level {zoom} at {focus[0]:.4f}, {focus[1]:.4f}"
        print(f"Caching: zoom={zoom}, focus={focus}")
        
        try:
            # Create a temporary map for this cache item
            temp_map = Map(
                self.world_map.width, 
                self.world_map.height,
                focus,
                zoom,
                self.world_map.map_type,
                self.world_map.api_key,
                item['style']
            )
            
            # Force the map to be fetched and cached
            map_data = temp_map.fetch_map()
            if map_data:
                print(f"Successfully cached map at zoom={zoom}, focus={focus}")
            else:
                print(f"Failed to cache map at zoom={zoom}, focus={focus}")
            
            # Update progress
            self.caching_progress += 1
            
        except Exception as e:
            print(f"Error caching map tile: {e}")
            # Skip this tile but continue with others
            self.caching_progress += 1
        
        # If queue is now empty, set completion time
        if not self.cache_queue:
            print("Cache queue is now empty")
            self.cache_complete_time = pygame.time.get_ticks()
            self.caching_message = "Caching completed successfully!"