"""Quick test to verify the scaling logic works correctly"""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import sys

app = QApplication(sys.argv)

# Test 1: Large image should be scaled
large_pixmap = QPixmap(1920, 1080)
max_width = 500

if large_pixmap.width() > max_width:
    scaled = large_pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    print(f"✓ Large image scaled: {large_pixmap.width()}x{large_pixmap.height()} -> {scaled.width()}x{scaled.height()}")
    assert scaled.width() == max_width
    # Check aspect ratio maintained
    expected_height = int((max_width / large_pixmap.width()) * large_pixmap.height())
    assert abs(scaled.height() - expected_height) <= 1  # Allow 1px rounding
else:
    print("✗ Large image not scaled")

# Test 2: Small image should not be scaled
small_pixmap = QPixmap(200, 150)
display = small_pixmap
if small_pixmap.width() > max_width:
    display = small_pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
else:
    print(f"✓ Small image not scaled: {small_pixmap.width()}x{small_pixmap.height()}")

assert display.width() == 200
assert display.height() == 150

# Test 3: Exactly max_width should not be scaled
exact_pixmap = QPixmap(500, 300)
display = exact_pixmap
if exact_pixmap.width() > max_width:
    display = exact_pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
else:
    print(f"✓ Exact width image not scaled: {exact_pixmap.width()}x{exact_pixmap.height()}")

assert display.width() == 500
assert display.height() == 300

print("\n✓ All scaling tests passed!")
