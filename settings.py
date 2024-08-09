import json
import os

class Settings:
    def __init__(self):
        self.filename = 'settings.json'
        self.default_settings = {
            'ui_color': 'GREEN'
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return self.default_settings

    def save_settings(self):
        with open(self.filename, 'w') as f:
            json.dump(self.settings, f)

    def get(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

settings = Settings()