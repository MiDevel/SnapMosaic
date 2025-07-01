import json
import os
from PySide6.QtCore import QStandardPaths

class Config:
    def __init__(self, file_path='SnapMosaic.json'):
        self.file_path = file_path
        self.settings = self.load_config()

    def load_config(self):
        # Start with default settings to ensure all keys are present
        settings = self.get_default_config()

        # If a user config file exists, load it and update the defaults
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    user_settings = json.load(f)
                    # The user_settings might be None or not a dict if the file is empty/corrupt
                    if isinstance(user_settings, dict):
                        settings.update(user_settings)
            except (json.JSONDecodeError, TypeError) as e:
                # Handle corrupted or invalid JSON
                print(f"Warning: Could not load or parse {self.file_path}: {e}. Using default settings.")
                # We already have the defaults in 'settings', so we can just continue
                pass
            
        return settings

    def save_config(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_config()

    def get_default_config(self):
        pictures_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        default_save_path = os.path.join(pictures_location, "SnapMosaic")

        return {
            'hotkey': 'f7',
            'window_geometry': None,
            'auto_copy_to_clipboard': False,
            'minimize_to_tray': False,
            'show_tray_notification': True,
            'sounds_enabled': True,
            'auto_save_enabled': False,
            'auto_save_location': default_save_path,
            'auto_save_prefix': 'SnapMosaic',
            'auto_save_suffix_type': 'timestamp', # 'timestamp' or 'numeric'
            'auto_save_numeric_counter': 1,
            'auto_save_format': 'png', # 'png' or 'jpg'
            'auto_save_jpg_quality': 95
        }
