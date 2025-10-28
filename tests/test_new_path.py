from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QStandardPaths
import sys

app = QApplication(sys.argv)
app.setApplicationName("SnapMosaic")
app.setOrganizationName("SnapMosaic")

config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
print(f"Config directory: {config_dir}")

from snap_mosaic.config import Config
c = Config()
print(f"Config file path: {c.file_path}")
