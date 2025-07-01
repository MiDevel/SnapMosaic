# SnapMosaic Project Summary

This document provides a technical overview of the SnapMosaic application, its architecture, and the key development decisions made. It is intended for developers to quickly understand the codebase for maintenance or feature additions.

## 1. Project Goal

The primary goal was to create a lightweight, easy-to-use screen capture utility for Windows. The application allows users to define a screen region, capture it repeatedly using a global hotkey, and view the captures in a responsive grid. Key requirements included multi-monitor support, High-DPI correctness, and a configurable hotkey.

## 2. Technology Stack

- **Language**: Python 3
- **UI Framework**: PySide6 (Qt for Python)
- **Global Hotkeys**: pynput
- **Packaging**: PyInstaller

## 3. Core Architecture

The application is built around a few key classes in `main.py`:

- **`SnapMosaic` (QMainWindow)**: The main application class. It manages the primary UI, including the top bar buttons and the image grid. It orchestrates all major functionality, such as initiating region selection, handling configuration, and displaying captured images.

- **`SelectionOverlay` (QWidget)**: A frameless, transparent widget that covers all screens. It displays a static screenshot of the desktop and uses a `QRubberBand` to allow the user to draw the capture region. It emits a `selection_made` signal with the `QRect` of the selected area.

- **`HotkeyListener` (QObject)**: Runs in a separate `QThread` to listen for global hotkey presses without blocking the UI. It uses `pynput.keyboard.Listener` and emits a `hotkey_pressed` signal when the designated key is pressed.

- **`SettingsDialog` (QDialog)**: A modal dialog for application settings. It currently contains the `HotkeyInput` widget to allow users to define a new global hotkey.

- **`HotkeyInput` (QPushButton)**: A custom widget that captures the next keypress to set as the new hotkey.

## 4. Key Implementation Details & Decisions

### Image Capture & Distortion Fix

- **Initial Problem**: The most significant challenge was a persistent image distortion bug, where captured images appeared sheared or shifted. This was caused by coordinate mismatches between logical pixels (used by the UI) and physical pixels (used by screen capture libraries) on High-DPI and multi-monitor setups.
- **Evolution of Solution**:
    1.  Initially used the `mss` library. Attempts to fix the issue by scaling coordinates with `devicePixelRatio` were unsuccessful and produced inconsistent results.
    2.  The final, successful solution was to **abandon `mss` entirely and use Qt's native screen capture method**: `QScreen.grabWindow()`. This method is inherently aware of the Qt coordinate system and display scaling, which completely resolved the distortion issue.
    3.  Both the selection overlay background and the final captures use `grabWindow(0)` to capture the entire virtual desktop, ensuring consistency.

### Responsive Image Grid

- **Requirement**: Display captured images in a grid that reflows as the window is resized.
- **Implementation**: 
    1.  The images are held in a `QWidget` with a `QGridLayout` placed inside a `QScrollArea`.
    2.  A `resizeEvent` on the main window triggers a `QTimer` (debounced to 150ms to avoid excessive calculations).
    3.  The timer's `timeout` calls a `redraw_grid()` method, which recalculates the optimal number of columns based on the current viewport width and the fixed width of the images. It then re-populates the `QGridLayout` with the image widgets.

### Global Hotkey Listener

- **Requirement**: A global hotkey that works even when the application is not in focus.
- **Implementation**: 
    1.  The `pynput` listener is run inside a `QThread` to prevent it from freezing the GUI.
    2.  **Hang on Close Fix**: The application initially hung on exit because the listener thread was not being stopped correctly. This was fixed by adding a `stop()` method to the `HotkeyListener` class that calls `pynput.keyboard.Listener.stop()`. The main window's `closeEvent` now calls this method and then `self.hotkey_thread.wait()` to ensure a clean shutdown.

### Configuration

- A simple `config.json` file stores persistent settings.
- **Stored Values**: The `(x, y, width, height)` of the last capture region and the string representation of the hotkey (e.g., `"f7"`).
- The configuration is loaded on startup and saved whenever the region or hotkey is changed.
