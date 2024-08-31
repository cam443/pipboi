import pygame
import os
import random
import configparser
import numpy as np
from settings import settings
from config import *
from pydub import AudioSegment
import json
import threading
from collections import deque


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
        if self.current_station:
            self.play_song()

    def load_stations(self):
        stations = {}
        base_path = 'sounds/radio'
        supported_formats = ('.ogg', '.wav', '.mp3', '.flac')
        for folder in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder)
            if os.path.isdir(folder_path):
                songs = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_formats)]
                if songs:  # Only include folders with supported audio files
                    config = configparser.ConfigParser()
                    config.read(os.path.join(folder_path, 'station.ini'))
                    station_name = config.get('metadata', 'station_name', fallback=folder)
                    ordered = config.getboolean('metadata', 'ordered', fallback=False)
                    songs = [os.path.join(folder_path, f) for f in songs]
                    if not ordered:
                        random.shuffle(songs)
                    stations[station_name] = {'songs': songs, 'ordered': ordered}
        return stations

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
            self.play_song()
            self.save_state()
            self.set_selected_index()

    def play_song(self):
        if self.current_station:
            songs = self.stations[self.current_station]['songs']
            if songs:
                self.current_song = songs[self.song_index]
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()
                self.start_time = pygame.time.get_ticks()
                self.load_waveform(self.current_song)
            else:
                self.current_song = None

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
        if not pygame.mixer.music.get_busy() and self.current_station:
            self.next_song()
        self.clock.tick(30)  # Limit to 30 FPS