"""
ThumbnailWidget -- Reusable widget for displaying and managing thumbnails.

Features:
- Display current thumbnail with caching
- Cycle through multiple thumbnails with left-click
- Expand thumbnail with Ctrl+left-click
- Paste from clipboard with right-click context menu
- Placeholder text when no thumbnail exists
- Dynamic sizing with configurable constraints
"""

import logging
from typing import Optional, List, TYPE_CHECKING
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu, QApplication, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter

from .thumbnail_renderer import get_thumbnail_service

if TYPE_CHECKING:
    from ..data_provider import ThumbnailProvider

logger = logging.getLogger(__name__)


class ThumbnailWidget(QWidget):
    """
    Reusable thumbnail widget for displaying item thumbnails.

    Signals:
        thumbnail_clicked: Emitted on normal left-click.
        thumbnail_expand_requested(str): Emitted on Ctrl+click with item_id.
        thumbnail_updated: Emitted when thumbnail changes (paste, delete).
        thumbnail_index_changed(str, int): Emitted when index changes (item_id, index).
    """

    thumbnail_clicked = Signal()
    thumbnail_expand_requested = Signal(str)
    thumbnail_updated = Signal()
    thumbnail_index_changed = Signal(str, int)

    DEFAULT_MIN_SIZE = 100
    DEFAULT_PREFERRED_SIZE = 150

    def __init__(self, parent=None, min_width=None, min_height=None, transparent=False):
        """
        Args:
            parent: Parent widget.
            min_width: Minimum width (default 100px).
            min_height: Minimum height (default 100px).
            transparent: If True, widget background is transparent.
        """
        super().__init__(parent)

        self.thumbnail_service = get_thumbnail_service()
        self._thumbnail_provider: Optional['ThumbnailProvider'] = None

        self.item_id = None
        self.current_index = 0
        self.thumbnails: List[Path] = []
        self.custom_placeholder_text = None
        self.transparent = transparent

        self.min_width = min_width or self.DEFAULT_MIN_SIZE
        self.min_height = min_height or self.DEFAULT_MIN_SIZE

        self._init_ui()

    def set_thumbnail_provider(self, provider: 'ThumbnailProvider') -> None:
        """
        Set the thumbnail data provider.

        Args:
            provider: Object implementing ThumbnailProvider protocol.
        """
        self._thumbnail_provider = provider

    def _init_ui(self):
        bg_style = "background-color: #f0f0f0;"
        if self.transparent:
            bg_style = "background-color: transparent;"

        self.setStyleSheet(f"ThumbnailWidget {{ {bg_style} }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumbnail_label.setMinimumSize(self.min_width, self.min_height)
        self.thumbnail_label.setScaledContents(False)
        self.thumbnail_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.thumbnail_label.setStyleSheet(
            "QLabel { border: none; background-color: #f0f0f0; margin: 0px; padding: 0px; }"
        )
        self.thumbnail_label.setText("No thumbnail\n\nRight-click to paste image")
        self.thumbnail_label.setWordWrap(True)
        self.thumbnail_label.setToolTip(
            "Left-click: Cycle thumbnails\n"
            "Ctrl+Left-click: Expand view\n"
            "Right-click: Paste from clipboard"
        )
        self.thumbnail_label.setMouseTracking(True)
        self.thumbnail_label.mousePressEvent = self._label_mouse_press_event

        layout.addWidget(self.thumbnail_label, stretch=1)

        self.thumbnail_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thumbnail_label.customContextMenuRequested.connect(self._show_context_menu)

    def set_item(self, item_id: str):
        """
        Set the item ID and load thumbnails.

        Args:
            item_id: Unique identifier for the item.
        """
        if not item_id:
            self.item_id = None
            self.thumbnails = []
            self.current_index = 0
            self._show_placeholder()
            return

        self.item_id = item_id
        self.current_index = 0
        self.load_thumbnails()

    # Alias for backward compatibility
    set_part = set_item

    def load_thumbnails(self):
        """Load thumbnails for the current item from the thumbnail provider."""
        if not self.item_id or not self._thumbnail_provider:
            self.thumbnails = []
            self._show_placeholder()
            return

        try:
            self.thumbnails = self._thumbnail_provider.get_thumbnails(self.item_id)

            if self.thumbnails:
                if self.current_index >= len(self.thumbnails):
                    self.current_index = len(self.thumbnails) - 1
                elif self.current_index < 0:
                    self.current_index = 0
                self._display_current_thumbnail()
            else:
                self.current_index = 0
                self._show_placeholder()

        except Exception as e:
            logger.error("Failed to load thumbnails for %s: %s", self.item_id, e, exc_info=True)
            self.thumbnails = []
            self._show_placeholder()

    def _display_current_thumbnail(self):
        """Display the current thumbnail using the shared rendering service."""
        if not self.thumbnails or self.current_index >= len(self.thumbnails):
            self._show_placeholder()
            return

        if self.current_index < 0:
            self.current_index = 0
            if not self.thumbnails:
                self._show_placeholder()
                return

        try:
            thumbnail_path = self.thumbnails[self.current_index]
            if not thumbnail_path.exists():
                self.load_thumbnails()
                return

            w = self.width() if self.width() > 0 else self.DEFAULT_PREFERRED_SIZE
            h = self.height() if self.height() > 0 else self.DEFAULT_PREFERRED_SIZE

            pixmap = self.thumbnail_service.load_thumbnail(str(thumbnail_path), w, h)

            if pixmap:
                label_w = self.thumbnail_label.width() if self.thumbnail_label.width() > 0 else w
                label_h = self.thumbnail_label.height() if self.thumbnail_label.height() > 0 else h

                centered = QPixmap(label_w, label_h)
                centered.fill(Qt.transparent)

                painter = QPainter(centered)
                x = (label_w - pixmap.width()) // 2
                y = (label_h - pixmap.height()) // 2
                painter.drawPixmap(x, y, pixmap)
                painter.end()

                self.thumbnail_label.setPixmap(centered)
            else:
                self._show_placeholder()
                return

            count = len(self.thumbnails)
            self.thumbnail_label.setToolTip(
                f"Thumbnail {self.current_index + 1} of {count}\n"
                f"Left-click: {'Next thumbnail' if count > 1 else 'No other thumbnails'}\n"
                f"Ctrl+Left-click: Expand view\n"
                f"Right-click: Paste new thumbnail"
            )

        except Exception as e:
            logger.error("Failed to display thumbnail: %s", e, exc_info=True)
            self._show_placeholder()

    def _show_placeholder(self):
        """Show placeholder when no thumbnail is available."""
        self.thumbnail_label.clear()
        text = self.custom_placeholder_text or "No thumbnail\n\nRight-click to paste image"
        self.thumbnail_label.setText(text)
        self.thumbnail_label.setToolTip("Right-click to paste image from clipboard")

    def _cycle_thumbnail(self):
        """Cycle to the next thumbnail."""
        if not self.thumbnails:
            return
        self.current_index = (self.current_index + 1) % len(self.thumbnails)
        self._display_current_thumbnail()
        if self.item_id:
            self.thumbnail_index_changed.emit(self.item_id, self.current_index)

    def _label_mouse_press_event(self, event):
        """Handle mouse press on the label."""
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                if self.item_id and self.thumbnails:
                    self.thumbnail_expand_requested.emit(self.item_id)
            else:
                if len(self.thumbnails) > 1:
                    self._cycle_thumbnail()
                self.thumbnail_clicked.emit()

    def mousePressEvent(self, event):
        self._label_mouse_press_event(event)
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.thumbnails:
            self._display_current_thumbnail()

    def _show_context_menu(self, position):
        """Show context menu on right-click."""
        menu = QMenu(self)

        paste_action = menu.addAction("Paste Thumbnail")
        paste_action.triggered.connect(self._paste_from_clipboard)

        if self.thumbnails and self.item_id and self.current_index > 0:
            make_primary = menu.addAction("Make Primary")
            make_primary.triggered.connect(self._make_primary_thumbnail)

        if self.thumbnails and self.item_id:
            delete_action = menu.addAction("Delete Current Thumbnail")
            delete_action.triggered.connect(self._delete_current_thumbnail)

        menu.exec(self.thumbnail_label.mapToGlobal(position))

    def _paste_from_clipboard(self):
        """Paste image from clipboard and save as thumbnail."""
        if not self.item_id or not self._thumbnail_provider:
            return

        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            # Check for file URLs first
            if mime_data and mime_data.hasUrls():
                urls = mime_data.urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    if file_path:
                        from pathlib import Path as P
                        path_obj = P(file_path)
                        if path_obj.exists() and path_obj.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                            image_data = path_obj.read_bytes()
                            ext = path_obj.suffix.lstrip('.')
                            saved = self._thumbnail_provider.save_thumbnail(self.item_id, image_data, ext)
                            if saved:
                                self.load_thumbnails()
                                if self.thumbnails:
                                    self.current_index = len(self.thumbnails) - 1
                                    self._display_current_thumbnail()
                                self.thumbnail_updated.emit()
                            return

            # Fall back to clipboard image data
            image = clipboard.image()
            if image.isNull():
                return

            from PySide6.QtCore import QBuffer, QIODevice, QByteArray
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            buffer.close()

            saved = self._thumbnail_provider.save_thumbnail(self.item_id, byte_array.data(), "png")
            if saved:
                self.load_thumbnails()
                if self.thumbnails:
                    self.current_index = len(self.thumbnails) - 1
                    self._display_current_thumbnail()
                self.thumbnail_updated.emit()

        except Exception as e:
            logger.error("Failed to paste thumbnail: %s", e, exc_info=True)

    def _delete_current_thumbnail(self):
        """Delete the currently displayed thumbnail."""
        if not self.thumbnails or self.current_index >= len(self.thumbnails):
            return
        if not self._thumbnail_provider:
            return

        try:
            thumbnail_path = self.thumbnails[self.current_index]
            success = self._thumbnail_provider.delete_thumbnail(self.item_id, thumbnail_path)
            if success:
                self.load_thumbnails()
                if self.current_index >= len(self.thumbnails) and self.current_index > 0:
                    self.current_index = len(self.thumbnails) - 1
                if self.thumbnails:
                    self._display_current_thumbnail()
                else:
                    self._show_placeholder()
                self.thumbnail_updated.emit()
        except Exception as e:
            logger.error("Failed to delete thumbnail: %s", e, exc_info=True)

    def _make_primary_thumbnail(self):
        """Make the current thumbnail the primary (first) thumbnail."""
        if not self.thumbnails or self.current_index >= len(self.thumbnails):
            return
        if not self._thumbnail_provider or self.current_index == 0:
            return

        try:
            thumbnail_path = self.thumbnails[self.current_index]
            success = self._thumbnail_provider.set_primary_thumbnail(self.item_id, thumbnail_path)
            if success:
                self.load_thumbnails()
                self.current_index = 0
                self._display_current_thumbnail()
                self.thumbnail_updated.emit()
                self.thumbnail_index_changed.emit(self.item_id, 0)
        except Exception as e:
            logger.error("Failed to set primary thumbnail: %s", e, exc_info=True)

    def refresh(self):
        """Refresh the thumbnail display."""
        self.load_thumbnails()
        if self.thumbnails:
            self._display_current_thumbnail()
        else:
            self._show_placeholder()

    def set_placeholder_text(self, text: str):
        """Set custom placeholder text."""
        self.custom_placeholder_text = text
        if not self.thumbnails:
            self._show_placeholder()

    def set_thumbnail_index(self, index: int):
        """Set the thumbnail index (for synchronization)."""
        if not self.thumbnails or index < 0 or index >= len(self.thumbnails):
            return
        if self.current_index != index:
            self.current_index = index
            self._display_current_thumbnail()
