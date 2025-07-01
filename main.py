import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QLabel, QDialog, QDialogButtonBox, QMessageBox, QRubberBand, QGridLayout
)
from PySide6.QtGui import QPainter, QScreen, QPixmap, QIcon, QImage
from PySide6.QtCore import Qt, QRect, Signal, QThread, QObject, QSize, QTimer
from pynput import keyboard

class HotkeyListener(QObject):
    hotkey_pressed = Signal()

    def __init__(self, hotkey_str='f7'):
        super().__init__()
        self.key_to_listen = self._parse_key(hotkey_str)
        self.listener = None
        print(f"Listening for hotkey: {self.key_to_listen}")

    def _parse_key(self, key_str):
        try:
            return getattr(keyboard.Key, key_str)
        except AttributeError:
            print(f"Could not parse '{key_str}' as a special key. Treating as a character.")
            return keyboard.KeyCode.from_char(key_str)

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as self.listener:
            self.listener.join()

    def on_press(self, key):
        if key == self.key_to_listen:
            self.hotkey_pressed.emit()

    def stop(self):
        if self.listener:
            self.listener.stop()

class SelectionOverlay(QWidget):
    selection_made = Signal(QRect)

    def __init__(self, screen_pixmap):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geometry)
        self.pixmap = screen_pixmap

        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.origin:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if self.origin:
            self.rubber_band.hide()
            selection_rect = QRect(self.origin, event.pos()).normalized()
            self.selection_made.emit(selection_rect)
            self.close()


class HotkeyInput(QPushButton):
    key_captured = Signal(str)

    def __init__(self, hotkey, parent=None):
        super().__init__(hotkey, parent)
        self.current_hotkey = hotkey
        self.is_capturing = False
        self.clicked.connect(self.start_capture)

    def start_capture(self):
        self.is_capturing = True
        self.setText("Press a key...")
        self.setFocus()

    def keyPressEvent(self, event):
        if self.is_capturing:
            key_name = self._qt_key_to_string(event)
            if key_name:
                self.current_hotkey = key_name
                self.setText(self.current_hotkey)
                self.key_captured.emit(self.current_hotkey)
            else:
                self.setText(self.current_hotkey) # Revert on invalid key
            self.is_capturing = False
            self.clearFocus()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if self.is_capturing:
            self.is_capturing = False
            self.setText(self.current_hotkey)
        super().focusOutEvent(event)

    def _qt_key_to_string(self, event):
        key = event.key()
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            return f"f{key - Qt.Key.Key_F1 + 1}"
        
        text = event.text()
        if text and text.isalnum() and len(text) == 1:
            return text.lower()
            
        key_map = {
            Qt.Key.Key_Control: 'ctrl',
            Qt.Key.Key_Shift: 'shift',
            Qt.Key.Key_Alt: 'alt',
            Qt.Key.Key_Meta: 'cmd',
            Qt.Key.Key_Enter: 'enter',
            Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Escape: 'esc',
            Qt.Key.Key_Insert: 'insert',
            Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Home: 'home',
            Qt.Key.Key_End: 'end',
            Qt.Key.Key_PageUp: 'page_up',
            Qt.Key.Key_PageDown: 'page_down',
            Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Down: 'down',
            Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Right: 'right',
        }
        if key in key_map:
             return key_map[key]

        return None


class SettingsDialog(QDialog):
    def __init__(self, current_hotkey, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.new_hotkey = current_hotkey

        layout = QVBoxLayout(self)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Capture Hotkey:"))
        self.hotkey_input = HotkeyInput(current_hotkey)
        self.hotkey_input.key_captured.connect(self.set_new_hotkey)
        h_layout.addWidget(self.hotkey_input)
        layout.addLayout(h_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def set_new_hotkey(self, hotkey):
        self.new_hotkey = hotkey


class SnapMosaic(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapMosaic")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_bar_layout = QHBoxLayout()
        self.define_region_button = QPushButton("Define Region")
        self.snap_button = QPushButton("Snap [F7]")
        self.clear_button = QPushButton("Clear")
        self.settings_button = QPushButton("Settings")
        top_bar_layout.addWidget(self.define_region_button)
        top_bar_layout.addWidget(self.snap_button)
        top_bar_layout.addWidget(self.clear_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.settings_button)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_content_widget)
        self.scroll_layout = QGridLayout(self.scroll_content_widget)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(self.scroll_area)

        self.define_region_button.clicked.connect(self.define_region)
        self.snap_button.clicked.connect(self.trigger_capture)
        self.clear_button.clicked.connect(self.clear_grid)
        self.settings_button.clicked.connect(self.open_settings)

        self.selection_overlay = None
        self.capture_region = None
        self.config_file = "config.json"
        self.hotkey = 'f7' # Default hotkey
        self.captured_images = []
        self.load_config()
        self.update_snap_button_text()

        # Set up hotkey listener in a separate thread
        self.hotkey_thread = QThread()
        self.hotkey_listener = HotkeyListener(self.hotkey)
        self.hotkey_listener.moveToThread(self.hotkey_thread)
        self.hotkey_thread.started.connect(self.hotkey_listener.run)
        self.hotkey_listener.hotkey_pressed.connect(self.trigger_capture)
        self.hotkey_thread.start()

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.redraw_grid)

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
        self.save_config()
        self.show()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    region = config.get("capture_region")
                    if region:
                        self.capture_region = QRect(region['x'], region['y'], region['width'], region['height'])
                        print(f"Loaded capture region: {self.capture_region}")
                    self.hotkey = config.get("hotkey", 'f7')
            except json.JSONDecodeError:
                print(f"Error reading {self.config_file}. A new one will be created.")

    def save_config(self):
        if self.capture_region:
            config = {
                "capture_region": {
                    "x": self.capture_region.x(),
                    "y": self.capture_region.y(),
                    "width": self.capture_region.width(),
                    "height": self.capture_region.height()
                },
                "hotkey": self.hotkey
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)

    def trigger_capture(self):
        if not self.capture_region:
            print("Hotkey pressed, but no region defined.")
            return

        # print(f"Hotkey pressed! Capturing region: {self.capture_region}")

        # Use Qt's grabWindow for consistency, as it works for the overlay
        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio()
        pixmap = screen.grabWindow(
            0,
            int(self.capture_region.x() * dpr),
            int(self.capture_region.y() * dpr),
            int(self.capture_region.width() * dpr),
            int(self.capture_region.height() * dpr)
        )

        self.captured_images.append(pixmap)

        # Add to grid
        if not pixmap.isNull():
            viewport_width = self.scroll_area.viewport().width()
            image_width = pixmap.width()
            spacing = self.scroll_layout.spacing()
            num_columns = max(1, viewport_width // (image_width + spacing))

            count = self.scroll_layout.count()
            row = count // num_columns
            col = count % num_columns

            label = QLabel()
            label.setPixmap(pixmap)
            self.scroll_layout.addWidget(label, row, col)

    def clear_grid(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.captured_images.clear()
        print("Grid and in-memory image list cleared.")

    def closeEvent(self, event):
        if self.hotkey_thread.isRunning():
            self.hotkey_listener.stop()
            self.hotkey_thread.quit()
            self.hotkey_thread.wait()
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
                self.hotkey = new_hotkey
                self.save_config()
                self.update_snap_button_text()
                QMessageBox.information(self, "Restart Required", 
                                        "The new hotkey will be active after you restart the application.")

    def redraw_grid(self):
        if self.scroll_layout.count() == 0:
            return

        widgets = []
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                widgets.append(item.widget())

        viewport_width = self.scroll_area.viewport().width()
        if not widgets:
            return

        image_width = widgets[0].pixmap().width()
        spacing = self.scroll_layout.spacing()
        num_columns = max(1, (viewport_width - spacing) // (image_width + spacing))

        for i, widget in enumerate(widgets):
            row = i // num_columns
            col = i % num_columns
            self.scroll_layout.addWidget(widget, row, col)

def main():
    # Enable High DPI support
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = SnapMosaic()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
