from PySide6.QtCore import QStandardPaths
import os

config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
config_file = os.path.join(config_dir, "SnapMosaic.json")

print(f"Config directory: {config_dir}")
print(f"Config file path: {config_file}")
