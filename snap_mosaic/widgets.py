from PySide6.QtWidgets import (
    QWidget, QLabel, QApplication, QRubberBand, QToolTip, QStyle
)
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QRect, Signal

class SelectionOverlay(QWidget):
    selection_made = Signal(QRect)

    def __init__(self, screen_pixmap):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geometry)
        self.pixmap = screen_pixmap

        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.origin:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if self.origin:
            self.rubber_band.hide()
            selection_rect = QRect(self.origin, event.pos()).normalized()
            self.selection_made.emit(selection_rect)
            self.close()

class HoverLabel(QLabel):
    delete_requested = Signal(object)
    save_requested = Signal(object)

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.is_hovering = False
        self.is_saved = False
        self.hovered_icon = None # Can be 'save', 'delete', or None

        # Define "hotspots" for the buttons
        icon_size = 24
        margin = 5
        self.save_rect = QRect(self.width() - 2 * (icon_size + margin), margin, icon_size, icon_size)
        self.delete_rect = QRect(self.width() - (icon_size + margin), margin, icon_size, icon_size)

        self.setMouseTracking(True) # Needed for mouseMoveEvent

    def enterEvent(self, event):
        self.is_hovering = True
        self.update() # Trigger a repaint
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovering = False
        self.hovered_icon = None
        QToolTip.hideText()
        self.update() # Trigger a repaint
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_hovering:
            pos = event.pos()
            old_hovered_icon = self.hovered_icon

            if self.save_rect.contains(pos):
                self.hovered_icon = 'save'
                QToolTip.showText(event.globalPos(), "Save Image", self)
            elif self.delete_rect.contains(pos):
                self.hovered_icon = 'delete'
                QToolTip.showText(event.globalPos(), "Delete Image", self)
            else:
                self.hovered_icon = None
                QToolTip.hideText()

            if self.hovered_icon != old_hovered_icon:
                self.update() # Repaint only if hover state changes
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.is_hovering:
            if self.save_rect.contains(event.pos()):
                # Pass the label instance itself
                self.save_requested.emit(self)
            elif self.delete_rect.contains(event.pos()):
                self.delete_requested.emit(self)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event) # First, draw the base pixmap

        # If there's no custom drawing to do, exit early.
        if not self.is_hovering and not self.is_saved:
            return

        painter = QPainter(self)

        if self.is_hovering:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw semi-transparent overlay and border
            overlay_color = QColor(0, 0, 0, 127) # Black with 50% opacity
            painter.fillRect(self.rect(), overlay_color)
            pen = QPen(QColor("#55aaff"), 2) # Blue border
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

            # Draw icons
            style = self.style()
            save_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
            delete_icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)

            save_icon.paint(painter, self.save_rect)
            delete_icon.paint(painter, self.delete_rect)

            # Draw hover effect on icons
            if self.hovered_icon:
                hover_color = QColor(255, 255, 255, 70) # White with ~27% opacity
                if self.hovered_icon == 'save':
                    painter.fillRect(self.save_rect, hover_color)
                elif self.hovered_icon == 'delete':
                    painter.fillRect(self.delete_rect, hover_color)

        if self.is_saved:
            icon_size = 24
            margin = 5
            saved_rect = QRect(margin, self.height() - icon_size - margin, icon_size, icon_size)

            # Draw a background for the checkmark for better visibility
            # The circle will be slightly larger than the icon
            bg_rect = saved_rect.adjusted(-margin, -margin, margin, margin)
            path = QPainterPath()
            path.addEllipse(bg_rect)
            
            # Use a semi-transparent white for the background
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.setPen(Qt.PenStyle.NoPen) # No outline for the circle
            painter.drawPath(path)

            # Now draw the icon on top
            saved_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
            saved_icon.paint(painter, saved_rect)
