import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QStyle,
    QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QRect, QThread, QTimer
from datetime import datetime

from snap_mosaic.config import Config
from snap_mosaic.hotkey import HotkeyListener
from snap_mosaic.widgets import SelectionOverlay, HoverLabel
from snap_mosaic.dialogs import SettingsDialog, AboutDialog
from snap_mosaic.utils import resource_path
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

        settings_icon = QIcon(resource_path('snap_mosaic/icons/settings.svg'))
        self.settings_button = QPushButton(settings_icon, " Settings")

        about_icon = QIcon(resource_path('snap_mosaic/icons/about.svg'))
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
        self.is_quitting = False
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.redraw_grid)

        # Load config and start services
        self.load_app_config()
        self.start_hotkey_listener()
        self.setup_tray_icon()

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

    def save_capture_region(self):
        if self.capture_region:
            region_data = {
                "x": self.capture_region.x(),
                "y": self.capture_region.y(),
                "width": self.capture_region.width(),
                "height": self.capture_region.height()
            }
            self.config.set("capture_region", region_data)

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
        self.save_capture_region()
        self.show()

    def trigger_capture(self):
        if not self.capture_region:
            print("Hotkey pressed, but no region defined.")
            return

        screen = QApplication.primaryScreen()
        if not screen:
            print("Error: Could not get primary screen.")
            return

        # IMPORTANT: Keep the device pixel ratio for High-DPI displays
        dpr = screen.devicePixelRatio()
        pixmap = screen.grabWindow(
            0,
            int(self.capture_region.x() * dpr),
            int(self.capture_region.y() * dpr),
            int(self.capture_region.width() * dpr),
            int(self.capture_region.height() * dpr)
        )

        if pixmap.isNull():
            return

        # Auto-copy to clipboard if enabled
        if self.config.get('auto_copy_to_clipboard', False):
            QApplication.clipboard().setPixmap(pixmap)
            print("Image auto-copied to clipboard.")

        # Create the image widget first
        image_container = HoverLabel(pixmap)
        image_container.delete_requested.connect(self.delete_image)
        image_container.save_requested.connect(self.save_image)
        image_container.copy_requested.connect(self.copy_image_to_clipboard)

        # Auto-save if enabled (this will also set the 'saved' flag)
        self.auto_save_image(image_container)
        
        self.captured_widgets.insert(0, image_container)
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

    def copy_image_to_clipboard(self, hover_label):
        QApplication.clipboard().setPixmap(hover_label.pixmap())
        print("Image copied to clipboard.")

    def auto_save_image(self, image_container):
        if not self.config.get('auto_save_enabled'):
            return

        location = self.config.get('auto_save_location')
        prefix = self.config.get('auto_save_prefix')
        suffix_type = self.config.get('auto_save_suffix_type')
        img_format = self.config.get('auto_save_format')
        pixmap = image_container.pixmap()

        try:
            os.makedirs(location, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {location}: {e}")
            QMessageBox.warning(self, "Auto-Save Error", f"Could not create the save directory:\n{location}\n\nPlease check permissions and the path in Settings.")
            return

        if suffix_type == 'timestamp':
            # Add milliseconds for uniqueness in rapid captures
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{prefix}-{timestamp}.{img_format}"
        else:  # numeric
            counter = self.config.get('auto_save_numeric_counter')
            filename = f"{prefix}-{counter:04d}.{img_format}"
            self.config.set('auto_save_numeric_counter', counter + 1)

        file_path = os.path.join(location, filename)
        quality = self.config.get('auto_save_jpg_quality') if img_format == 'jpg' else -1

        if not pixmap.save(file_path, None, quality):
            print(f"Error auto-saving image to {file_path}")
            QMessageBox.warning(self, "Auto-Save Error", f"Could not save the image to:\n{file_path}")
        else:
            print(f"Auto-saved image to {file_path}")
            image_container.is_saved = True
            image_container.update() # Trigger repaint to show saved checkmark

    def clear_grid(self):
        for widget in self.captured_widgets[:]: # Iterate over a copy
            self.delete_image(widget)
        self.captured_widgets.clear()
        print("Grid and in-memory image list cleared.")

    def closeEvent(self, event):
        if self.is_quitting:
            super().closeEvent(event)
            return

        if self.config.get('minimize_to_tray'):
            event.ignore()
            self.hide()
            if self.config.get('show_tray_notification'):
                self.tray_icon.showMessage(
                    "SnapMosaic",
                    "Application is still running in the system tray.",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            self.quit_application()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150) # Debounce resize events

    def update_snap_button_text(self):
        self.snap_button.setText(f"Snap [{self.hotkey.upper()}]")

    def open_settings(self):
        previous_hotkey = self.config.get('hotkey')
        dialog = SettingsDialog(self.config, self)

        if dialog.exec():
            new_hotkey = self.config.get('hotkey')
            if new_hotkey != previous_hotkey:
                self.hotkey = new_hotkey  # Update instance variable

                if self.start_hotkey_listener():
                    # Success - config is already saved by the dialog
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
                    self.config.set('hotkey', previous_hotkey)  # Revert in config
                    self.start_hotkey_listener()  # Restart with the old, working key
                    self.update_snap_button_text()  # Update button text back

    def open_about(self):
        dialog = AboutDialog(self.version, self)
        dialog.exec()

    def setup_tray_icon(self):
        icon_path = resource_path('assets/SnapMosaic.png')
        if not os.path.exists(icon_path):
            # Fallback icon in case assets are not found
            icon_path = resource_path('snap_mosaic/icons/settings.svg')

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip("SnapMosaic")

        menu = QMenu(self)
        show_action = menu.addAction("Show Window")
        show_action.triggered.connect(self.show_window)

        define_region_action = menu.addAction("Define new Region")
        define_region_action.triggered.connect(self.define_region)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        # A single-click (Trigger) shows/hides the window.
        # Note: On some platforms, a right-click can also emit a Trigger signal,
        # which might cause the window to show unexpectedly after the context menu.
        # However, single-click is the most intuitive primary action.
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window_visibility()

    def toggle_window_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    def show_window(self):
        self.showNormal() # Restore from minimized state
        self.activateWindow() # Bring to front

    def quit_application(self):
        self.is_quitting = True
        # Save window geometry
        geom = self.geometry()
        self.config.set('window_geometry', {'x': geom.x(), 'y': geom.y(), 'width': geom.width(), 'height': geom.height()})
        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.tray_icon.hide()
        QApplication.instance().quit()

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
