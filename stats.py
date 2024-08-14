import pygame
import os
import math
import random
import serial
from config import *
from datetime import datetime, timedelta

class StatPage:
    def __init__(self):
        self.content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vehicula."
        
        # FONTS
        self.small_font = RobotoR[24]

        try:
            self.serial_port = serial.Serial('COM9', 115200)  # Initialize serial port
        except serial.SerialException:
            self.serial_port = None  # Handle case where serial port is not available
        self.last_heart_rate = 72  # Default heart rate value

        # Load leg frames at original size
        self.leg_frames = [pygame.image.load(os.path.join('images/legs', f'{i}.png')).convert_alpha() for i in range(1, 9)]
        self.current_leg_frame = 0
        
        # Load head frames and select a random head at original size
        self.head_frames = [pygame.image.load(os.path.join('images/head', f'{i}.png')).convert_alpha() for i in range(1, 8)]
        self.head_frame = random.choice(self.head_frames)

        # Head bob parameters
        self.head_bob_amplitude = 1  # Adjust the amplitude as needed
        
        # Resizing scale factor
        self.scale_factor = 1  # Adjust this factor as needed

        # Supersampling factor (not used in animation rendering)
        self.supersample_factor = 2

        # Animation timing
        self.leg_frame_delay = 200  # milliseconds
        self.last_update = pygame.time.get_ticks()

        # Footer parameters
        self.hp = 100
        self.hp_max = 100
        self.level = 27
        self.xp = 35
        self.max_xp = 100
        self.ap = 100
        self.ap_max = 175

        # Font Params
        self.footer_bold = RobotoB[22]

        # Sensor readouts
        self.heart_rate = 72
        self.spo2 = 98
        self.temperature = 36.5
        self.humidity = 45
        self.pressure = 1013
        self.altitude = 150
        self.bac = 0.0

        # Load icons
        self.icons = {
            "heart_rate": pygame.image.load('images/icons/heart.png').convert_alpha(),
            "spo2": pygame.image.load('images/icons/ox.png').convert_alpha(),
            "temperature": pygame.image.load('images/icons/temp.png').convert_alpha(),
            "humidity": pygame.image.load('images/icons/humid.png').convert_alpha(),
            "pressure": pygame.image.load('images/icons/pressure.png').convert_alpha(),
            "altitude": pygame.image.load('images/icons/altitude.png').convert_alpha(),
            "bac": pygame.image.load('images/icons/bac.png').convert_alpha()
        }

    def update_hp_from_serial(self):
        try:
            if self.serial_port and self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if "HR=" in line:
                        try:
                            heart_rate = int(line.split("HR=")[1])
                            self.heart_rate = heart_rate  # Update hp with heart rate value
                            self.last_heart_rate = heart_rate  # Store the last valid heart rate
                            print(f"HeartRate: {heart_rate}") # Debugging
                        except ValueError:
                            pass
                except serial.SerialException:
                    self.serial_port = None  # Handle case where serial port is lost
        except (serial.SerialException, OSError) as e:
            self.serial_port = None  # Handle case where serial port is lost
        finally:
            if not self.serial_port:
                self.heart_rate = self.last_heart_rate  # Use the last valid heart rate if serial port is not available



    def resize_images(self):
        supersample_factor = self.supersample_factor
        self.leg_frames = [pygame.transform.smoothscale(frame, 
                        (int(frame.get_width() * self.scale_factor * supersample_factor), 
                         int(frame.get_height() * self.scale_factor * supersample_factor))) for frame in self.leg_frames]
        self.head_frame = pygame.transform.smoothscale(self.head_frame, 
                       (int(self.head_frame.get_width() * self.scale_factor * supersample_factor), 
                        int(self.head_frame.get_height() * self.scale_factor * supersample_factor)))

        # Scale down to the desired size
        self.leg_frames = [pygame.transform.smoothscale(frame, 
                        (int(frame.get_width() // supersample_factor), 
                         int(frame.get_height() // supersample_factor))) for frame in self.leg_frames]
        self.head_frame = pygame.transform.smoothscale(self.head_frame, 
                       (int(self.head_frame.get_width() // supersample_factor), 
                        int(self.head_frame.get_height() // supersample_factor)))

    def draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def draw_animation(self, surface, color):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.leg_frame_delay:
            self.last_update = now
            self.current_leg_frame = (self.current_leg_frame + 1) % len(self.leg_frames)
        
        leg_image = self.leg_frames[self.current_leg_frame].copy()
        leg_image.fill(color, special_flags=pygame.BLEND_MULT)
        leg_rect = leg_image.get_rect(center=(320, 280))  # Center on screen (400x320)
        surface.blit(leg_image, leg_rect.topleft)
        
        # Calculate head bob offset based on current leg frame
        head_bob_offset = self.head_bob_amplitude * math.sin(self.current_leg_frame * (1 * math.pi / len(self.leg_frames)) - 1)
        head_bob_offset2 = self.head_bob_amplitude * math.sin(self.current_leg_frame * (2 * math.pi / len(self.leg_frames)) + 1)
        head_image = self.head_frame.copy()
        head_image.fill(color, special_flags=pygame.BLEND_MULT)
        head_rect = head_image.get_rect(center=(315 - head_bob_offset2, 170 + head_bob_offset))  # Position above legs with bob
        surface.blit(head_image, head_rect.topleft)

    def draw_footer(self, surface, font, color):
        screen_width, screen_height = surface.get_size()
        footer_height = 40
        footer_y = screen_height - footer_height
        gap = 5  # Gap between boxes

        # Adjust the width of each box
        side_box_width = screen_width // 5  # Smaller side boxes
        middle_box_width = screen_width // 3  # Larger middle box
        total_width = 2 * side_box_width + middle_box_width + 2 * gap  # Total width of all boxes and gaps
        start_x = (screen_width - total_width) // 2  # Center the boxes horizontally

        # Define rectangles
        left_rect = pygame.Rect(0, footer_y, start_x + side_box_width, footer_height)  # Extend to the left edge
        middle_rect = pygame.Rect(start_x + side_box_width + gap, footer_y, middle_box_width, footer_height)
        right_rect = pygame.Rect(start_x + side_box_width + gap + middle_box_width + gap, footer_y, start_x + side_box_width, footer_height)  # Extend to the right edge

        # Draw solid rectangles
        pygame.draw.rect(surface, get_color('DARK'), left_rect)
        pygame.draw.rect(surface, get_color('DARK'), middle_rect)
        pygame.draw.rect(surface, get_color('DARK'), right_rect)

        # Draw text for HP (right-aligned)
        hp_text = f"HP: {self.hp}/{self.hp_max}"
        hp_surface = self.footer_bold.render(hp_text, True, get_color('BRIGHT'))
        hp_rect = hp_surface.get_rect(right=left_rect.right - 5, centery=left_rect.centery)
        surface.blit(hp_surface, hp_rect)

        # Draw text for AP (left-aligned)
        ap_text = f"AP: {self.ap}/{self.ap_max}"
        ap_surface = self.footer_bold.render(ap_text, True, get_color('BRIGHT'))
        ap_rect = ap_surface.get_rect(left=right_rect.left + 5, centery=right_rect.centery)
        surface.blit(ap_surface, ap_rect)

        # Calculate XP percentage based on the date
        # Get today's date
        today = datetime.now()

        # Determine the next May 17th
        if today.month < 5 or (today.month == 5 and today.day < 17):
            next_may_17 = datetime(today.year, 5, 17)
        else:
            next_may_17 = datetime(today.year + 1, 5, 17)

        # Calculate the number of days until the next May 17th
        days_until_next_may_17 = (next_may_17 - today).days
        days_left = 365 - days_until_next_may_17

        # Calculate the percentage of days until the next May 17th out of 365
        xp_percentage = days_left / 365.0

        # Level and XP bar
        level_text = f"LEVEL {self.level}"
        level_surface = self.footer_bold.render(level_text, True, get_color('BRIGHT'))

        # XP bar
        xp_bar_width = middle_rect.width - level_surface.get_width() - 20
        xp_bar_height = 15
        xp_bar_x = middle_rect.x + level_surface.get_width() + 10
        xp_bar_y = middle_rect.centery - xp_bar_height // 2

        # Draw level text and XP bar
        surface.blit(level_surface, (middle_rect.x + 5, middle_rect.centery - level_surface.get_height() // 2))
        pygame.draw.rect(surface, get_color('BRIGHT'), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height), 2)
        pygame.draw.rect(surface, get_color('BRIGHT'), (xp_bar_x, xp_bar_y, xp_bar_width * xp_percentage, xp_bar_height))

    def draw_sensors(self, surface, font, color):
        sensor_data = [
            ("heart_rate", f"{self.heart_rate} BPM", (460, 150)),  # Near chest
            ("spo2", f"{self.spo2}%", (460, 220)),  # Near arm
            ("bac", f"{self.bac} %", (460, 290)),  # Near head
            ####
            ("temperature", f"{self.temperature}°F", (20, 120)),  # Near stomach
            ("humidity", f"{self.humidity}%", (20, 190)),  # Near other arm
            ("pressure", f"{self.pressure} hPa", (20, 260)),  # Below Vault Boy
            ("altitude", f"{self.altitude} FT", (20, 330))  # Below Vault Boy
            
        ]

        for icon_key, value, (x, y) in sensor_data:
            rect = pygame.Rect(x, y, 160, 40)  # Smaller rectangular boxes
            pygame.draw.rect(surface, get_color('DARK'), rect)
            icon = pygame.transform.scale(self.icons[icon_key], (30, 30))
            icon.fill(color, special_flags=pygame.BLEND_MULT)
            surface.blit(icon, (rect.x + 5, rect.y + 5))  # Icon on the left
            text_surface = self.small_font.render(value, True, color)
            text_rect = text_surface.get_rect(midleft=(rect.x + 45, rect.centery))  # Text to the right of the icon
            surface.blit(text_surface, text_rect)

    def draw(self, surface, font, color):
        self.update_hp_from_serial()  # Update hp before drawing
        self.draw_animation(surface, color)
        self.draw_footer(surface, font, color)
        self.draw_sensors(surface, font, color)