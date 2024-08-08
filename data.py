import pygame

class DataPage:
    def __init__(self):
        self.content = "Phasellus at dui eu nisl hendrerit gravida. Aliquam erat volutpat."
    
    def draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def draw(self, surface, font, color):
        self.draw_text(self.content, font, color, surface, 20, 80)
