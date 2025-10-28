# SnapMosaic

[<img src="https://github.com/MiDevel/SnapMosaic/blob/main/assets/SnapMosaic.png?raw=true" width="125"/>](image.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/MiDevel/SnapMosaic/releases)

A simple and efficient screen capture and review utility, built with Python and PySide6.

SnapMosaic allows you to define a specific region on your screen and capture it multiple times with a global hotkey. Captured images are displayed in a responsive grid, perfect for comparing screenshots, tracking changes, or creating step-by-step guides.

![SnapMosaic Screenshot](https://github.com/MiDevel/SnapMosaic/blob/main/docs/snap-mosaic.png?raw=true)

## Features

-   **Capture Region**: Define a persistent screen region for repeated captures.
-   **Global Hotkey**: Trigger captures from any application using a system-wide, configurable hotkey (default `F7`).
-   **Auto-Snap Mode**: Automatically capture at regular intervals with toggle hotkey (default `F8`) and configurable interval (default 10 seconds).
-   **Responsive Image Grid**: View captures in a scrollable grid that dynamically adjusts to window size. Large images are automatically scaled for display while preserving full resolution for save/copy operations.
-   **Image Management**: Copy, save, or delete captures directly from the grid. A visual indicator marks saved images.
-   **Automated Workflow**:
    -   **Auto-Copy**: Automatically copy new captures to the clipboard.
    -   **Auto-Save**: Automatically save new captures to a specified directory with configurable naming and format (PNG/JPG).
-   **System Tray Mode**: Run the application discreetly in the system tray with a context menu for quick actions.
-   **Sound Notifications**: Optional audio feedback for capture, save, and copy events.
-   **High-DPI Aware**: Ensures distortion-free captures on multi-monitor and High-DPI displays.

## Getting Started

To get started with SnapMosaic from the source code, you'll need Python 3.

### 1. Clone the Repository

First, clone this repository to your local machine:
```bash
git clone https://github.com/MiDevel/SnapMosaic.git
cd SnapMosaic
```

### 2. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

-   **Windows (PowerShell):**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```
-   **macOS & Linux (bash/zsh):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 3. Install Dependencies

With your virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Once the dependencies are installed, you can run the application directly:
```bash
python main.py
```

### Quick Start Guide

1. **Define a Capture Region**: Click "Define Region" and drag to select the area you want to capture repeatedly.

2. **Manual Capture**: 
   - Click the "Snap [F7]" button, or
   - Press `F7` (or your configured hotkey) from any application

3. **Auto-Snap Mode** (New!):
   - Click the "Auto [F8]" button or press `F8` to start automatic captures
   - The button turns green when active
   - Captures will occur at your configured interval (default: 10 seconds)
   - Click/press again to stop

4. **Manage Your Captures**:
   - **Hover** over any image to reveal action buttons
   - **Copy**: Click the clipboard icon to copy to clipboard
   - **Save**: Click the save icon to save to a file
   - **Delete**: Click the X icon to remove from grid

5. **Configure Settings**: Click "Settings" to customize:
   - **General**: Hotkeys, clipboard behavior, display width, sounds, system tray
   - **Auto-Snap**: Toggle hotkey and capture interval
   - **Auto-Save**: Automatic file saving with custom naming and formats

### Keyboard Shortcuts

SnapMosaic supports keyboard shortcuts for efficient workflow:

- **`F7`** (default, configurable): Capture the defined region
- **`F8`** (default, configurable): Toggle Auto-Snap mode on/off
- **`Escape`**: Stop Auto-Snap mode (when active)
- **`Ctrl+S`**: Quick save the last captured or currently hovered image
- **`Ctrl+C`**: Copy the last captured or currently hovered image to clipboard
- **`Delete`**: Delete the currently hovered image

*Tip: All shortcuts are shown in button and icon tooltips throughout the app.*

### Tips

- **Large Captures**: Images wider than the configured max display width (default 500px) are automatically scaled down in the grid for easier viewing, but full resolution is always preserved for save/copy operations.
- **Auto-Save Integration**: When Auto-Snap mode is active and Auto-Save is enabled, all captures are automatically saved to your configured location.
- **System Tray**: Configure the app to minimize to system tray instead of closing, keeping hotkeys active in the background.
- **Keyboard Power User**: Hover over an image and use `Ctrl+S`, `Ctrl+C`, or `Delete` for quick actions without clicking.

## Building an Executable

This project uses PyInstaller to create a standalone executable. The recommended way to build is by using the provided `SnapMosaic.spec` file, which contains the correct build configurations.

1.  **Install PyInstaller** in your virtual environment:
    ```bash
    pip install pyinstaller
    ```

2.  **Run the build command** from the project's root directory:
    ```bash
    pyinstaller SnapMosaic.spec
    ```

3.  **Find your application** in the `dist` folder that PyInstaller creates.

## Contributing

Contributions are welcome! If you have a suggestion or want to report a bug, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License with attribution required. See the [LICENSE](LICENSE) file for details.

---
*Author: Mirek Wojtowicz* | *Website: [mirekw.com](https://mirekw.com/)*
