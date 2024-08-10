import json
import os

class Settings:
    def __init__(self):
        self.filename = 'settings.json'
        self.default_settings = {
            'ui_color': 'GREEN',
            'radio_station': None,
            'radio_volume': 0.5
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return self.default_settings.copy()

    def save_settings(self):
        with open(self.filename, 'w') as f:
            json.dump(self.settings, f)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

settings = Settings()