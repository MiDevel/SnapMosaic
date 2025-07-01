# SnapMosaic Project Summary

This document provides a technical overview of the SnapMosaic application, its architecture, and the key development decisions made. It is intended for developers to quickly understand the codebase for maintenance or feature additions.

## 1. Project Goal

The primary goal was to create a lightweight, easy-to-use screen cross-platform capture utility. The application allows users to define a screen region, capture it repeatedly using a global hotkey, view the captures in a responsive grid, and manage them with save and delete options. Key features include multi-monitor support, High-DPI correctness, and a configurable hotkey.

## 2. Technology Stack

- **Language**: Python 3
- **UI Framework**: PySide6 (Qt for Python)
- **Global Hotkeys**: pynput
- **Packaging**: PyInstaller

## 3. Core Architecture

The application was refactored from a single-file script into a modular package (`snap_mosaic`) to improve maintainability and organization. The core classes are now located in their own modules:

- **`SnapMosaic` (`main_window.py`)**: The main application `QMainWindow`. It manages the primary UI, orchestrates all major functionality, and handles application state and configuration.

- **`SelectionOverlay` & `HoverLabel` (`widgets.py`)**: Custom widgets for UI interaction. `SelectionOverlay` handles drawing the capture region, while `HoverLabel` displays captured images and provides interactive save/delete controls.

- **`HotkeyListener` & `HotkeyInput` (`hotkey.py`)**: Classes responsible for the global hotkey system. `HotkeyListener` uses `pynput` to listen for system-wide key presses, while `HotkeyInput` is the UI widget for setting a new hotkey.

- **`SettingsDialog` & `AboutDialog` (`dialogs.py`)**: Standard `QDialog` subclasses for the settings and about windows.

- **`Config` (`config.py`)**: A simple class to manage loading and saving the `config.json` file.

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

- **Requirement**: A global hotkey that works even when the application is not in focus, with robust handling for complex key combinations and user feedback on registration success or failure.
- **Implementation & Evolution**:
    1.  The implementation was refactored from a manual `pynput.keyboard.Listener` in a `QThread` to using `pynput.keyboard.GlobalHotKeys`. This was done to provide more reliable handling of compound hotkeys.
    2.  The `GlobalHotKeys` class handles its own non-blocking thread, which simplified the design by removing the need for a dedicated `QThread` and the associated cleanup code (`thread.wait()`).
    3.  The `HotkeyListener.start()` method attempts to register the hotkey and returns `True` or `False`. This enables the UI to give immediate feedback if a hotkey is already in use and revert to the previous one if needed.
    4.  To support special keys (like `Insert`, `Home`, `PageUp`), a mapping was added to the `HotkeyInput` widget to translate `Qt.Key` names into `pynput`-compatible strings.
    5.  **Clean Shutdown**: The main window's `closeEvent` calls the listener's `stop()` method, which correctly terminates the `pynput` listener, preventing the application from hanging on exit.

### Configuration

- A simple `config.json` file stores persistent settings.
- **Stored Values**: The `(x, y, width, height)` of the last capture region and the string representation of the hotkey (e.g., `"f7"`).
- The configuration is loaded on startup and saved whenever the region or hotkey is changed.

### Interactive Image Management

- **Requirement**: Allow users to save or delete individual images directly from the grid.
- **Implementation**:
    1.  A custom `HoverLabel` class was created, inheriting from `QLabel`. This widget is responsible for managing its own state (hovering, saved) and drawing all interactive elements.
    2.  **Hover Effect**: On `mouseEnterEvent`, the label draws a semi-transparent overlay and reveals "Save" and "Delete" icons in the top-right corner. The icons also provide visual feedback (a highlight tint) and tooltips when hovered over individually.
    3.  **Actions**: Clicking an icon emits a `save_requested` or `delete_requested` signal. The `SnapMosaic` main window has slots connected to these signals to handle the file-saving dialog or remove the widget from the grid.
    4.  **Saved Indicator**: After an image is successfully saved, a boolean flag `is_saved` is set on the `HoverLabel` instance. The `paintEvent` checks this flag and, if true, draws a green checkmark icon with a semi-transparent circular background in the bottom-left corner for persistent, high-visibility feedback.

## 5. Final Refinements & UI Polish

The final development phase focused on improving robustness, usability, and visual appeal.

### UI Enhancements & Asset Management

- **Custom Icons**: The standard Qt icons for "Settings" and "About" were replaced with custom white SVG icons to match the application's dark theme.
- **Application Icon**: A custom application icon (`.ico` on Windows, `.svg` on other platforms) was added. This icon is displayed in the window's title bar and the system taskbar.
- **Asset Bundling**: The `SnapMosaic.spec` file for PyInstaller was updated to bundle the `assets` and `snap_mosaic/icons` directories. This ensures all icons are included in the standalone executable, making it fully portable.
- **Image Border**: A subtle 1px border was added via stylesheet to captured images in the grid. This visually separates them from the application background, which is especially helpful when a captured image has edges of a similar color.
