import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QStyle,
    QSystemTrayIcon, QMenu, QCheckBox
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QRect, QThread, QTimer
import threading
from playsound import playsound
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
        self.define_region_button.setToolTip("Define a new screen region to capture")
        
        self.snap_button = QPushButton() # Text set in update_snap_button_text
        
        self.auto_button = QPushButton() # Text set in update_auto_button_text
        self.auto_button.setCheckable(True)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setToolTip("Clear all captures from grid")

        settings_icon = QIcon(resource_path('snap_mosaic/icons/settings.svg'))
        self.settings_button = QPushButton(settings_icon, " Settings")
        self.settings_button.setToolTip("Open settings")

        about_icon = QIcon(resource_path('snap_mosaic/icons/about.svg'))
        self.about_button = QPushButton(about_icon, " About")
        self.about_button.setToolTip("About SnapMosaic")

        top_button_layout.addWidget(self.define_region_button)
        top_button_layout.addWidget(self.snap_button)
        top_button_layout.addWidget(self.auto_button)
        top_button_layout.addWidget(self.clear_button)
        top_button_layout.addStretch()
        top_button_layout.addWidget(self.settings_button)
        top_button_layout.addWidget(self.about_button)
        main_layout.addLayout(top_button_layout)

        # Scroll Area for captures
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_content_widget)
        self.scroll_layout = QGridLayout(self.scroll_content_widget)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        main_layout.addWidget(self.scroll_area)

        # --- Connections ---
        self.define_region_button.clicked.connect(self.define_region)
        self.snap_button.clicked.connect(self.trigger_capture)
        self.auto_button.clicked.connect(self.toggle_auto_snap)
        self.clear_button.clicked.connect(self.clear_grid)
        self.settings_button.clicked.connect(self.open_settings)
        self.about_button.clicked.connect(self.open_about)

        # --- App State ---
        self.selection_overlay = None
        self.captured_widgets = []
        self.hotkey_listener = None
        self.auto_snap_hotkey_listener = None
        self.is_quitting = False
        self.is_auto_snapping = False
        self.auto_snap_timer = QTimer(self)
        self.auto_snap_timer.timeout.connect(self.trigger_capture)
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.redraw_grid)
        self.last_hovered_widget = None  # Track last hovered widget for keyboard shortcuts



        # Load config and start services
        self.load_app_config()
        self.start_hotkey_listener()
        self.start_auto_snap_hotkey_listener()
        self.setup_tray_icon()

    def load_app_config(self):
        # Load capture region from config
        region_data = self.config.get("capture_region")
        if region_data:
            self.capture_region = QRect(region_data['x'], region_data['y'], region_data['width'], region_data['height'])
            print(f"Loaded capture region: {self.capture_region}")
        else:
            self.capture_region = None

        # Load hotkeys and update button text
        self.hotkey = self.config.get("hotkey", 'f7')
        self.auto_snap_hotkey = self.config.get("auto_snap_hotkey", 'f8')
        self.update_snap_button_text()
        self.update_auto_button_text()

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

    def start_auto_snap_hotkey_listener(self):
        if self.auto_snap_hotkey_listener:
            self.auto_snap_hotkey_listener.stop()

        self.auto_snap_hotkey_listener = HotkeyListener(self.auto_snap_hotkey)
        self.auto_snap_hotkey_listener.hotkey_pressed.connect(self.toggle_auto_snap)
        return self.auto_snap_hotkey_listener.start()

    def toggle_auto_snap(self):
        if self.is_auto_snapping:
            self.stop_auto_snap()
        else:
            self.start_auto_snap()

    def start_auto_snap(self):
        if not self.capture_region:
            QMessageBox.warning(self, "No Region Defined", 
                              "Please define a capture region first before starting Auto-Snap.")
            self.auto_button.setChecked(False)
            return

        self.is_auto_snapping = True
        self.auto_button.setChecked(True)
        interval_sec = self.config.get('auto_snap_interval', 10)
        self.auto_snap_timer.start(interval_sec * 1000)
        self.update_auto_button_style()
        print(f"Auto-Snap started with {interval_sec}s interval")

    def stop_auto_snap(self):
        self.is_auto_snapping = False
        self.auto_button.setChecked(False)
        self.auto_snap_timer.stop()
        self.update_auto_button_style()
        print("Auto-Snap stopped")

    def flash_auto_button(self):
        """Briefly flash the auto button to provide visual feedback during auto-snap."""
        original_style = self.auto_button.styleSheet()
        # Brighter flash
        self.auto_button.setStyleSheet("""
            QPushButton {
                background-color: #66FF66;
                color: white;
                font-weight: bold;
            }
        """)
        # Reset after 150ms
        QTimer.singleShot(150, lambda: self.auto_button.setStyleSheet(original_style))

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
        # Stop auto-snap if running since we're clearing the grid and defining new region
        if self.is_auto_snapping:
            self.stop_auto_snap()
        
        # Check if there are captures that need to be cleared first
        if self.captured_widgets:
            QMessageBox.information(
                self,
                "Clear Captures First",
                "Please clear all captures before defining a new region.\n\n"
                "Click 'Clear All' button to remove current captures, then try again."
            )
            return
        
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

    def play_sound(self, name):
        """
        Plays a sound using the 'playsound' library in a separate thread
        to prevent UI blocking.
        """
        if not self.config.get('sounds_enabled', True):
            return

        sound_map = {
            'snap': 'snap_mosaic/sounds/snap.wav',
            'save': 'snap_mosaic/sounds/save.wav',
            'clipboard': 'snap_mosaic/sounds/clipboard.wav',
            'error': 'snap_mosaic/sounds/error.wav'
        }

        if name in sound_map:
            file_path = resource_path(sound_map[name])
            
            # Run playsound in a separate thread to avoid blocking the GUI
            try:
                sound_thread = threading.Thread(target=playsound, args=(file_path,), daemon=True)
                sound_thread.start()
            except Exception as e:
                print(f"Error playing sound '{name}': {e}")
        else:
            print(f"Warning: Sound '{name}' not defined in play_sound's sound_map.")

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

        self.play_sound('snap')
        
        # Visual feedback for auto-snap mode
        if self.is_auto_snapping:
            self.flash_auto_button()

        # Auto-copy to clipboard if enabled
        if self.config.get('auto_copy_to_clipboard', False):
            QApplication.clipboard().setPixmap(pixmap)
            print("Image auto-copied to clipboard.")

        # Scale for display if needed
        max_width = self.config.get('max_display_width', 500)
        display_pixmap = pixmap
        if pixmap.width() > max_width:
            display_pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
            print(f"Scaled image from {pixmap.width()}x{pixmap.height()} to {display_pixmap.width()}x{display_pixmap.height()} for display")

        # Create the image widget with both display and original pixmaps
        image_container = HoverLabel(display_pixmap, pixmap)
        image_container.delete_requested.connect(self.delete_image)
        image_container.save_requested.connect(self.save_image)
        image_container.copy_requested.connect(self.copy_image_to_clipboard)
        
        # Connect hover events for keyboard shortcuts tracking
        image_container.installEventFilter(self)

        # Auto-save if enabled (this will also set the 'saved' flag)
        self.auto_save_image(image_container)
        
        self.captured_widgets.insert(0, image_container)
        self.redraw_grid()

    def save_image(self, hover_label, quiet=False):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Image", 
            "", 
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg)"
        )
        if file_path:
            pixmap = hover_label.original_pixmap
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path += '.png' # Default to png if no valid extension
            pixmap.save(file_path)
            print(f"Image saved to {file_path}")
            hover_label.is_saved = True
            hover_label.update() # Trigger repaint to show saved checkmark
            if not quiet:
                self.play_sound('save')

    def delete_image(self, image_container):
        if image_container in self.captured_widgets:
            self.captured_widgets.remove(image_container)
            image_container.deleteLater()
            print("Image removed.")
            QTimer.singleShot(0, self.redraw_grid)

    def copy_image_to_clipboard(self, hover_label, quiet=False):
        QApplication.clipboard().setPixmap(hover_label.original_pixmap)
        if not quiet:
            self.play_sound('clipboard')
        print("Image copied to clipboard.")

    def auto_save_image(self, image_container, quiet=False):
        if not self.config.get('auto_save_enabled'):
            return

        location = self.config.get('auto_save_location')
        prefix = self.config.get('auto_save_prefix')
        suffix_type = self.config.get('auto_save_suffix_type')
        img_format = self.config.get('auto_save_format')
        pixmap = image_container.original_pixmap

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

    def clear_grid_with_confirmation(self, reason=None):
        """
        Clear grid with user confirmation if there are captures.
        
        Args:
            reason: Optional string explaining why clearing is needed (currently unused)
        
        Returns:
            True if grid was cleared or was already empty.
            False if user cancelled.
        """
        if not self.captured_widgets:
            return True  # Nothing to clear, proceed
        
        # Check if we should show confirmation
        confirmations = self.config.get('confirmations', {})
        if confirmations.get('clear_all', True):
            msg_box = QMessageBox(self)
            msg_box.setModal(True)
            msg_box.setWindowTitle("Clear All Captures")
            msg_box.setText("Are you sure you want to clear all captures?")
            msg_box.setInformativeText("This will remove all images from the grid.\nUnsaved captures will be lost.")
            
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            # Add "Don't ask again" checkbox
            dont_ask_checkbox = QCheckBox("Don't ask again")
            msg_box.setCheckBox(dont_ask_checkbox)
            
            result = msg_box.exec()
            
            # Save preference if checkbox was checked
            if dont_ask_checkbox.isChecked():
                confirmations['clear_all'] = False
                self.config.set('confirmations', confirmations)
            
            if result != QMessageBox.StandardButton.Yes:
                return False  # User cancelled
        
        # Clear the grid
        for widget in self.captured_widgets[:]:
            self.delete_image(widget)
        self.captured_widgets.clear()
        print("Grid and in-memory image list cleared.")
        return True  # Successfully cleared

    def clear_grid(self):
        """Clear grid - called from Clear All button."""
        self.clear_grid_with_confirmation()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Escape key stops auto-snap if running
        if event.key() == Qt.Key.Key_Escape:
            if self.is_auto_snapping:
                self.stop_auto_snap()
                event.accept()
                return
        
        # Ctrl+S - Quick save the last captured or hovered image
        if event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            target_widget = self.last_hovered_widget if self.last_hovered_widget else (self.captured_widgets[0] if self.captured_widgets else None)
            if target_widget:
                self.save_image(target_widget)
                event.accept()
                return
        
        # Ctrl+C - Copy the last captured or hovered image
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            target_widget = self.last_hovered_widget if self.last_hovered_widget else (self.captured_widgets[0] if self.captured_widgets else None)
            if target_widget:
                self.copy_image_to_clipboard(target_widget, quiet=True)
                event.accept()
                return
        
        # Delete key - Delete the hovered image
        if event.key() == Qt.Key.Key_Delete:
            if self.last_hovered_widget:
                self.delete_image(self.last_hovered_widget)
                event.accept()
                return
        
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Track which widget is being hovered for keyboard shortcuts."""
        if isinstance(obj, HoverLabel):
            if event.type() == event.Type.Enter:
                self.last_hovered_widget = obj
            elif event.type() == event.Type.Leave:
                if self.last_hovered_widget == obj:
                    self.last_hovered_widget = None
        
        return super().eventFilter(obj, event)

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
        self.snap_button.setToolTip(f"Capture the defined region ({self.hotkey.upper()})")

    def update_auto_button_text(self):
        self.auto_button.setText(f"Auto [{self.auto_snap_hotkey.upper()}]")
        interval = self.config.get('auto_snap_interval', 10)
        self.auto_button.setToolTip(
            f"Toggle automatic captures every {interval}s ({self.auto_snap_hotkey.upper()})\n"
            f"Press Escape to stop"
        )

    def update_auto_button_style(self):
        if self.is_auto_snapping:
            self.auto_button.setStyleSheet("""
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.auto_button.setStyleSheet("")

    def open_settings(self):
        previous_hotkey = self.config.get('hotkey')
        previous_auto_snap_hotkey = self.config.get('auto_snap_hotkey')
        previous_max_width = self.config.get('max_display_width', 500)
        previous_interval = self.config.get('auto_snap_interval', 10)
        dialog = SettingsDialog(self.config, self)

        if dialog.exec():
            new_hotkey = self.config.get('hotkey')
            if new_hotkey != previous_hotkey:
                self.hotkey = new_hotkey

                if self.start_hotkey_listener():
                    self.update_snap_button_text()
                    QMessageBox.information(self, "Hotkey Updated",
                                            f"The new hotkey '{self.hotkey}' is now active.")
                else:
                    QMessageBox.warning(self, "Invalid Hotkey",
                                        f"Could not register the hotkey '{self.hotkey}'.\n"
                                        "It might be already in use by another application.\n"
                                        "Reverting to the previous hotkey.")
                    self.play_sound('error')
                    self.hotkey = previous_hotkey
                    self.config.set('hotkey', previous_hotkey)
                    self.start_hotkey_listener()
                    self.update_snap_button_text()
            
            # Handle auto-snap hotkey changes
            new_auto_snap_hotkey = self.config.get('auto_snap_hotkey')
            if new_auto_snap_hotkey != previous_auto_snap_hotkey:
                self.auto_snap_hotkey = new_auto_snap_hotkey

                if self.start_auto_snap_hotkey_listener():
                    self.update_auto_button_text()
                    QMessageBox.information(self, "Auto-Snap Hotkey Updated",
                                            f"The new auto-snap hotkey '{self.auto_snap_hotkey}' is now active.")
                else:
                    QMessageBox.warning(self, "Invalid Auto-Snap Hotkey",
                                        f"Could not register the auto-snap hotkey '{self.auto_snap_hotkey}'.\n"
                                        "It might be already in use by another application.\n"
                                        "Reverting to the previous hotkey.")
                    self.play_sound('error')
                    self.auto_snap_hotkey = previous_auto_snap_hotkey
                    self.config.set('auto_snap_hotkey', previous_auto_snap_hotkey)
                    self.start_auto_snap_hotkey_listener()
                    self.update_auto_button_text()
            
            # Handle interval changes while auto-snap is running
            new_interval = self.config.get('auto_snap_interval', 10)
            if new_interval != previous_interval and self.is_auto_snapping:
                self.auto_snap_timer.setInterval(new_interval * 1000)
                print(f"Auto-snap interval updated to {new_interval}s")
            
            # Check if max_display_width changed and redraw grid if needed
            if previous_max_width != self.config.get('max_display_width'):
                self.redraw_grid()

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
        # Stop auto-snap if running
        if self.is_auto_snapping:
            self.stop_auto_snap()
        # Stop hotkey listeners
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.auto_snap_hotkey_listener:
            self.auto_snap_hotkey_listener.stop()
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
