from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QPushButton
from pynput import keyboard

class HotkeyListener(QObject):
    hotkey_pressed = Signal()

    def __init__(self, hotkey_str='f7'):
        super().__init__()
        self.hotkey_str = self._format_hotkey_for_pynput(hotkey_str)
        self.listener = None

    def _format_hotkey_for_pynput(self, key_str):
        parts = key_str.lower().split('+')
        formatted_parts = []
        for part in parts:
            if part in ('ctrl', 'alt', 'shift', 'meta'):
                formatted_parts.append(f"<{part.replace('meta', 'cmd')}>")
            elif len(part) > 1:
                # Other special keys like 'f7', 'home', 'enter'
                formatted_parts.append(f'<{part}>')
            else:
                # Regular character keys
                formatted_parts.append(part)
        return "+".join(formatted_parts)

    def on_hotkey_activated(self):
        # This callback is executed in the listener's thread.
        # Emitting a Qt signal is a thread-safe way to communicate with the main GUI thread.
        self.hotkey_pressed.emit()

    def start(self):
        if not self.hotkey_str:
            print("Cannot start listener: hotkey is not defined.")
            return False
        
        try:
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey_str: self.on_hotkey_activated
            })
            self.listener.start()
            print(f"Hotkey listener started for '{self.hotkey_str}'.")
            return True
        except Exception as e:
            print(f"Failed to register hotkey '{self.hotkey_str}': {e}")
            self.listener = None
            return False

    def stop(self):
        if self.listener and self.listener.is_alive():
            self.listener.stop()
            print("Hotkey listener stopped.")
        self.listener = None


class HotkeyInput(QPushButton):
    key_captured = Signal(str)

    def __init__(self, hotkey, parent=None):
        super().__init__(parent)
        self.hotkey_str = hotkey
        self.setText(self.hotkey_str)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.is_recording = False

    def mousePressEvent(self, event):
        self.is_recording = True
        self.setText("Press new hotkey...")
        self.setFocus()
        super().mousePressEvent(event)

    def focusOutEvent(self, event):
        if self.is_recording:
            self.is_recording = False
            self.setText(self.hotkey_str)
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in (Qt.Key.Key_unknown, Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        modifiers = event.modifiers()
        mod_map = {
            Qt.KeyboardModifier.ControlModifier: "ctrl",
            Qt.KeyboardModifier.AltModifier: "alt",
            Qt.KeyboardModifier.ShiftModifier: "shift",
            Qt.KeyboardModifier.MetaModifier: "meta",
        }
        mod_parts = [name for mod, name in mod_map.items() if modifiers & mod]

        key_map = {
            Qt.Key.Key_Insert: 'insert',
            Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Home: 'home',
            Qt.Key.Key_End: 'end',
            Qt.Key.Key_PageUp: 'page_up',
            Qt.Key.Key_PageDown: 'page_down',
            Qt.Key.Key_Enter: 'enter',
            Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Escape: 'esc',
            Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Down: 'down',
            Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Right: 'right',
            Qt.Key.Key_Tab: 'tab',
            Qt.Key.Key_Backspace: 'backspace',
            Qt.Key.Key_Space: 'space',
            Qt.Key.Key_CapsLock: 'caps_lock',
            Qt.Key.Key_NumLock: 'num_lock',
            Qt.Key.Key_ScrollLock: 'scroll_lock',
            Qt.Key.Key_Print: 'print_screen',
            Qt.Key.Key_Pause: 'pause',
        }

        if key in key_map:
            key_text = key_map[key]
        else:
            key_text = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText).lower()

        if not key_text or key_text in mod_parts:
            return

        # Handle cases where toString() includes modifiers, e.g., "ctrl+c"
        if '+' in key_text:
            parts = key_text.split('+')
            key_text = parts[-1]
            for part in parts[:-1]:
                if part not in mod_parts:
                    mod_parts.append(part)

        self.hotkey_str = "+".join(sorted(mod_parts) + [key_text])
        self.setText(self.hotkey_str)
        self.key_captured.emit(self.hotkey_str)
        self.is_recording = False
        self.clearFocus()
