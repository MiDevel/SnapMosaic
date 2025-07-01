import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QStyle
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QRect, QThread, QTimer

from snap_mosaic.config import Config
from snap_mosaic.hotkey import HotkeyListener
from snap_mosaic.widgets import SelectionOverlay, HoverLabel
from snap_mosaic.dialogs import SettingsDialog, AboutDialog
from . import __version__

class SnapMosaic(QMainWindow):
    def __init__(self):
        super().__init__()
        self.version = __version__
        self.config = Config()

        self.setWindowTitle("SnapMosaic")
        self.restore_geometry()

        # --- UI Setup ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Button Bar
        top_button_layout = QHBoxLayout()
        self.define_region_button = QPushButton("Define Region")
        self.snap_button = QPushButton() # Text set in update_snap_button_text
        self.clear_button = QPushButton("Clear All")

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'settings.svg')
        settings_icon = QIcon(icon_path)
        self.settings_button = QPushButton(settings_icon, " Settings")

        about_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'about.svg')
        about_icon = QIcon(about_icon_path)
        self.about_button = QPushButton(about_icon, " About")

        top_button_layout.addWidget(self.define_region_button)
        top_button_layout.addWidget(self.snap_button)
        top_button_layout.addWidget(self.clear_button)
        top_button_layout.addStretch()
        top_button_layout.addWidget(self.settings_button)
        top_button_layout.addWidget(self.about_button)

        # Scroll Area for captures
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_content_widget)
        self.scroll_layout = QGridLayout(self.scroll_content_widget)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        main_layout.addLayout(top_button_layout)
        main_layout.addWidget(self.scroll_area)

        # --- Connections ---
        self.define_region_button.clicked.connect(self.define_region)
        self.snap_button.clicked.connect(self.trigger_capture)
        self.clear_button.clicked.connect(self.clear_grid)
        self.settings_button.clicked.connect(self.open_settings)
        self.about_button.clicked.connect(self.open_about)

        # --- App State ---
        self.selection_overlay = None
        self.captured_widgets = []
        self.hotkey_listener = None
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.redraw_grid)

        # Load config and start services
        self.load_app_config()
        self.start_hotkey_listener()

    def load_app_config(self):
        # Load capture region from config
        region_data = self.config.get("capture_region")
        if region_data:
            self.capture_region = QRect(region_data['x'], region_data['y'], region_data['width'], region_data['height'])
            print(f"Loaded capture region: {self.capture_region}")
        else:
            self.capture_region = None

        # Load hotkey and update button text
        self.hotkey = self.config.get("hotkey", 'f7')
        self.update_snap_button_text()

    def save_app_config(self):
        # Save capture region
        if self.capture_region:
            region_data = {
                "x": self.capture_region.x(),
                "y": self.capture_region.y(),
                "width": self.capture_region.width(),
                "height": self.capture_region.height()
            }
            self.config.set("capture_region", region_data)
        
        # Save hotkey
        self.config.set("hotkey", self.hotkey)

    def start_hotkey_listener(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        self.hotkey_listener = HotkeyListener(self.hotkey)
        self.hotkey_listener.hotkey_pressed.connect(self.trigger_capture)
        return self.hotkey_listener.start()

    def restore_geometry(self):
        geom_data = self.config.get('window_geometry')
        if geom_data:
            rect = QRect(geom_data['x'], geom_data['y'], geom_data['width'], geom_data['height'])
            # Check if the geometry is within any available screen
            is_on_screen = any(s.geometry().intersects(rect) for s in QApplication.screens())
            if is_on_screen:
                self.setGeometry(rect)
                return
        # Default if no config or off-screen
        self.resize(800, 600)
        self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())

    def define_region(self):
        self.clear_grid()
        self.hide()
        screen = QApplication.primaryScreen()
        virtual_desktop_rect = screen.virtualGeometry()
        screenshot = screen.grabWindow(0, virtual_desktop_rect.x(), virtual_desktop_rect.y(), virtual_desktop_rect.width(), virtual_desktop_rect.height())
        self.selection_overlay = SelectionOverlay(screenshot)
        self.selection_overlay.selection_made.connect(self.set_capture_region)
        self.selection_overlay.show()

    def set_capture_region(self, rect):
        self.capture_region = rect
        print(f"Capture region set to: {self.capture_region}")
        self.save_app_config()
        self.show()

    def trigger_capture(self):
        if not self.capture_region:
            print("Hotkey pressed, but no region defined.")
            return

        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio()
        pixmap = screen.grabWindow(
            0,
            int(self.capture_region.x() * dpr),
            int(self.capture_region.y() * dpr),
            int(self.capture_region.width() * dpr),
            int(self.capture_region.height() * dpr)
        )

        if not pixmap.isNull():
            hover_label = HoverLabel(pixmap)
            hover_label.save_requested.connect(self.save_image)
            hover_label.delete_requested.connect(self.delete_image)
            hover_label.setStyleSheet("border: 1px solid #444444;")
            
            self.captured_widgets.append(hover_label)
            self.redraw_grid()

    def save_image(self, hover_label):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Image", 
            "", 
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg)"
        )
        if file_path:
            pixmap = hover_label.pixmap()
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path += '.png' # Default to png if no valid extension
            pixmap.save(file_path)
            print(f"Image saved to {file_path}")
            hover_label.is_saved = True
            hover_label.update() # Trigger repaint to show saved checkmark

    def delete_image(self, image_container):
        if image_container in self.captured_widgets:
            self.captured_widgets.remove(image_container)
            image_container.deleteLater()
            print("Image removed.")
            QTimer.singleShot(0, self.redraw_grid) 

    def clear_grid(self):
        for widget in self.captured_widgets[:]: # Iterate over a copy
            self.delete_image(widget)
        self.captured_widgets.clear()
        print("Grid and in-memory image list cleared.")

    def closeEvent(self, event):
        # Save window geometry
        geom = self.geometry()
        self.config.set('window_geometry', {'x': geom.x(), 'y': geom.y(), 'width': geom.width(), 'height': geom.height()})

        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150) # Debounce resize events

    def update_snap_button_text(self):
        self.snap_button.setText(f"Snap [{self.hotkey.upper()}]")

    def open_settings(self):
        dialog = SettingsDialog(self.hotkey, self)
        if dialog.exec():
            new_hotkey = dialog.new_hotkey
            if new_hotkey != self.hotkey:
                previous_hotkey = self.hotkey
                self.hotkey = new_hotkey

                if self.start_hotkey_listener():
                    # Success
                    self.save_app_config()
                    self.update_snap_button_text()
                    QMessageBox.information(self, "Hotkey Updated", 
                                            f"The new hotkey '{self.hotkey}' is now active.")
                else:
                    # Failure
                    QMessageBox.warning(self, "Invalid Hotkey",
                                        f"Could not register the hotkey '{self.hotkey}'.\n"
                                        "It might be already in use by another application.\n"
                                        "Reverting to the previous hotkey.")
                    self.hotkey = previous_hotkey
                    self.start_hotkey_listener() # Restart with the old, working key
                    self.update_snap_button_text() # Update button text back

    def open_about(self):
        dialog = AboutDialog(self.version, self)
        dialog.exec()

    def redraw_grid(self):
        # Clear the existing layout first
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not self.captured_widgets:
            return

        viewport_width = self.scroll_area.viewport().width()
        if not self.captured_widgets:
            return
        image_width = self.captured_widgets[0].width()
        spacing = self.scroll_layout.spacing()
        num_columns = max(1, (viewport_width - spacing) // (image_width + spacing))

        for i, widget in enumerate(self.captured_widgets):
            row = i // num_columns
            col = i % num_columns
            self.scroll_layout.addWidget(widget, row, col)
