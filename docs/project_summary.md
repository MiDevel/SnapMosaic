# SnapMosaic Project Summary

This document provides a technical overview of the SnapMosaic application, its architecture, and the key development decisions made. It is intended for developers to quickly understand the codebase for maintenance or feature additions.

## 1. Project Goal

The primary goal was to create a lightweight, easy-to-use screen cross-platform capture utility. The application allows users to define a screen region, capture it repeatedly using a global hotkey, view the captures in a responsive grid, and manage them with copy, save and delete options. Key features include multi-monitor support, High-DPI correctness, a configurable hotkey, and a comprehensive auto-save system.

## 2. Technology Stack

- **Language**: Python 3
- **UI Framework**: PySide6 (Qt for Python)
- **Global Hotkeys**: pynput
- **Sound**: playsound
- **Packaging**: PyInstaller

## 3. Core Architecture

The application was refactored from a single-file script into a modular package (`snap_mosaic`) to improve maintainability and organization. The core classes are now located in their own modules:

- **`SnapMosaic` (`main_window.py`)**: The main application `QMainWindow`. It manages the primary UI, orchestrates all major functionality, and handles application state and configuration.

- **`SelectionOverlay` & `HoverLabel` (`widgets.py`)**: Custom widgets for UI interaction. `SelectionOverlay` handles drawing the capture region, while `HoverLabel` displays captured images and provides interactive copy/save/delete controls.

- **`HotkeyListener` & `HotkeyInput` (`hotkey.py`)**: Classes responsible for the global hotkey system. `HotkeyListener` uses `pynput` to listen for system-wide key presses, while `HotkeyInput` is the UI widget for setting a new hotkey.

- **`Config` (`config.py`)**: A robust configuration manager that handles loading and saving user settings to a `SnapMosaic.json` file. It is designed to be forward-compatible by merging a complete set of default settings with the user's saved settings, preventing crashes when new configuration keys are introduced.

- **`SettingsDialog` & `AboutDialog` (`dialogs.py`)**: The UI dialogs for the application. `SettingsDialog` provides a clean, tabbed interface ("General" and "Auto-Save") for all user-configurable options.

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

- A simple `SnapMosaic.json` file stores persistent settings.
- **Stored Values**:
    - The `(x, y, width, height)` of the last capture region
    - The string representation of the hotkey (e.g., `"f7"`)
    - The boolean value of the auto-copy to clipboard option
    - Auto-save configuration (enabled, location, prefix, suffix, format, quality)
    - System tray integration (close to tray, show notification)
    - Sound effects enabled (boolean)

The configuration is loaded on startup and saved whenever any of the above values is changed.

### Interactive Image Management

- **Requirement**: Allow users to save or delete individual images directly from the grid.
- **Implementation**:
    1.  A custom `HoverLabel` class was created, inheriting from `QLabel`. This widget is responsible for managing its own state (hovering, saved) and drawing all interactive elements.
    2.  **Hover Effect**: On `mouseEnterEvent`, the label draws a semi-transparent overlay and reveals "Save" and "Delete" icons in the top-right corner. The icons also provide visual feedback (a highlight tint) and tooltips when hovered over individually.
    3.  **Actions**: Clicking an icon emits a `save_requested` or `delete_requested` signal. The `SnapMosaic` main window has slots connected to these signals to handle the file-saving dialog or remove the widget from the grid.
    4.  **Saved Indicator**: After an image is successfully saved, a boolean flag `is_saved` is set on the `HoverLabel` instance. The `paintEvent` checks this flag and, if true, draws a green checkmark icon with a semi-transparent circular background in the bottom-left corner for persistent, high-visibility feedback.

### Sound Effects

- **Requirement**: Provide optional, audible feedback for key user actions.
- **Evolution of Solution**:
    1.  The initial implementation used Qt's native `QSoundEffect` class. This approach suffered from inconsistent and truncated playback, especially with very short `.wav` files. The root cause was determined to be a combination of garbage collection issues (where the player object was destroyed before the sound finished) and potential incompatibilities with certain audio backends or file formats.
    2.  After multiple attempts to create a reliable player pool with `QSoundEffect`, the decision was made to switch to a more robust, dedicated library.
    3.  The final, successful solution uses the third-party `playsound` library. It is simple, has no complex dependencies, and has proven to be highly reliable. To prevent the UI from freezing during playback, each sound is played in its own non-blocking background thread (`threading.Thread`).
- **Configuration**: A new "Enable sounds" checkbox was added to the General settings tab, allowing users to toggle all sound effects on or off. This setting is persisted in `SnapMosaic.json` as `sounds_enabled`.

### System Tray Integration

- **Close Behavior**: Instead of quitting, the application's close button can be configured to hide the main window, leaving the app running in the background and accessible via a system tray icon.
- **Tray Icon Menu**: A right-click on the tray icon provides a context menu with essential actions: "Show Window," "Define new Region," and "Quit."
- **Interaction**: A single left-click on the tray icon toggles the visibility of the main window.
- **Configuration**: This behavior, along with the associated notification, is fully configurable in the settings.

### Asset & Resource Handling

- **Problem**: When an application is bundled with PyInstaller, it runs from a temporary directory. This breaks simple relative paths used during development (e.g., `snap_mosaic/icons/clipboard.svg`), causing "file not found" errors for assets like icons in the final executable.
- **Solution**: A helper function, `utils.resource_path()`, was created. This function detects whether the application is running from source code or as a bundled executable (by checking for `sys._MEIPASS`, a variable set by PyInstaller). It then constructs the correct, absolute path to the requested resource.
- **Implementation**: All code that loads an external asset (icons, images) has been refactored to use `resource_path()`. This makes asset loading robust and reliable, ensuring that the application works identically in both development and distributed environments.

## 5. Final Refinements & UI Polish

The final development phase focused on improving robustness, usability, and visual appeal.

### UI Enhancements & Asset Management

- **Custom Icons**: The standard Qt icons for "Settings" and "About" were replaced with custom white SVG icons to match the application's dark theme.
- **Application Icon**: A custom application icon (`.ico` on Windows, `.svg` on other platforms) was added. This icon is displayed in the window's title bar and the system taskbar.
- **Asset Bundling**: The `SnapMosaic.spec` file for PyInstaller was updated to bundle the `assets`, `snap_mosaic/icons`, and `snap_mosaic/sounds` directories. This ensures all icons and sound files are included in the standalone executable, making it fully portable.
- **Image Border**: A subtle 1px border was added via stylesheet to captured images in the grid. This visually separates them from the application background, which is especially helpful when a captured image has edges of a similar color.
