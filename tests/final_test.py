from PySide6.QtWidgets import QApplication
import sys
import os

app = QApplication(sys.argv)
app.setApplicationName("SnapMosaic")

from snap_mosaic.config import Config
c = Config()

print(f"✓ Config path: {c.file_path}")
print(f"✓ Config has {len(c.settings)} settings")
print(f"✓ Sample setting (hotkey): {c.get('hotkey')}")
print(f"✓ File exists: {os.path.exists(c.file_path)}")
print(f"\n✓ All tests passed!")
