# AGENTS.md - AI Assistant Guide for SnapMosaic

This document provides essential context and guidelines for AI assistants working on the SnapMosaic project. It summarizes the architecture, key decisions, and common pitfalls to help you provide accurate and effective assistance.

## Project Overview

**SnapMosaic** is a cross-platform screen capture utility built with Python and PySide6 (Qt). It allows users to define a screen region, capture it repeatedly via a global hotkey, view captures in a responsive grid, and manage them with copy/save/delete operations.

**Key Features:**
- Multi-monitor support with High-DPI correctness
- Global hotkey capture (configurable)
- Auto-snap mode with configurable interval
- Responsive image grid with hover interactions
- Auto-save functionality
- System tray integration
- Sound effects for user feedback
- Persistent configuration

## Technology Stack

- **Language:** Python 3
- **UI Framework:** PySide6 (Qt for Python)
- **Global Hotkeys:** pynput
- **Sound:** playsound (v1.2.2)
- **Packaging:** PyInstaller

## Project Structure

```
SnapMosaic/
├── main.py                    # Entry point
├── snap_mosaic/              # Main package
│   ├── __init__.py           # Package initialization with __version__
│   ├── main_window.py        # SnapMosaic class (main QMainWindow)
│   ├── widgets.py            # SelectionOverlay, HoverLabel
│   ├── hotkey.py             # HotkeyListener, HotkeyInput
│   ├── config.py             # Config class for settings management
│   ├── dialogs.py            # SettingsDialog, AboutDialog
│   ├── utils.py              # Helper functions (resource_path, etc.)
│   ├── icons/                # SVG icons for UI
│   └── sounds/               # WAV files for sound effects
├── assets/                   # Application icons (.ico, .svg)
├── docs/                     # Documentation
│   └── project_summary.md    # Detailed technical overview
├── SnapMosaic.json           # User configuration (generated at runtime)
├── SnapMosaic.spec           # PyInstaller specification
└── requirements.txt          # Python dependencies
```

## Core Architecture

### Main Classes

1. **`SnapMosaic` (`main_window.py`)**
   - Main application window (QMainWindow)
   - Orchestrates all functionality
   - Manages application state and configuration
   - Handles hotkey listener lifecycle
   - Implements system tray integration

2. **`SelectionOverlay` (`widgets.py`)**
   - Frameless fullscreen widget for region selection
   - Captures virtual desktop background for visual context
   - Handles mouse drag-to-select interaction

3. **`HoverLabel` (`widgets.py`)**
   - Custom QLabel for displaying captured images
   - Stores both display pixmap (scaled) and original pixmap (full resolution)
   - Interactive hover effects with save/delete buttons
   - Visual feedback for saved state (green checkmark)
   - Always saves/copies the original full-resolution image

4. **`HotkeyListener` (`hotkey.py`)**
   - Uses `pynput.keyboard.GlobalHotKeys` for reliable hotkey handling
   - Runs in a QThread to avoid blocking the UI
   - Emits Qt signal when hotkey is pressed

5. **`HotkeyInput` (`hotkey.py`)**
   - Custom QLineEdit for capturing new hotkey combinations
   - Provides user-friendly key sequence display

6. **`Config` (`config.py`)**
   - Forward-compatible configuration management
   - Merges default settings with user settings
   - Auto-saves on any change

7. **`SettingsDialog` (`dialogs.py`)**
   - Tabbed interface (General, Auto-Snap, Auto-Save)
   - All user-configurable options in one place

## Critical Implementation Details

### 1. High-DPI & Multi-Monitor Image Capture

**THE MOST IMPORTANT DECISION:**
- **Always use Qt's native `QScreen.grabWindow(0)`** for screen capture
- **Never use third-party libraries like `mss`** - they cause coordinate mismatches
- Qt's method is inherently aware of Qt coordinate system and display scaling
- Both selection overlay background and final captures use `grabWindow(0)`

**Why this matters:** This was the solution to persistent image distortion bugs on High-DPI and multi-monitor setups. Any attempt to use other capture methods will likely reintroduce these issues.

### 2. Asset & Resource Paths

**Critical for PyInstaller compatibility:**
- Always use `utils.resource_path()` for loading assets
- This function handles both development and bundled executable scenarios
- It checks for `sys._MEIPASS` (PyInstaller's temp directory)
- Direct relative paths like `'snap_mosaic/icons/clipboard.svg'` will fail in bundled exe

**Example:**
```python
from snap_mosaic.utils import resource_path
icon_path = resource_path('snap_mosaic/icons/settings.svg')
```

### 3. Sound Effects

**Architecture Decision:**
- Uses `playsound` library (v1.2.2 specifically)
- Each sound plays in a separate background thread to avoid UI freezing
- Previously attempted `QSoundEffect` but had reliability issues

**Implementation pattern:**
```python
if self.config.get('sounds_enabled', True):
    sound_path = resource_path('snap_mosaic/sounds/capture.wav')
    threading.Thread(target=playsound, args=(sound_path,), daemon=True).start()
```

### 4. Global Hotkey System

**Key points:**
- Uses `pynput.keyboard.GlobalHotKeys` (not manual Listener)
- Runs in a QThread for non-blocking operation
- Hotkey stored as string representation (e.g., "f7", "ctrl+shift+s")
- Robust error handling for hotkey registration failures

### 5. Responsive Grid Layout

**How it works:**
- Images in QGridLayout inside QScrollArea
- Window resize triggers debounced QTimer (150ms)
- Timer timeout recalculates column count based on viewport width
- Grid is repopulated with existing widgets

**Don't:** Try to use QFlowLayout or other custom layouts - the current approach is proven and reliable.

### 6. Configuration System

**Forward-compatibility design:**
- `get_default_config()` always returns a complete settings dictionary
- User's saved settings are merged with defaults on load
- Missing keys automatically get default values
- Prevents crashes when new settings are added in updates

### 7. Image Display Scaling

**Problem solved:** Large screen captures (e.g., full screen on 4K monitors) made the grid unusable as individual images were larger than the application window.

**Implementation:**
- Configurable `max_display_width` setting (default 500px)
- Images wider than max are scaled down for display only
- Original full-resolution image is preserved separately
- Save and copy operations always use the original full-resolution image
- Smaller images are never upscaled
- Aspect ratio is always preserved during scaling
- Grid layout calculations use the display width

**Key design:**
- `HoverLabel` constructor accepts both `display_pixmap` and `original_pixmap`
- `trigger_capture()` creates scaled display version if needed
- `save_image()` and `copy_image_to_clipboard()` use `original_pixmap`
- Changing the max width in settings triggers immediate grid redraw

### 8. Auto-Snap Mode

**Purpose:** Automatically capture the defined region at regular intervals without manual intervention.

**Implementation:**
- Configurable toggle hotkey (default F8)
- Configurable capture interval (default 10 seconds, range 1-3600s)
- Visual button state with green background when active
- QTimer-based interval triggering
- Integrates with auto-save if enabled
- Automatically stops when defining new region

**Key design:**
- `auto_button` is a checkable QPushButton with custom styling
- `is_auto_snapping` flag tracks state
- `auto_snap_timer` QTimer triggers `trigger_capture()` at intervals
- `start_auto_snap()` validates region exists before starting
- `stop_auto_snap()` called on region definition and app quit
- Separate hotkey listener for toggle functionality

**Settings stored in `SnapMosaic.json`:**
- `capture_region`: Last selected region (x, y, width, height)
- `hotkey`: Global hotkey string for manual capture
- `auto_snap_hotkey`: Global hotkey string for toggling auto-snap
- `auto_snap_interval`: Interval in seconds between auto-captures
- `auto_copy_to_clipboard`: Boolean
- `max_display_width`: Maximum width (in pixels) for displaying large captures
- `auto_save_*`: Auto-save configuration
- `minimize_to_tray`, `show_tray_notification`: System tray options
- `sounds_enabled`: Sound effects toggle
- `window_geometry`: Saved window position/size

## Common Tasks & Patterns

### Adding a New Setting

1. Add default value in `config.py` → `get_default_config()`
2. Add UI control in `dialogs.py` → appropriate tab in `SettingsDialog`
3. Load setting in `main_window.py` → `load_app_config()`
4. Save setting when changed using `self.config.set(key, value)`
5. Handle setting changes in `open_settings()` if live updates needed

### Adding a New Icon

1. Place SVG in `snap_mosaic/icons/`
2. Update `SnapMosaic.spec` if not already including the icons directory
3. Load using: `QIcon(resource_path('snap_mosaic/icons/youricon.svg'))`

### Adding a New Sound

1. Place WAV file in `snap_mosaic/sounds/`
2. Update `SnapMosaic.spec` if not already including the sounds directory
3. Play using the threading pattern (see Sound Effects section above)

## Testing & Validation

### Always Test These Scenarios

1. **High-DPI displays** - Images should not be distorted or sheared
2. **Multi-monitor setups** - Region selection should work across all monitors
3. **PyInstaller bundle** - Assets must load correctly in the exe
4. **Hotkey conflicts** - App should handle registration failures gracefully
5. **Window resizing** - Grid should reflow smoothly without flickering

### Building the Executable

```bash
pyinstaller SnapMosaic.spec
```

The `.spec` file is already configured to bundle all necessary assets.

## Known Limitations & Design Decisions

1. **playsound version pinned to 1.2.2** - Later versions have breaking changes
2. **No video capture** - By design, only still images
3. **Hotkey requires restart** - Changing hotkeys requires stopping/starting the listeners
4. **Grid column calculation** - Based on display width of images
5. **System tray on Linux** - May have limited support depending on desktop environment
6. **Display scaling non-retroactive** - Changing max_display_width doesn't rescale existing captures (by design - avoids reprocessing)
7. **Auto-snap state not persisted** - Auto-snap always starts disabled on app launch (by design - prevents unwanted captures)
8. **Auto-snap interval changes** - Live-updated if auto-snap is running, otherwise takes effect on next start

## Things to NEVER Do

1. ❌ Replace `QScreen.grabWindow()` with `mss` or similar libraries
2. ❌ Use direct file paths without `resource_path()`
3. ❌ Use `QSoundEffect` for sound playback
4. ❌ Block the main thread with long-running operations
5. ❌ Modify `Config` class to break forward compatibility
6. ❌ Remove default values from `get_default_config()`

## Documentation Hierarchy

1. **This file (AGENTS.md)** - Quick reference for AI assistants
2. **docs/project_summary.md** - Detailed technical overview with rationale
3. **README.md** - User-facing documentation
4. **Code comments** - Inline documentation for complex logic

## Version Information

- Version string is stored in `snap_mosaic/__init__.py` as `__version__`
- Displayed in About dialog
- Should follow semantic versioning (MAJOR.MINOR.PATCH)

## Questions to Ask Before Making Changes

1. Will this work correctly on High-DPI displays?
2. Will this work in the PyInstaller bundle?
3. Does this maintain backward compatibility with existing configs?
4. Will this block the UI thread?
5. Is there a Qt-native solution instead of adding a new dependency?
6. If adding timers, are they properly stopped on cleanup?
7. If adding hotkeys, is there proper error handling for registration failures?

## Useful Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py

# Build executable
pyinstaller SnapMosaic.spec

# Test the executable
.\dist\SnapMosaic\SnapMosaic.exe
```

## Getting Help

When stuck, refer to:
1. This file for architecture decisions
2. `docs/project_summary.md` for detailed implementation history
3. Code comments for specific logic explanations
4. Qt documentation for PySide6 API questions

---

**Last Updated:** 2025-10-27  
**Project Version:** Check `snap_mosaic/__init__.py`
