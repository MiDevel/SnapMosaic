from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QCheckBox, QGroupBox, 
    QFormLayout, QRadioButton, QComboBox, QSpinBox,
    QFileDialog, QDialogButtonBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from .hotkey import HotkeyInput

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.config = config
        self.new_hotkey = self.config.get('hotkey')

        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        # Create tabs
        general_tab = self.create_general_tab()
        auto_save_tab = self.create_auto_save_tab()

        # Add tabs
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(auto_save_tab, "Auto-Save")

        main_layout.addWidget(tab_widget)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.apply_settings)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def create_general_tab(self):
        general_tab = QWidget()
        layout = QVBoxLayout(general_tab)

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

        # Minimize to tray setting
        self.minimize_to_tray_checkbox = QCheckBox("Close to system tray instead of quitting")
        self.minimize_to_tray_checkbox.setChecked(self.config.get('minimize_to_tray', False))
        layout.addWidget(self.minimize_to_tray_checkbox)

        # Notification sub-setting
        self.show_tray_notification_checkbox = QCheckBox("Show notification on close")
        self.show_tray_notification_checkbox.setChecked(self.config.get('show_tray_notification', True))
        
        notification_layout = QHBoxLayout()
        notification_layout.addSpacing(20) # Indentation
        notification_layout.addWidget(self.show_tray_notification_checkbox)
        layout.addLayout(notification_layout)

        # Connect signal to enable/disable sub-setting and set initial state
        self.minimize_to_tray_checkbox.toggled.connect(self.show_tray_notification_checkbox.setEnabled)
        self.show_tray_notification_checkbox.setEnabled(self.minimize_to_tray_checkbox.isChecked())

        layout.addStretch()
        return general_tab

    def create_auto_save_tab(self):
        auto_save_tab = QWidget()
        layout = QVBoxLayout(auto_save_tab)

        self.auto_save_group = QGroupBox("Auto-Save")
        self.auto_save_group.setCheckable(True)
        self.auto_save_group.setChecked(self.config.get('auto_save_enabled', False))
        group_layout = QFormLayout()

        # Save Location
        location_layout = QHBoxLayout()
        self.location_edit = QLineEdit(self.config.get('auto_save_location'))
        location_layout.addWidget(self.location_edit)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_for_folder)
        location_layout.addWidget(self.browse_button)
        group_layout.addRow("Save Location:", location_layout)

        # Filename Prefix
        self.prefix_edit = QLineEdit(self.config.get('auto_save_prefix'))
        group_layout.addRow("Filename Prefix:", self.prefix_edit)

        # Suffix Type
        suffix_layout = QHBoxLayout()
        self.timestamp_radio = QRadioButton("Timestamp")
        self.numeric_radio = QRadioButton("Numeric")
        is_numeric = self.config.get('auto_save_suffix_type') == 'numeric'
        self.numeric_radio.setChecked(is_numeric)
        self.timestamp_radio.setChecked(not is_numeric)
        suffix_layout.addWidget(self.timestamp_radio)
        suffix_layout.addWidget(self.numeric_radio)
        suffix_layout.addStretch()
        group_layout.addRow("Filename Suffix:", suffix_layout)

        # Image Format
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(['png', 'jpg'])
        self.format_combo.setCurrentText(self.config.get('auto_save_format'))
        self.format_combo.currentTextChanged.connect(self.update_quality_visibility)
        format_layout.addWidget(self.format_combo)

        # JPG Quality
        self.quality_label = QLabel("JPG Quality:")
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(1, 100)
        self.quality_spinbox.setValue(self.config.get('auto_save_jpg_quality'))
        self.quality_spinbox.setSuffix('%')
        format_layout.addWidget(self.quality_label)
        format_layout.addWidget(self.quality_spinbox)
        format_layout.addStretch()
        group_layout.addRow("Image Format:", format_layout)

        self.auto_save_group.setLayout(group_layout)
        layout.addWidget(self.auto_save_group)
        layout.addStretch()

        # Set initial state
        self.update_quality_visibility(self.format_combo.currentText())

        return auto_save_tab

    def set_new_hotkey(self, hotkey):
        self.new_hotkey = hotkey

    def browse_for_folder(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self.location_edit.text()
        )
        if directory:
            self.location_edit.setText(directory)

    def update_quality_visibility(self, text):
        is_jpg = text.lower() == 'jpg'
        self.quality_label.setVisible(is_jpg)
        self.quality_spinbox.setVisible(is_jpg)

    def apply_settings(self):
        self.config.set('hotkey', self.new_hotkey)
        self.config.set('auto_copy_to_clipboard', self.auto_copy_checkbox.isChecked())
        self.config.set('minimize_to_tray', self.minimize_to_tray_checkbox.isChecked())
        self.config.set('show_tray_notification', self.show_tray_notification_checkbox.isChecked())

        self.config.set('auto_save_enabled', self.auto_save_group.isChecked())
        self.config.set('auto_save_location', self.location_edit.text())
        self.config.set('auto_save_prefix', self.prefix_edit.text())
        suffix_type = 'numeric' if self.numeric_radio.isChecked() else 'timestamp'
        self.config.set('auto_save_suffix_type', suffix_type)
        self.config.set('auto_save_format', self.format_combo.currentText())
        self.config.set('auto_save_jpg_quality', self.quality_spinbox.value())
        
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
