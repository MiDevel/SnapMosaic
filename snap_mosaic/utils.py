import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not bundled, so the base path is the project root, which is one level up from this file's package
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)
