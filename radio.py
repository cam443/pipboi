import pygame
import os
import time
import random
import configparser
import datetime
import numpy as np
from settings import settings
from config import *
from pydub import AudioSegment
import json
import threading
from collections import deque
from mutagen import File as MutagenFile
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)


def load_cached_waveform(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            data = json.load(f)
        return data['waveform'], data['num_samples'], data['frame_rate'], data['audio_duration']
    return None, None, None, None

def load_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples())
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)
    return samples, len(samples), audio.frame_rate, audio.duration_seconds

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def precompute_waveform(samples, height, smoothing=10, zoom_factor=1.0):
    max_amplitude = np.max(np.abs(samples))
    normalized_samples = samples / max_amplitude
    smoothed_samples = moving_average(normalized_samples, smoothing)
    scaled_samples = smoothed_samples * (height // 2) + (height // 2)
    return scaled_samples

class RadioPage:
    def __init__(self):
        self.stations = self.load_stations()
        self.font = RobotoR[24]
        self.bold = RobotoB[24]
        self.load_state()
        pygame.mixer.init()
        self.volume = settings.get('radio_volume', 0.5)
        pygame.mixer.music.set_volume(self.volume / 100)
        self.waveform_cache_dir = 'waveform_cache'
        os.makedirs(self.waveform_cache_dir, exist_ok=True)

        self.station_logos = {}
        self.stations = self.load_stations()
        self.current_station = None
        self.current_artist = "ERROR"
        self.current_title = "Title not Found"

        self.song_count = 0
        self.set_new_interlude_interval()
        self.news_sequence = []
        self.is_playing_news = False

        self.scroll_offset = 0
        self.scroll_speed = 10  # Pixels to move per scroll
        self.scroll_interval = .5  # Time between scrolls in seconds
        self.max_text_width = 280
        self.last_scroll_time = time.time()
        self.scroll_padding = 50

        self.current_waveform = None
        self.offset = 0  # Initialize the offset for scrolling
        self.slice_width = SCREEN_WIDTH // 2  # Width of the waveform slice to render
        self.zoom_factor = 15  # Adjust this value to change the zoom level
        self.waveform_height = SCREEN_HEIGHT // 2
        self.right_padding = 20
        self.top_padding = 80  # Adjust this value to move the grid higher
        self.grid_width = 300  # Width of the grid
        self.grid_height = 200
        self.clock = pygame.time.Clock()
        self.start_time = 0
        self.use_pregenerated_waveforms = False  # Flag to switch between pregenerated and live waveforms
        self.waveform_thread = None
        self.waveform_ready = threading.Event()
        self.current_waveform = deque()  # Use deque for waveform data
        saved_station = settings.get('radio_station')
        if saved_station:
            self.select_station(saved_station)
        

    def load_stations(self):
        stations = {}
        base_path = 'sounds/radio'
        supported_formats = ('.ogg', '.wav', '.mp3', '.flac')
        for folder in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder)
            if os.path.isdir(folder_path):
                songs = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_formats)]
                interludes = []
                interlude_path = os.path.join(folder_path, 'interludes')
                if os.path.exists(interlude_path):
                    interludes = [os.path.join(interlude_path, f) for f in os.listdir(interlude_path) if f.lower().endswith(supported_formats)]
                
                news = []
                news_path = os.path.join(folder_path, 'news')
                if os.path.exists(news_path):
                    news_intros = [os.path.join(news_path, 'news_intro', f) for f in os.listdir(os.path.join(news_path, 'news_intro')) if f.lower().endswith(supported_formats)]
                    news_intros2 = [os.path.join(news_path, 'news_intro', 'news_intro2', f) for f in os.listdir(os.path.join(news_path, 'news_intro', 'news_intro2')) if f.lower().endswith(supported_formats)]
                    news_clips = [os.path.join(news_path, f) for f in os.listdir(news_path) if f.lower().endswith(supported_formats) and os.path.isfile(os.path.join(news_path, f))]
                    news_outros = [os.path.join(news_path, 'news_outro', f) for f in os.listdir(os.path.join(news_path, 'news_outro')) if f.lower().endswith(supported_formats)]
                    news_outros2 = [os.path.join(news_path, 'news_outro', 'somemusic', f) for f in os.listdir(os.path.join(news_path, 'news_outro', 'somemusic')) if f.lower().endswith(supported_formats)]
                    news = {
                        'intros': news_intros,
                        'intros2': news_intros2,
                        'clips': news_clips,
                        'outros': news_outros,
                        'outros2': news_outros2
                    }
                
                if songs:
                    config = configparser.ConfigParser()
                    config.read(os.path.join(folder_path, 'station.ini'))
                    station_name = config.get('metadata', 'station_name', fallback=folder)
                    ordered = config.getboolean('metadata', 'ordered', fallback=False)
                    logo_file = config.get('metadata', 'logo', fallback=None)
                    has_news = config.getboolean('metadata', 'news', fallback=False)
                    songs = [os.path.join(folder_path, f) for f in songs]
                    if not ordered:
                        random.shuffle(songs)
                    stations[station_name] = {
                        'songs': songs,
                        'ordered': ordered,
                        'logo': os.path.join(folder_path, logo_file) if logo_file else None,
                        'folder_path': folder_path,
                        'interludes': interludes,
                        'has_news': has_news,
                        'news': news
                    }
        return stations
    
    def load_station_logo(self, station_name):
        logo_path = self.stations[station_name]['logo']
        if logo_path and os.path.exists(logo_path):
            logo = pygame.image.load(logo_path).convert_alpha()
            return pygame.transform.scale(logo, (300, 50))  # Scale to 300x50
        return None

    def load_state(self):
        self.current_station = settings.get('radio_station')
        self.song_index = 0
        self.current_song = None
        self.set_selected_index()

    def set_selected_index(self):
        if self.current_station:
            station_names = list(self.stations.keys())
            if self.current_station in station_names:
                self.selected_index = station_names.index(self.current_station)
            else:
                self.current_station = None
                self.selected_index = 0
        else:
            self.selected_index = 0

    def save_state(self):
        settings.set('radio_station', self.current_station)

    def select_station(self, station_name):
        if station_name in self.stations:
            self.current_station = station_name
            self.song_index = 0
            self.is_playing_news = False
            if not self.stations[self.current_station]['ordered']:
                random.shuffle(self.stations[self.current_station]['songs'])

            # Check if the station has interludes and play one if available
            if self.stations[self.current_station]['interludes']:
                self.play_interlude()
            elif self.stations[self.current_station]['has_news']:
                self.play_news()
            else:
                self.play_song()

            self.save_state()
            self.set_selected_index()
            self.song_count = 0
            

    def set_new_interlude_interval(self):
        self.interlude_interval = random.randint(4, 8)
        logging.debug(f"New interlude interval set: {self.interlude_interval}")

    def play_song(self):
        if self.current_station:
            logging.debug(f"Current interlude interval: {self.interlude_interval}")
            logging.debug(f"Current song count: {self.song_count}")

            if self.song_count >= self.interlude_interval:
                if self.stations[self.current_station]['has_news']:
                    self.play_news()
                elif self.stations[self.current_station]['interludes']:
                    self.play_interlude()
                self.song_count = 0
            else:
                songs = self.stations[self.current_station]['songs']
                if songs:
                    self.current_song = songs[self.song_index]
                    logging.debug(f"Playing song: {self.current_song}")
                    pygame.mixer.music.load(self.current_song)
                    pygame.mixer.music.play()
                    self.start_time = pygame.time.get_ticks()
                    self.load_waveform(self.current_song)
                    self.update_now_playing()
                    self.song_count += 1
                else:
                    self.current_song = None
                    self.current_artist = "Unknown Artist"
                    self.current_title = "Unknown Title"

    def play_news(self):
        news = self.stations[self.current_station]['news']
        if news:
            self.news_sequence = [
                random.choice(news['intros']),
                random.choice(news['intros2']),
                random.choice(news['clips']),
                random.choice(news['outros']),
                random.choice(news['outros2'])
            ]
            self.is_playing_news = True
            self.play_next_news_clip()

    def play_next_news_clip(self):
        if self.news_sequence:
            clip = self.news_sequence.pop(0)
            logging.debug(f"Playing news clip: {clip}")
            pygame.mixer.music.load(clip)
            pygame.mixer.music.play()
            self.start_time = pygame.time.get_ticks()
            self.load_waveform(clip)
            self.current_artist = "News"
            self.current_title = "Galaxy News Radio"
        else:
            self.is_playing_news = False
            self.song_count = 0
            self.set_new_interlude_interval()
            self.play_song()

    def play_interlude(self):
        interludes = self.stations[self.current_station]['interludes']
        if interludes:
            interlude = random.choice(interludes)
            logging.debug(f"Playing interlude: {interlude}")
            pygame.mixer.music.load(interlude)
            pygame.mixer.music.play()
            self.start_time = pygame.time.get_ticks()
            self.current_artist = "Radio Host"
            self.current_title = "Interlude"
            self.load_waveform(interlude)
            self.song_count = 0
            self.set_new_interlude_interval()  # Set a new interval after playing an interlude
        else:
            # If no interludes are available, play a regular song
            self.play_song()

    
    def get_current_host(self):
        current_hour = datetime.datetime.now().hour
        if 6 <= current_hour < 12:
            return "Morning Host"
        elif 12 <= current_hour < 18:
            return "Afternoon Host"
        elif 18 <= current_hour < 24:
            return "Evening Host"
        else:
            return "Night Host"

    def update_now_playing(self):
        if self.current_song:
            try:
                audio = MutagenFile(self.current_song)
                if audio is not None:
                    if 'artist' in audio:
                        self.current_artist = audio['artist'][0]
                    elif 'TPE1' in audio:  # ID3 tag for artist
                        self.current_artist = audio['TPE1'].text[0]
                    else:
                        self.current_artist = "Unknown Artist"

                    if 'title' in audio:
                        self.current_title = audio['title'][0]
                    elif 'TIT2' in audio:  # ID3 tag for title
                        self.current_title = audio['TIT2'].text[0]
                    else:
                        self.current_title = os.path.splitext(os.path.basename(self.current_song))[0]
                else:
                    self.current_artist = "Unknown Artist"
                    self.current_title = os.path.splitext(os.path.basename(self.current_song))[0]
            except Exception as e:
                logging.error(f"Error reading metadata: {e}")
                self.current_artist = "Unknown Artist"
                self.current_title = os.path.splitext(os.path.basename(self.current_song))[0]
        else:
            self.current_artist = "Unknown Artist"
            self.current_title = "Unknown Title"

    def next_song(self):
        if self.current_station:
            songs = self.stations[self.current_station]['songs']
            ordered = self.stations[self.current_station]['ordered']
            if ordered:
                self.song_index = (self.song_index + 1) % len(songs)
            else:
                self.song_index = random.randint(0, len(songs) - 1)
            self.play_song()
            self.save_state()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.stations)
                self.select_station(list(self.stations.keys())[self.selected_index])
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.stations)
                self.select_station(list(self.stations.keys())[self.selected_index])
            elif event.key == pygame.K_LEFT:
                self.adjust_volume(-5)
            elif event.key == pygame.K_RIGHT:
                self.adjust_volume(5)

    def adjust_volume(self, change):
        self.volume = max(0, min(100, self.volume + change))
        pygame.mixer.music.set_volume(self.volume / 100)
        settings.set('radio_volume', self.volume)

    def load_waveform(self, song_path):
        logging.debug(f"Loading waveform for: {song_path}")
        self.waveform_ready.clear()
        self.waveform_thread = threading.Thread(target=self.generate_waveform, args=(song_path,))
        self.waveform_thread.start()

    def generate_waveform(self, song_path):
        if self.use_pregenerated_waveforms:
            cache_path = os.path.join(self.waveform_cache_dir, os.path.splitext(os.path.basename(song_path))[0] + '.npy')
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    data = np.load(f, allow_pickle=True).item()
                self.current_waveform = data['waveform']
                self.total_samples = data['num_samples']
                self.audio_duration = data['audio_duration']
                self.waveform_ready.set()
                return
        # Fallback to live generation if pregenerated waveform is not available
        samples, num_samples, frame_rate, audio_duration = load_audio(song_path)
        self.current_waveform = precompute_waveform(samples, self.waveform_height, smoothing=50, zoom_factor=self.zoom_factor)
        self.total_samples = num_samples
        self.audio_duration = audio_duration
        self.waveform_ready.set()
        logging.debug(f"Waveform generated for: {song_path}")

    def draw_ticks(self, surface, box_x, box_y, box_width, box_height, tick_spacing=25, long_tick_length=10, short_tick_length=5):
        # Draw long ticks on the bottom
        for x in range(box_x, box_x + box_width, tick_spacing):
            pygame.draw.line(surface, get_color('BRIGHT'), (x, box_y + box_height), (x, box_y + box_height - long_tick_length), 2)

        # Draw long ticks on the right
        for y in range(box_y, box_y + box_height, tick_spacing):
            pygame.draw.line(surface, get_color('BRIGHT'), (box_x + box_width, y), (box_x + box_width - long_tick_length, y), 2)

        for x in range(box_x, box_x + box_width, 5):
            pygame.draw.line(surface, get_color('BRIGHT'), (x, box_y + box_height), (x, box_y + box_height - short_tick_length), 1)

        # Draw long ticks on the right
        for y in range(box_y, box_y + box_height, 5):
            pygame.draw.line(surface, get_color('BRIGHT'), (box_x + box_width, y), (box_x + box_width - short_tick_length, y), 1)

        # Draw the main border
        pygame.draw.line(surface, get_color('BRIGHT'), (box_x, box_y + box_height), (box_x + box_width, box_y + box_height), 2)
        pygame.draw.line(surface, get_color('BRIGHT'), (box_x + box_width, box_y), (box_x + box_width, box_y + box_height), 2)

    def draw_waveform(self, surface):
        if not self.current_station or self.current_station == "Radio Off":
            # Draw random noise for "Radio Off" or no station selected
            box_x = SCREEN_WIDTH // 2
            box_y = self.top_padding
            box_width = self.grid_width 
            box_height = self.grid_height

            center_y = box_y + box_height // 2
            amplitude = box_height // 64  # Reduce amplitude to 1/4 of the box height

            prev_x, prev_y = box_x, center_y
            for i in range(self.slice_width - 25):
                x = box_x + i
                y = center_y + random.randint(-amplitude, amplitude)
                pygame.draw.line(surface, get_color('BRIGHT'), (prev_x, prev_y), (x, y), 3)
                prev_x, prev_y = x, y
            return

        if not self.waveform_ready.is_set():
            return  # Do not draw until waveform is ready

        # Calculate the current position in the song
        current_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
        if current_time > self.audio_duration:
            current_time = current_time % self.audio_duration

        # Calculate the current sample index based on the audio position
        self.sample_index = int((current_time / self.audio_duration) * len(self.current_waveform))

        # Calculate the number of samples to display in the slice based on the zoom factor
        samples_per_pixel = int(self.zoom_factor)
        slice_start = self.sample_index
        slice_end = slice_start + (self.slice_width * samples_per_pixel)

        # Draw the waveform inside the box
        box_x = SCREEN_WIDTH // 2
        box_y = self.top_padding
        box_width = self.grid_width 
        box_height = self.grid_height

        prev_x, prev_y = box_x, box_y + int(self.current_waveform[slice_start] * (box_height / self.waveform_height))
        for i in range(self.slice_width - 25):
            x = box_x + i
            sample_idx = slice_start + (i * samples_per_pixel)
            if sample_idx >= len(self.current_waveform):
                break
            y = box_y + int(self.current_waveform[sample_idx] * (box_height / self.waveform_height))
            pygame.draw.line(surface, get_color('BRIGHT'), (prev_x, prev_y), (x, y), 3)
            prev_x, prev_y = x, y


    def draw(self, surface, font, color):
        # Draw stations list
        y = 100
        for i, station in enumerate(self.stations):
            rect = pygame.Rect(20, y, SCREEN_WIDTH // 2 - 40, 30)
            if i == self.selected_index:
                pygame.draw.rect(surface, get_color('BRIGHT'), rect)
                text_color = BLACK
            else:
                text_color = get_color('BRIGHT')
            self.draw_text(station, font, text_color, surface, rect.x + 10, rect.y)
            y += 40

        # Draw volume bar
        volume_width = int((self.volume / 100) * (SCREEN_WIDTH // 2 - 110))
        pygame.draw.rect(surface, get_color('BRIGHT'), (412, 295, SCREEN_WIDTH // 2 - 110, 25), 3)
        pygame.draw.rect(surface, get_color('BRIGHT'), (412, 295, volume_width, 25))
        pygame.draw.rect(surface, get_color('BRIGHT'), (320, 295, 90, 25))
        self.draw_text(f"VOL: {int(self.volume)}", self.bold, BLACK, surface, 322, 293)

        # Draw Now Playing
        artist_text = self.bold.render(self.current_artist, True, get_color('BRIGHT'))
        title_text = self.font.render(self.current_title, True, get_color('BRIGHT'))
        
        artist_width = artist_text.get_width()
        title_width = title_text.get_width()
        
        # Update scroll offset if needed
        current_time = time.time()
        if current_time - self.last_scroll_time >= self.scroll_interval:
            self.scroll_offset += self.scroll_speed
            self.last_scroll_time = current_time
        
        # Calculate the center position for the text
        center_x = SCREEN_WIDTH - (SCREEN_WIDTH // 4) - 10
        
        # Draw artist text
        artist_rect = pygame.Rect(0, 0, self.max_text_width, artist_text.get_height())
        artist_rect.midtop = (center_x, 390)
        if artist_width > self.max_text_width:
            # Create a surface with padding
            scroll_surface = pygame.Surface((artist_width + self.scroll_padding, artist_rect.height), pygame.SRCALPHA)
            scroll_surface.blit(artist_text, (0, 0))
            
            # Calculate the scroll position
            scroll_x = self.scroll_offset % (artist_width + self.scroll_padding)
            
            # Create a surface twice the width of the text + padding
            double_surface = pygame.Surface(((artist_width + self.scroll_padding) * 2, artist_rect.height), pygame.SRCALPHA)
            double_surface.blit(scroll_surface, (0, 0))
            double_surface.blit(scroll_surface, (artist_width + self.scroll_padding, 0))
            
            # Blit the scrolling text onto the main surface
            surface.blit(double_surface, artist_rect, 
                         (scroll_x, 0, self.max_text_width, artist_rect.height))
        else:
            # Center the text if it's shorter than max_text_width
            artist_rect.x += (self.max_text_width - artist_width) // 2
            surface.blit(artist_text, artist_rect)

        # Draw title text
        title_rect = pygame.Rect(0, 0, self.max_text_width, title_text.get_height())
        title_rect.midtop = (center_x, 420)
        if title_width > self.max_text_width:
            # Create a surface with padding
            scroll_surface = pygame.Surface((title_width + self.scroll_padding, title_rect.height), pygame.SRCALPHA)
            scroll_surface.blit(title_text, (0, 0))
            
            # Calculate the scroll position
            scroll_x = self.scroll_offset % (title_width + self.scroll_padding)
            
            # Create a surface twice the width of the text + padding
            double_surface = pygame.Surface(((title_width + self.scroll_padding) * 2, title_rect.height), pygame.SRCALPHA)
            double_surface.blit(scroll_surface, (0, 0))
            double_surface.blit(scroll_surface, (title_width + self.scroll_padding, 0))
            
            # Blit the scrolling text onto the main surface
            surface.blit(double_surface, title_rect, 
                         (scroll_x, 0, self.max_text_width, title_rect.height))
        else:
            # Center the text if it's shorter than max_text_width
            title_rect.x += (self.max_text_width - title_width) // 2
            surface.blit(title_text, title_rect)

        # Draw station logo
        if self.current_station:
            # Load station logo if not already loaded
            if self.current_station not in self.station_logos:
                self.station_logos[self.current_station] = self.load_station_logo(self.current_station)

            # Display station logo
            logo = self.station_logos[self.current_station]
            if logo:
                tinted_logo = logo.copy()
                tinted_logo.fill(get_color('BRIGHT'), special_flags=pygame.BLEND_RGBA_MULT)
                logo_rect = tinted_logo.get_rect(center=(SCREEN_WIDTH - (SCREEN_WIDTH // 4) - 10, 360))
                surface.blit(tinted_logo, logo_rect)

        # Draw the graph box
        box_x = SCREEN_WIDTH // 2
        box_y = self.top_padding
        box_width = self.grid_width
        box_height = self.grid_height

        # Draw the ticks
        self.draw_ticks(surface, box_x, box_y, box_width, box_height)

        self.draw_waveform(surface)

    def draw_text(self, text, font, color, surface, x, y):
        textobj = self.font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def update(self):
        if not pygame.mixer.music.get_busy():
            if self.is_playing_news:
                self.play_next_news_clip()
            elif self.current_station:
                self.next_song()
        self.clock.tick(30)  # Limit to 30 FPS