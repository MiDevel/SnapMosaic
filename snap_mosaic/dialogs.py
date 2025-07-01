from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt
from .hotkey import HotkeyInput

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config = config
        self.new_hotkey = self.config.get('hotkey')

        layout = QVBoxLayout(self)

        # Hotkey setting
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Capture Hotkey:"))
        self.hotkey_input = HotkeyInput(self.new_hotkey)
        self.hotkey_input.key_captured.connect(self.set_new_hotkey)
        h_layout.addWidget(self.hotkey_input)
        layout.addLayout(h_layout)

        # Auto-copy setting
        self.auto_copy_checkbox = QCheckBox("Auto-copy new captures to clipboard")
        self.auto_copy_checkbox.setChecked(self.config.get('auto_copy_to_clipboard', False))
        layout.addWidget(self.auto_copy_checkbox)

        layout.addWidget(QLabel(""))

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.apply_settings)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def set_new_hotkey(self, hotkey):
        self.new_hotkey = hotkey

    def apply_settings(self):
        self.config.set('hotkey', self.new_hotkey)
        self.config.set('auto_copy_to_clipboard', self.auto_copy_checkbox.isChecked())
        self.accept()

class AboutDialog(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SnapMosaic")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        title = QLabel("SnapMosaic")
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel(f"Version: {version}"))
        layout.addWidget(QLabel("Author: Mirek Wojtowicz"))
        website_label = QLabel('Website: <a href="https://mirekw.com">https://mirekw.com</a>')
        website_label.setTextFormat(Qt.TextFormat.RichText)
        website_label.setOpenExternalLinks(True)
        layout.addWidget(website_label)

        github_label = QLabel('GitHub: <a href="https://github.com/MiDevel/SnapMosaic">https://github.com/MiDevel/SnapMosaic</a>')
        github_label.setTextFormat(Qt.TextFormat.RichText)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)
        layout.addWidget(QLabel("License: MIT with attribution required"))

        layout.addWidget(QLabel(""))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
