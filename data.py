import pygame
from config import *
from settings import settings

class DataPage:
    def __init__(self):
        self.content = "Phasellus at dui eu nisl hendrerit gravida. Aliquam erat volutpat."
        self.sub_tabs = ["INFO", "SETTINGS"]
        self.current_sub_tab = 0
        self.color_options = list(COLOR_SCHEMES.keys())
        self.selected_color = self.color_options.index(settings.get('ui_color'))
        self.color_menu_open = False
        self.color_menu_index = 0
        self.settings_options = ["UI Color", "Option 2", "Option 3"]  # Add more options as needed
        self.current_setting = 0
    
    def draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def draw_sub_tabs(self, surface, font, color):
        tab_width = SCREEN_WIDTH // 8  # Adjust this value to change the spacing between tabs
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

    def draw_settings(self, surface, font, color):
        option_width = SCREEN_WIDTH // 4  # Width for the option text
        value_width = SCREEN_WIDTH // 4 - 20  # Width for the value/selection   

        for i, option in enumerate(self.settings_options):
            rect = pygame.Rect(20, 100 + i * 30, option_width + value_width, 25)    

            # Determine the background color and text color
            if i == self.current_setting:
                if option == "UI Color" and self.color_menu_open:
                    bg_color = get_color('DIM')
                    text_color = get_color('BRIGHT')
                else:
                    bg_color = get_color('BRIGHT')
                    text_color = BLACK
            else:
                bg_color = BLACK
                text_color = get_color('BRIGHT')

            # Draw the background
            pygame.draw.rect(surface, bg_color, rect)

            # Draw the option text
            self.draw_text(option, RobotoB[18], text_color, surface, rect.x + 10, rect.y + 1)   

            # Draw the current value
            if option == "UI Color":
                current_color = self.color_options[self.selected_color]
                value_text = RobotoB[18].render(current_color, True, text_color)
                value_rect = value_text.get_rect(right=rect.right - 10, centery=rect.centery)
                surface.blit(value_text, value_rect)    

        # Draw the color menu if open
        if self.color_menu_open and self.current_setting == self.settings_options.index("UI Color"):
            option_rect = pygame.Rect(20, 100 + self.current_setting * 30, option_width + value_width, 25)
            for i, color_option in enumerate(self.color_options):
                if i == 0:
                    # First option in line with the current option
                    rect = pygame.Rect(option_rect.right + 5, option_rect.y, value_width, 25)
                else:
                    # Subsequent options drop down
                    rect = pygame.Rect(option_rect.right + 5, option_rect.y + i * 30, value_width, 25)
                
                if i == self.color_menu_index:
                    pygame.draw.rect(surface, get_color('BRIGHT'), rect)
                    text_color = BLACK
                else:
                    pygame.draw.rect(surface, BLACK, rect)
                    text_color = get_color('BRIGHT')
                self.draw_text(color_option, RobotoB[18], text_color, surface, rect.x + 10, rect.y + 1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_1, pygame.K_2]:
                self.current_sub_tab = event.key - pygame.K_1
            elif self.current_sub_tab == 1:  # SETTINGS tab
                if event.key == pygame.K_UP:
                    if self.color_menu_open:
                        self.color_menu_index = (self.color_menu_index - 1) % len(self.color_options)
                    else:
                        self.current_setting = (self.current_setting - 1) % len(self.settings_options)
                elif event.key == pygame.K_DOWN:
                    if self.color_menu_open:
                        self.color_menu_index = (self.color_menu_index + 1) % len(self.color_options)
                    else:
                        self.current_setting = (self.current_setting + 1) % len(self.settings_options)
                elif event.key == pygame.K_RETURN:
                    if self.settings_options[self.current_setting] == "UI Color":
                        if not self.color_menu_open:
                            self.color_menu_open = True
                        else:
                            self.selected_color = self.color_menu_index
                            settings.set('ui_color', self.color_options[self.selected_color])
                            self.color_menu_open = False

    def draw(self, surface, font, color):
        self.draw_sub_tabs(surface, font, color)
        if self.current_sub_tab == 0:
            self.draw_text(self.content, font, color, surface, 20, 100)
        else:
            self.draw_settings(surface, font, color)