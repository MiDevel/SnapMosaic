import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from snap_mosaic.main_window import SnapMosaic

def main():
    """Main function to run the SnapMosaic application."""
    app = QApplication(sys.argv)

    # --- Set Application Icon ---
    # Use the .ico on Windows for best results, otherwise use the .svg
    if sys.platform == "win32":
        icon_filename = 'SnapMosaic.ico'
    else:
        icon_filename = 'SnapMosaic.svg'
    
    # The assets folder is at the same level as the main.py script
    base_dir = os.path.dirname(__file__)
    icon_path = os.path.join(base_dir, 'assets', icon_filename)

    # Fallback to SVG if ICO is not found on Windows
    if not os.path.exists(icon_path) and sys.platform == "win32":
        svg_path = os.path.join(base_dir, 'assets', 'SnapMosaic.svg')
        if os.path.exists(svg_path):
            icon_path = svg_path

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # --- Create and Show Main Window ---
    window = SnapMosaic()
    window.show()
    
    # --- Start Event Loop ---
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
