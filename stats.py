import pygame
import os
import math
import random
from config import * 

class StatPage:
    def __init__(self):
        self.content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vehicula."
        
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
        self.hp = 80
        self.hp_max = 100
        self.level = 5
        self.xp = 35
        self.max_xp = 100
        self.ap = 60
        self.ap_max = 75

        #Font Params
        self.footer_bold = RobotoB[26]

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

    def draw_animation(self, surface):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.leg_frame_delay:
            self.last_update = now
            self.current_leg_frame = (self.current_leg_frame + 1) % len(self.leg_frames)
        
        leg_image = self.leg_frames[self.current_leg_frame]
        leg_rect = leg_image.get_rect(center=(320, 280))  # Center on screen (400x320)
        surface.blit(leg_image, leg_rect.topleft)
        
        # Calculate head bob offset based on current leg frame
        head_bob_offset = self.head_bob_amplitude * math.sin(self.current_leg_frame * (2 * math.pi / len(self.leg_frames)) - 1)
        head_bob_offset2 = self.head_bob_amplitude * math.sin(self.current_leg_frame * (2.1 * math.pi / len(self.leg_frames)) + 1)
        head_rect = self.head_frame.get_rect(center=(318 + head_bob_offset2, 164 + head_bob_offset))  # Position above legs with bob
        surface.blit(self.head_frame, head_rect.topleft)

    def draw_footer(self, surface, font, color):
       screen_width, screen_height = surface.get_size()
       footer_height = 40
       footer_y = screen_height - footer_height
       gap = 5  # Gap between boxes

       # Define rectangles
       left_rect = pygame.Rect(0, footer_y, screen_width // 4, footer_height)
       middle_rect = pygame.Rect(screen_width // 4 + gap, footer_y, screen_width // 2 - 2 * gap, footer_height)
       right_rect = pygame.Rect(3 * screen_width // 4, footer_y, screen_width // 4 - gap, footer_height)

       # Draw solid rectangles
       pygame.draw.rect(surface, DARK, left_rect)
       pygame.draw.rect(surface, DARK, middle_rect)
       pygame.draw.rect(surface, DARK, right_rect)

       # Draw text for HP
       self.draw_text(f"HP: {self.hp}/{self.hp_max}", self.footer_bold, BRIGHT, surface, left_rect.x + 5, left_rect.centery - self.footer_bold.get_height() // 2)

       # Draw text for AP (right-aligned)
       ap_text = f"AP: {self.ap}/{self.ap_max}"
       ap_surface = self.footer_bold.render(ap_text, True, BRIGHT)
       ap_rect = ap_surface.get_rect(right=right_rect.right - 5, centery=right_rect.centery)
       surface.blit(ap_surface, ap_rect)

       # Level and XP bar
       level_text = f"LEVEL {self.level}"
       level_surface = self.footer_bold.render(level_text, True, BRIGHT)

       # XP bar
       xp_bar_width = middle_rect.width - level_surface.get_width() - 30
       xp_bar_height = 15
       xp_bar_x = middle_rect.x + level_surface.get_width() + 20
       xp_bar_y = middle_rect.centery - xp_bar_height // 2
       xp_percentage = self.xp / self.max_xp

       # Draw level text and XP bar
       surface.blit(level_surface, (middle_rect.x + 5, middle_rect.centery - level_surface.get_height() // 2))
       pygame.draw.rect(surface, BRIGHT, (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height), 2)
       pygame.draw.rect(surface, BRIGHT, (xp_bar_x, xp_bar_y, xp_bar_width * xp_percentage, xp_bar_height))

    def draw(self, surface, font, color):
        #self.draw_text(self.content, font, color, surface, 20, 20)
        self.draw_animation(surface)
        self.draw_footer(surface, font, color)