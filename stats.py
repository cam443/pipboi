import pygame
import os
import random

class StatPage:
    def __init__(self):
        self.content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vehicula."
        
        # Load leg frames at original size
        self.leg_frames = [pygame.image.load(os.path.join('images/legs', f'{i}.png')).convert_alpha() for i in range(1, 9)]
        self.current_leg_frame = 0
        
        # Load head frames and select a random head at original size
        self.head_frames = [pygame.image.load(os.path.join('images/head', f'{i}.png')).convert_alpha() for i in range(1, 8)]
        self.head_frame = random.choice(self.head_frames)
        
        # Resizing scale factor
        self.scale_factor = 0.75  # Adjust this factor as needed

        # Supersampling factor
        self.supersample_factor = 2

        # Resize images
        self.resize_images()

        # Animation timing
        self.leg_frame_delay = 200  # milliseconds
        self.last_update = pygame.time.get_ticks()

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
        leg_rect = leg_image.get_rect(center=(200, 200))  # Center on screen (400x320)
        surface.blit(leg_image, leg_rect.topleft)
        
        head_rect = self.head_frame.get_rect(center=(198, 113))  # Position above legs
        surface.blit(self.head_frame, head_rect.topleft)

    def draw(self, surface, font, color):
        #self.draw_text(self.content, font, color, surface, 20, 20)
        self.draw_animation(surface)
