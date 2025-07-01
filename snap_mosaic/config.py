import json
import os

class Config:
    def __init__(self, file_path='SnapMosaic.json'):
        self.file_path = file_path
        self.settings = self.load_config()

    def load_config(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return self.get_default_config()

    def save_config(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_config()

    def get_default_config(self):
        return {
            'hotkey': 'f7',
            'window_geometry': None,
            'auto_copy_to_clipboard': False
        }
