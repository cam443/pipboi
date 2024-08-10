import pygame
import numpy as np
import time

# Overlay class
class Overlay:
    def __init__(self, image_path, width, height, strength=1, scale_factor=1.5):
        self.image_path = image_path
        self.width = width
        self.height = height
        self.strength = strength  # Store the strength value
        self.scale_factor = scale_factor  # Factor to scale the image up
        self.image = pygame.image.load(self.image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (int(self.width * self.scale_factor), int(self.height * self.scale_factor)))
    
    def render(self, surface):
        temp_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
        temp_surface.blit(self.image, (0, 0))
        for _ in range(self.strength):  # Apply the overlay multiple times
            surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_ADD)

# Scanline class
class Scanline:
    def __init__(self, image_path, width, height, screen_height, speed=5, delay=2, strength=2):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.speed = speed
        self.delay = delay
        self.last_move_time = time.time()
        self.rect.y = -height
        self.screen_height = screen_height
        self.strength = strength  # Store the strength value

    def update(self):
        current_time = time.time()
        if current_time - self.last_move_time > self.delay:
            self.rect.y += self.speed
            if self.rect.y >= self.screen_height:
                self.rect.y = -self.rect.height
                self.last_move_time = current_time

    def render(self, surface, color):
        tinted_image = self.image.copy()
        tinted_image.fill(color, special_flags=pygame.BLEND_MULT)
        for _ in range(self.strength):  # Apply the overlay multiple times
            surface.blit(tinted_image, self.rect, special_flags=pygame.BLEND_ADD)

#CRT Distortion Class
class CRTShader:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.shader_surface = pygame.Surface(screen_size)
        self.distortion = 0.08  # Adjust this value to change the curvature

    def apply(self, surface):
        width, height = self.screen_size
        pixels = pygame.surfarray.array3d(surface).astype(float)

        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        xx, yy = np.meshgrid(x, y)

        d = np.sqrt(xx*xx + yy*yy)

        # Outward bulge distortion
        d_barrel = d / (1 - self.distortion * (d**2 - 1))

        source_x = ((d_barrel/d * xx + 1) / 2 * (width - 1))
        source_y = ((d_barrel/d * yy + 1) / 2 * (height - 1))

        # Bilinear interpolation
        x0 = np.floor(source_x).astype(int)
        x1 = np.clip(x0 + 1, 0, width - 1)
        y0 = np.floor(source_y).astype(int)
        y1 = np.clip(y0 + 1, 0, height - 1)

        x0 = np.clip(x0, 0, width - 1)
        y0 = np.clip(y0, 0, height - 1)

        wa = (x1 - source_x) * (y1 - source_y)
        wb = (x1 - source_x) * (source_y - y0)
        wc = (source_x - x0) * (y1 - source_y)
        wd = (source_x - x0) * (source_y - y0)

        distorted = (wa[:, :, np.newaxis] * pixels[x0, y0] +
                     wb[:, :, np.newaxis] * pixels[x0, y1] +
                     wc[:, :, np.newaxis] * pixels[x1, y0] +
                     wd[:, :, np.newaxis] * pixels[x1, y1])

        vignette = np.maximum(1 - d * 0, 0.0)  # Adjusted from 0.5 to 1
        distorted = (distorted * vignette[:, :, np.newaxis]).astype(np.uint8)

        distorted = np.transpose(distorted, (1, 0, 2))  # Correct the dimensions to match the surface

        pygame.surfarray.blit_array(self.shader_surface, distorted)

        return self.shader_surface