import pygame
import random
import string
from config import *

class HackingGame:
    def __init__(self, difficulty='MEDIUM'):
        self.font = TechMono[16]
        self.CHAR_WIDTH, self.CHAR_HEIGHT = self.font.size('X')
        
        # Set word length based on difficulty
        if difficulty == 'EASY':
            self.WORD_LENGTH = 4
        elif difficulty == 'MEDIUM':
            self.WORD_LENGTH = 6
        else:  # HARD
            self.WORD_LENGTH = 8

        self.MIN_WORDS = 6
        self.MAX_WORDS = 10
        self.attempts = 4
        self.cursor_pos = 0
        self.message = ""
        self.game_won = False
        self.game_over = False
        self.COLS = 12
        self.ROWS = 16
        self.UI_OFFSET_TOP = 7 * self.CHAR_HEIGHT
        self.BYTECODE_OFFSET_LEFT = 20
        self.BYTECODE_OFFSET_RIGHT = 24 * self.CHAR_WIDTH + 20
        self.COLUMN_OFFSET_LEFT = 7 * self.CHAR_WIDTH + 20
        self.COLUMN_OFFSET_RIGHT = 31 * self.CHAR_WIDTH + 20
        self.HISTORY_OFFSET_RIGHT = self.COLUMN_OFFSET_RIGHT + self.COLS * (self.CHAR_WIDTH + 2) + 20
        self.HISTORY_TOP = 13 * (self.CHAR_HEIGHT + 2) + self.UI_OFFSET_TOP
        self.KERNING = 2
        self.history = []
        self.BRACKET_PAIRS = {'(': ')', '[': ']', '{': '}', '<': '>'}
        self.selected_brackets = set()
        self.MIN_DISTANCE = 6
        self.word_list = self.load_words_from_file('./passcode/google-10000-english-usa-no-swears.txt', self.WORD_LENGTH)
        self.selected_words = self.select_similar_words(self.word_list, self.MIN_WORDS, self.MAX_WORDS)
        self.password = random.choice(self.selected_words)
        self.memory_dump, self.word_positions = self.generate_memory_dump(self.selected_words)
        self.BRACKET_CHARS = set(self.BRACKET_PAIRS.keys()) | set(self.BRACKET_PAIRS.values())
        self.enable_cheat = True

        self.end_animation_done = False
        self.animation_chars = []
        self.animation_timer = 0
        self.boot_sequence = self.generate_boot_sequence()
        self.boot_sequence_index = 0
        self.boot_text = ""
        self.boot_timer = 0
        self.chars_per_frame = random.randint(1, 3)  # Characters to type per frame
        self.line_delay = random.randint(5, 200)  # Milliseconds between lines
        self.last_type_time = 0
        self.visible_lines = 20

    def load_words_from_file(self, file_path, word_length):
        with open(file_path, 'r') as file:
            words = [line.strip().upper() for line in file if len(line.strip()) == word_length]
        if len(words) < self.MIN_WORDS:
            raise ValueError(f"Not enough {word_length}-letter words in the file. Found only {len(words)}.")
        return words

    def select_similar_words(self, word_list, min_words, max_words):
        password = random.choice(word_list)
        similar_words = [password]
        while len(similar_words) < max_words:
            word = random.choice(word_list)
            if sum(1 for a, b in zip(word, password) if a == b) > 0 and word not in similar_words:
                similar_words.append(word)
        return random.sample(similar_words, random.randint(min_words, len(similar_words)))

    def generate_memory_dump(self, word_list):
        junk_chars = list(string.punctuation)
        total_chars = 2 * self.ROWS * self.COLS
        memory_dump = [random.choice(junk_chars) for _ in range(total_chars)]
        word_positions = {}

        for word in word_list:
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                start_idx = random.randint(0, total_chars - len(word))
                if all(memory_dump[start_idx + i] in junk_chars for i in range(len(word))) and \
                   all(abs(start_idx - pos) >= self.MIN_DISTANCE + len(word) for pos in word_positions.values()):
                    for i, char in enumerate(word):
                        memory_dump[start_idx + i] = char
                    word_positions[word] = start_idx
                    placed = True
                attempts += 1
            if not placed:
                print(f"Warning: Could not place word '{word}' after 1000 attempts")

        return memory_dump, word_positions
    
    def draw_lose_animation(self, surface):
        if not hasattr(self, 'fall_speeds'):
            self.init_lose_animation(surface)

        surface.fill(BLACK)
        
        animation_done = True
        for col in range(self.total_cols):
            if self.fall_positions[col] < self.total_rows:
                animation_done = False
                for row in range(self.total_rows):
                    x = col * (self.CHAR_WIDTH + 2)
                    y = row * (self.CHAR_HEIGHT + 2)
                    
                    if row < self.fall_positions[col]:
                        char = '.'
                    else:
                        char_index = (col * self.total_rows + row) % len(self.memory_dump)
                        char = self.memory_dump[char_index]
                    
                    color = get_color('BRIGHT') if row >= self.fall_positions[col] else get_color('DIM')
                    char_surface = self.font.render(char, True, color)
                    surface.blit(char_surface, (x, y))
                
                self.fall_positions[col] += self.fall_speeds[col]
        
        self.animation_timer += 1
        
        # Type out "TERMINAL LOCKED" message on two lines
        message1 = "TERMINAL LOCKED"
        message2 = "PLEASE CONTACT AN ADMINISTRATOR"
        typed_chars = min(len(message1) + len(message2), self.animation_timer // 1)
        
        if typed_chars <= len(message1):
            typed_message1 = message1[:typed_chars]
            typed_message2 = ""
        else:
            typed_message1 = message1
            typed_message2 = message2[:typed_chars - len(message1)]
        
        text_surface1 = self.font.render(typed_message1, True, get_color('BRIGHT'))
        text_rect1 = text_surface1.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - self.CHAR_HEIGHT))
        surface.blit(text_surface1, text_rect1)
        
        text_surface2 = self.font.render(typed_message2, True, get_color('BRIGHT'))
        text_rect2 = text_surface2.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + self.CHAR_HEIGHT))
        surface.blit(text_surface2, text_rect2)
        
        if animation_done and typed_chars == len(message1) + len(message2) and self.animation_timer > (len(message1) + len(message2)) * 3 + 60:
            self.end_animation_done = True

        pygame.time.delay(50)  # Add delay between frames

    def init_lose_animation(self, surface):
        self.total_cols = surface.get_width() // (self.CHAR_WIDTH + 2)
        self.total_rows = surface.get_height() // (self.CHAR_HEIGHT + 2)
        
        min_fall_speed = 2
        max_fall_speed = 8
        
        self.fall_speeds = [random.randint(min_fall_speed, max_fall_speed) for _ in range(self.total_cols)]
        self.fall_positions = [0 for _ in range(self.total_cols)]

    def draw_win_animation(self, surface):
        current_time = pygame.time.get_ticks()
        
        if self.boot_sequence_index < len(self.boot_sequence):
            if not self.boot_text:
                self.boot_timer = current_time
            
            if current_time - self.last_type_time > 1:  # Check every frame
                if len(self.boot_text) < len(self.boot_sequence[self.boot_sequence_index]):
                    chars_to_add = min(self.chars_per_frame, 
                                       len(self.boot_sequence[self.boot_sequence_index]) - len(self.boot_text))
                    self.boot_text += self.boot_sequence[self.boot_sequence_index][len(self.boot_text):len(self.boot_text) + chars_to_add]
                    self.last_type_time = current_time
                elif current_time - self.last_type_time > self.line_delay:
                    self.boot_sequence_index += 1
                    self.boot_text = ""
                    self.chars_per_frame = random.randint(1, 3)  # Randomize typing speed for each line
        
        self.render_boot_screen(surface)
        
        if self.boot_sequence_index == len(self.boot_sequence) and current_time - self.last_type_time > 2000:
            self.end_animation_done = True

    def render_boot_screen(self, surface):
        surface.fill(BLACK)
        
        # Calculate the total number of lines to display
        total_lines = self.boot_sequence_index + (1 if self.boot_text else 0)
        
        # Calculate the start index for visible lines
        start_index = max(0, total_lines - self.visible_lines)
        
        y_offset = 10
        
        # Render completed lines
        for i, line in enumerate(self.boot_sequence[start_index:self.boot_sequence_index]):
            self.render_monospace_line(surface, line, 10, y_offset + i * (self.CHAR_HEIGHT + 2))
        
        # Render current line being typed
        if self.boot_text:
            self.render_monospace_line(surface, self.boot_text, 10, y_offset + (total_lines - start_index - 1) * (self.CHAR_HEIGHT + 2))
        
        # Draw blinking cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 10 + len(self.boot_text) * (self.CHAR_WIDTH)
            cursor_y = y_offset + (total_lines - start_index - 1) * (self.CHAR_HEIGHT + 2)
            pygame.draw.rect(surface, get_color('BRIGHT'), (cursor_x, cursor_y, self.CHAR_WIDTH, self.CHAR_HEIGHT))

    def render_monospace_line(self, surface, text, x, y):
        for i, char in enumerate(text):
            char_surface = self.font.render(char, True, get_color('BRIGHT'))
            surface.blit(char_surface, (x + i * (self.CHAR_WIDTH), y))

    def generate_boot_sequence(self):
        def generate_hex_address():
            return f"0x{random.randint(0, 0xFFFFFFFF):08X}"

        def generate_file_check():
            files = ['kernel.sys', 'bootmgr.exe', 'hal.dll', 'ntoskrnl.exe', 'bootvid.dll', 'ci.dll', 'cryptbase.dll', 'csrss.exe', 'smss.exe', 'winload.exe']
            file = random.choice(files)
            status = 'OK' if random.random() > 0.1 else 'CORRUPT'
            return f"Verifying {file}... {status}"

        def generate_binary_dump():
            return ''.join(random.choice('01') for _ in range(random.randint(16, 64)))

        def generate_mem_dump():
            return ' '.join([f"{random.randint(0, 255):02X}" for _ in range(random.randint(2, 16))])
        
        def generate_hex_dump():
            return ' '.join([generate_hex_address() for _ in range(random.randint(2, 6))])

        boot_sequence = [
            "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM",
            "COPYRIGHT 2075-2077 ROBCO INDUSTRIES",
            f"BIOS Version {random.randint(1, 9)}.{random.randint(0, 99):02d}",
            "",
            "Initializing Boot Sequence...",
            f"CPU: ROBCO-{random.randint(1000, 9999)} @ {random.randint(1, 5)}.{random.randint(0, 99):02d} GHz",
            f"Memory Test: {random.randint(64, 512)}K OK",
            "0x0000",
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            "",
            "Detecting Hardware...",
            "Motherboard: ROBCO-MB2075",
            f"Hard Drive: {random.randint(1, 10)}TB QUANTUM STORAGE",
            f"Network Adapter: ROBCO-NET {random.choice(['v1', 'v2', 'v3'])}",
            f"Graphics Adapter: ROBCO-VID {random.choice(['MK1', 'MK2', 'MK3'])}",
            f"Sound Card: ROBCO-AUD {random.choice(['Basic', 'Advanced', 'Pro'])}",
            "0x0000",
            generate_binary_dump(),
            generate_binary_dump(),
            generate_binary_dump(),
            generate_binary_dump(),
            "",
            "Initializing System Services...",
            "[OK] Power Management",
            "[OK] Thermal Control",
            "[OK] Fan Control",
            "[OK] Voltage Regulation",
            "0x0000",
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            "",
            "Loading Operating System...",
            f"ROBCO-OS v{random.randint(1, 9)}.{random.randint(0, 99):02d}.{random.randint(0, 999):03d}",
            "",
            "Mounting File Systems...",
            "[OK] /stat",
            "[OK] /radio",
            "[OK] /map",
            "[OK] /data",
            "[OK] /conf",
            "0x0000",
            generate_binary_dump(),
            generate_binary_dump(),
            generate_binary_dump(),
            generate_binary_dump(),
            "",
            "Starting Biometric Services...",
            "[OK] Heart Rate",
            "[OK] Oxygen Saturation",
            "[OK] Blood Alcohol Level",
            "0x0000",
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            generate_hex_dump(),
            "",
            "Starting Environmental Services...",
            "[OK] Temperature",
            "[OK] Humidity",
            "[OK] Pressure",
            "[OK] Altitude",
            "",
            "Performing file system check...",
        ]

        # Add file system checks
        for _ in range(random.randint(8, 15)):
            boot_sequence.append(generate_file_check())

        boot_sequence.extend([
            "",
            "Initializing memory...",
        ])

        # Add memory dump
        for _ in range(random.randint(15, 25)):
            boot_sequence.append(generate_hex_dump())

        boot_sequence.extend([
            "",
            "System initialization complete.",
            "All services started successfully.",
            "ROBCO Industries (TM) Termlink Protocol",
            "Establishing secure connection...",
            "Connection established.",
            "Booting...",
            "",
            "> "
        ])

        return boot_sequence

    def draw(self, surface):
        if self.game_won and not self.end_animation_done:
            self.draw_win_animation(surface)
        elif self.game_over and not self.end_animation_done:
            self.draw_lose_animation(surface)
        elif not self.end_animation_done:
            surface.fill(BLACK)
            self.draw_ui(surface)
            self.draw_bytecode(surface)
            self.draw_memory_dump(surface)
            self.display_history(surface)
        # If end_animation_done is True, we don't draw anything

    def draw_ui(self, surface):
        robco_surface = self.font.render("Welcome to ROBCO Industries (TM) Termlink", True, get_color('BRIGHT'))
        surface.blit(robco_surface, (20, self.CHAR_HEIGHT))

        password_req_surface = self.font.render("Password Required", True, get_color('BRIGHT'))
        surface.blit(password_req_surface, (20, 3 * self.CHAR_HEIGHT))

        label_surface = self.font.render("Attempts Remaining:", True, get_color('BRIGHT'))
        surface.blit(label_surface, (20, 5 * self.CHAR_HEIGHT))

        cheat_surface = self.font.render(f"{self.password}", True, get_color('DIM'))
        if self.enable_cheat:
            surface.blit(cheat_surface, (20, 6 * self.CHAR_HEIGHT))

        for i in range(4):
            rect_color = get_color('BRIGHT') if i < self.attempts else BLACK
            rect_x = 20 + label_surface.get_width() + 10 + i * (self.CHAR_WIDTH + 5)
            pygame.draw.rect(surface, rect_color, pygame.Rect(rect_x, 5 * self.CHAR_HEIGHT, self.CHAR_WIDTH, self.CHAR_HEIGHT))

    def draw_memory_dump(self, surface):
        bracket_start, bracket_end = self.get_bracket_pair(divmod(self.cursor_pos, self.COLS))
        
        for i, char in enumerate(self.memory_dump):
            row, col = divmod(i, self.COLS)
            x_offset = self.COLUMN_OFFSET_LEFT if row < self.ROWS else self.COLUMN_OFFSET_RIGHT
            x_position = x_offset + (col % self.COLS) * (self.CHAR_WIDTH + 2)
            y_position = (row % self.ROWS) * (self.CHAR_HEIGHT + 2) + self.UI_OFFSET_TOP
            
            highlight = i == self.cursor_pos or (bracket_start is not None and bracket_end is not None and 
                        bracket_start <= i <= bracket_end and (bracket_start, bracket_end) not in self.selected_brackets)

            if highlight:
                pygame.draw.rect(surface, get_color('BRIGHT'), 
                                 (x_position - 1, y_position, self.CHAR_WIDTH + 2, self.CHAR_HEIGHT))
                text_color = BLACK
            else:
                text_color = get_color('BRIGHT')
            
            text_surface = self.font.render(char, True, text_color)
            surface.blit(text_surface, (x_position, y_position))

        current_word, start_idx = self.get_word_at_cursor()
        if current_word:
            for i in range(len(current_word)):
                idx = start_idx + i
                row, col = divmod(idx, self.COLS)
                x_offset = self.COLUMN_OFFSET_LEFT if row < self.ROWS else self.COLUMN_OFFSET_RIGHT
                x_position = x_offset + (col % self.COLS) * (self.CHAR_WIDTH + 2)
                y_position = (row % self.ROWS) * (self.CHAR_HEIGHT + 2) + self.UI_OFFSET_TOP
                pygame.draw.rect(surface, get_color('BRIGHT'), 
                                 (x_position - 1, y_position, self.CHAR_WIDTH + 2, self.CHAR_HEIGHT))
                text_surface = self.font.render(current_word[i], True, BLACK)
                surface.blit(text_surface, (x_position, y_position))

    def draw_bytecode(self, surface):
        for row in range(self.ROWS):
            y_position = row * (self.CHAR_HEIGHT + 2) + self.UI_OFFSET_TOP
            address_left = hex((0xF000 + (row * 12)))[2:].upper().zfill(4)
            address_right = hex((0xF000) + (row + self.ROWS) * 12)[2:].upper().zfill(4)
            surface.blit(self.font.render(f"0x{address_left}", True, get_color('BRIGHT')), (self.BYTECODE_OFFSET_LEFT, y_position))
            surface.blit(self.font.render(f"0x{address_right}", True, get_color('BRIGHT')), (self.BYTECODE_OFFSET_RIGHT, y_position))

    def check_game_end(self):
        return (self.game_won or self.game_over) and self.end_animation_done

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self.cursor_pos = self.move_cursor(event.key)
            elif event.key == pygame.K_RETURN:
                selected_word = self.get_selected_word()
                if selected_word:
                    self.check_password(selected_word)
                else:
                    self.handle_bracket_selection()
            elif event.key == pygame.K_ESCAPE:
                self.game_over = True

    def move_cursor(self, key):
        row, col = divmod(self.cursor_pos, self.COLS)
        total_rows = 2 * self.ROWS
        total_chars = total_rows * self.COLS

        current_word, current_start = self.get_word_at_cursor()

        if key == pygame.K_RIGHT:
            if current_word:
                new_pos = current_start + len(current_word)
            else:
                new_pos = self.cursor_pos + 1
            if new_pos % self.COLS == 0:  # Wrap to other column
                new_pos = (row + self.ROWS) * self.COLS
            self.cursor_pos = new_pos % total_chars
        elif key == pygame.K_LEFT:
            if current_word:
                new_pos = current_start - 1
            else:
                new_pos = self.cursor_pos - 1
            if new_pos < row * self.COLS or new_pos >= (row + 1) * self.COLS:  # Wrap to other column
                new_pos = ((row + self.ROWS) * self.COLS) + self.COLS - 1
            self.cursor_pos = new_pos % total_chars
        elif key == pygame.K_DOWN:
            self.cursor_pos = (self.cursor_pos + self.COLS) % total_chars
        elif key == pygame.K_UP:
            self.cursor_pos = (self.cursor_pos - self.COLS) % total_chars

        return self.cursor_pos

    def get_bracket_pair(self, cursor_pos):
        row, col = cursor_pos
        index = row * self.COLS + col
        char = self.memory_dump[index]

        if char in self.BRACKET_CHARS:
            line_start = (index // self.COLS) * self.COLS
            line_end = line_start + self.COLS

            if char in self.BRACKET_PAIRS:
                for i in range(index + 1, line_end):
                    if self.memory_dump[i] == self.BRACKET_PAIRS[char]:
                        return index, i
            else:
                for i in range(index - 1, line_start - 1, -1):
                    if self.memory_dump[i] in self.BRACKET_PAIRS and self.BRACKET_PAIRS[self.memory_dump[i]] == char:
                        return i, index

        return None, None

    def handle_bracket_selection(self):
        start, end = self.get_bracket_pair(divmod(self.cursor_pos, self.COLS))
        if start is not None and end is not None and (start, end) not in self.selected_brackets:
            between_brackets = self.memory_dump[start+1:end]
            if not any(start < word_start < end or start < word_start + len(word) <= end 
                       for word, word_start in self.word_positions.items()):
                self.selected_brackets.add((start, end))
                self.attempts, message = self.remove_dud_or_reset_guesses()
                self.history.append((message,))

    def remove_dud_or_reset_guesses(self):
        if random.random() < 0.5 and len(self.word_positions) > 1:
            dud_words = [word for word in self.word_positions.keys() if word != self.password]
            if dud_words:
                dud_word = random.choice(dud_words)
                start_idx = self.word_positions[dud_word]
                for i in range(len(dud_word)):
                    self.memory_dump[start_idx + i] = '.'
                del self.word_positions[dud_word]
                return self.attempts, "Dud removed"
        else:
            return 4, "Tries reset"
        return self.attempts, "No change"

    def get_word_at_cursor(self):
        for word, start_idx in self.word_positions.items():
            if start_idx <= self.cursor_pos < start_idx + len(word):
                return word, start_idx
        return None, self.cursor_pos

    def get_selected_word(self):
        for word, start_pos in self.word_positions.items():
            if start_pos <= self.cursor_pos < start_pos + len(word):
                return word
        return None

    def check_password(self, selected_word):
        if selected_word == self.password:
            self.history.append((selected_word, "Access Granted"))
            self.message = "Access Granted!"
            self.game_won = True
        else:
            self.attempts -= 1
            likeness = sum(1 for a, b in zip(selected_word, self.password) if a == b)
            self.history.append((selected_word, "Entry Denied", f"{likeness}/{self.WORD_LENGTH} correct"))
            if self.attempts == 0:
                self.message = "Access Denied!"
                self.game_over = True
            else:
                self.message = f"Incorrect. {self.attempts} attempts left."

    def display_history(self, surface):
        y_offset = 0
        for entry in reversed(self.history[-5:]):
            if len(entry) == 1:
                message = entry[0]
                text_surface = self.font.render(f"> {message}", True, get_color('BRIGHT'))
                surface.blit(text_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
            elif len(entry) == 2:
                word, result = entry
                word_surface = self.font.render(f"> {word}", True, get_color('BRIGHT'))
                result_surface = self.font.render(f"> {result}", True, get_color('BRIGHT'))
                surface.blit(result_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
                surface.blit(word_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
            elif len(entry) == 3:
                word, result, likeness = entry
                likeness_surface = self.font.render(f"> {likeness}", True, get_color('BRIGHT'))
                result_surface = self.font.render(f"> {result}", True, get_color('BRIGHT'))
                word_surface = self.font.render(f"> {word}", True, get_color('BRIGHT'))
                surface.blit(likeness_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
                surface.blit(result_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
                surface.blit(word_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP - y_offset))
                y_offset += self.CHAR_HEIGHT + 2
        self.display_active_word(surface)

    def display_end_screen(self, surface, message, color):
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 48)
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(text_surface, text_rect)
        
        pygame.display.flip()

    def display_active_word(self, surface):
        current_word, _ = self.get_word_at_cursor()
        active_word = current_word if current_word else self.memory_dump[self.cursor_pos]
        active_word_surface = self.font.render(f"> {active_word}", True, get_color('BRIGHT'))
        surface.blit(active_word_surface, (self.HISTORY_OFFSET_RIGHT, self.HISTORY_TOP + (2 * (self.CHAR_HEIGHT + 2))))