# SnapMosaic

[<img src="https://github.com/MiDevel/SnapMosaic/blob/main/assets/SnapMosaic.png?raw=true" width="125"/>](image.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version](https://img.shields.io/badge/version-1.10.6-blue.svg)](https://github.com/MiDevel/SnapMosaic/releases)

A simple and efficient screen capture and review utility, built with Python and PySide6.

SnapMosaic allows you to define a specific region on your screen and capture it multiple times with a global hotkey. Captured images are displayed in a responsive grid, perfect for comparing screenshots, tracking changes, or creating step-by-step guides.

## Features

-   **Capture Region**: Define a persistent screen region for repeated captures.
-   **Global Hotkey**: Trigger captures from any application using a system-wide, configurable hotkey (default `F7`).
-   **Responsive Image Grid**: View captures in a scrollable grid that dynamically adjusts to window size.
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
