"""
ThumbnailColumnDelegate -- Custom delegate for QColumnView thumbnail rendering.

Renders:
- Unselected items: Paint thumbnail preview in paint() method
- Selected items: Interactive ThumbnailWidget via createEditor()
"""

import logging
from typing import Optional
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle

from .thumbnail_renderer import get_thumbnail_service
from .thumbnail_factory import ThumbnailWidgetFactory

logger = logging.getLogger(__name__)


class ThumbnailColumnDelegate(QStyledItemDelegate):
    """
    Custom delegate for QColumnView that displays thumbnails.

    - Unselected items: Paints thumbnail preview
    - Selected item: Shows interactive ThumbnailWidget via persistent editor
    """

    THUMBNAIL_SIZE = 100
    ITEM_WIDTH = 140
    ITEM_HEIGHT = 180
    PADDING = 10
    TEXT_HEIGHT = 60

    def __init__(self, parent=None, thumbnail_provider=None, get_display_text=None):
        """
        Args:
            parent: Parent widget (typically the column view).
            thumbnail_provider: Optional ThumbnailProvider for loading thumbnails.
            get_display_text: Optional callable(item_id, display_role_text) -> str
                for customizing the text shown below each thumbnail.
        """
        super().__init__(parent)
        self.thumbnail_service = get_thumbnail_service()
        self._thumbnail_provider = thumbnail_provider
        self._get_display_text = get_display_text
        self._thumbnail_path_cache: dict[str, Optional[Path]] = {}
        logger.debug("ThumbnailColumnDelegate initialized")

    def set_thumbnail_provider(self, provider) -> None:
        """Set the thumbnail provider."""
        self._thumbnail_provider = provider
        self._thumbnail_path_cache.clear()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Paint thumbnail preview for items."""
        item_id = index.data(Qt.UserRole)
        is_hovered = bool(option.state & QStyle.State_MouseOver)
        is_selected = bool(option.state & QStyle.State_Selected)

        parent_view = self.parent()
        if not is_selected and parent_view and hasattr(parent_view, 'selectionModel'):
            selection_model = parent_view.selectionModel()
            if selection_model and index.isValid():
                is_selected = selection_model.isSelected(index)

        has_editor = False
        if parent_view and hasattr(parent_view, 'indexWidget'):
            has_editor = parent_view.indexWidget(index) is not None

        painter.save()

        try:
            display_text = index.data(Qt.DisplayRole) or ""

            # Custom text resolver
            if self._get_display_text and item_id:
                display_text = self._get_display_text(item_id, display_text)

            self._draw_background(painter, option.rect)

            if has_editor:
                if display_text:
                    self._draw_text(painter, option.rect, display_text)
                if is_hovered or is_selected:
                    painter.fillRect(option.rect, QColor(100, 150, 255, 51))
                return

            # Paint thumbnail
            thumbnail_path = self._get_first_thumbnail(item_id) if item_id else None

            if thumbnail_path:
                pixmap = self.thumbnail_service.load_thumbnail(
                    str(thumbnail_path), self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE
                )
                if pixmap:
                    x_center = option.rect.x() + (option.rect.width() - self.THUMBNAIL_SIZE) // 2
                    thumb_rect = QRect(
                        x_center, option.rect.y() + self.PADDING,
                        self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE
                    )
                    self.thumbnail_service.render_thumbnail(pixmap, thumb_rect, painter)
                else:
                    self._draw_placeholder_rect(painter, option.rect)
            else:
                self._draw_placeholder_rect(painter, option.rect)

            if display_text:
                self._draw_text(painter, option.rect, display_text)

        except Exception as e:
            logger.error("Paint failed for index %d: %s", index.row(), e)
            self._draw_placeholder_rect(painter, option.rect)

        finally:
            if is_hovered or is_selected:
                painter.fillRect(option.rect, QColor(100, 150, 255, 51))
            painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(self.ITEM_WIDTH, self.ITEM_HEIGHT)

    def createEditor(self, parent, option: QStyleOptionViewItem, index):
        """Create interactive ThumbnailWidget for selected item."""
        try:
            item_id = index.data(Qt.UserRole)
            if not item_id:
                return None

            widget = ThumbnailWidgetFactory.create_for_column_view(parent=parent)
            widget.setFixedSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)

            if self._thumbnail_provider:
                widget.set_thumbnail_provider(self._thumbnail_provider)

            widget.set_item(item_id)
            return widget

        except Exception as e:
            logger.error("Failed to create editor for index %d: %s", index.row(), e)
            return None

    def updateEditorGeometry(self, editor, option: QStyleOptionViewItem, index):
        """Position editor to match painted thumbnail position."""
        x_center = option.rect.x() + (option.rect.width() - self.THUMBNAIL_SIZE) // 2
        y = option.rect.y() + self.PADDING
        editor.move(x_center, y)
        editor.show()
        editor.raise_()

    def _draw_background(self, painter: QPainter, rect: QRect):
        painter.fillRect(rect, self.thumbnail_service.BACKGROUND_COLOR)

    def _draw_placeholder_rect(self, painter: QPainter, rect: QRect):
        x_center = rect.x() + (rect.width() - self.THUMBNAIL_SIZE) // 2
        thumb_rect = QRect(
            x_center, rect.y() + self.PADDING,
            self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE
        )
        self.thumbnail_service.render_placeholder(thumb_rect, painter)

    def _draw_text(self, painter: QPainter, rect: QRect, text: str):
        text_y = rect.y() + self.PADDING + self.THUMBNAIL_SIZE + self.PADDING
        text_rect = QRect(
            rect.x() + self.PADDING, text_y,
            rect.width() - 2 * self.PADDING, self.TEXT_HEIGHT
        )
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, text)

    def _get_first_thumbnail(self, item_id: str) -> Optional[Path]:
        """Get first thumbnail for an item, using cache."""
        if item_id in self._thumbnail_path_cache:
            return self._thumbnail_path_cache[item_id]

        if not self._thumbnail_provider:
            self._thumbnail_path_cache[item_id] = None
            return None

        try:
            thumbnails = self._thumbnail_provider.get_thumbnails(item_id)
            if thumbnails:
                first = thumbnails[0]
                self._thumbnail_path_cache[item_id] = first
                return first
        except Exception as e:
            logger.error("Failed to get thumbnail for %s: %s", item_id, e)

        self._thumbnail_path_cache[item_id] = None
        return None

    def clear_cache(self):
        """Clear thumbnail path cache and service cache."""
        self._thumbnail_path_cache.clear()
        self.thumbnail_service.clear_cache()
