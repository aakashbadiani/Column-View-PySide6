"""
Tree Highlight Controller and Delegate.

Provides:
- HighlightDelegate: Custom QStyledItemDelegate that renders highlight backgrounds
  via a custom data role, bypassing stylesheet conflicts.
- TreeHighlightController: Manages highlighting of items by ID across the tree.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

logger = logging.getLogger(__name__)

# Custom role for highlight color (must be > Qt.UserRole)
HIGHLIGHT_ROLE = Qt.UserRole + 100

# Color presets
HIGHLIGHT_COLORS = {
    "yellow": QColor(255, 255, 150),
    "red": QColor(255, 150, 150),
    "green": QColor(150, 255, 150),
    "blue": QColor(150, 200, 255),
    "clear": None,
}


class HighlightDelegate(QStyledItemDelegate):
    """
    Custom delegate that renders highlight backgrounds using HIGHLIGHT_ROLE.

    When an item has a QColor stored at HIGHLIGHT_ROLE, this delegate
    paints that color as the background and draws text manually.
    Otherwise, falls through to default stylesheet-based painting.
    """

    def paint(self, painter, option, index) -> None:
        highlight_color = index.data(HIGHLIGHT_ROLE)

        if highlight_color and isinstance(highlight_color, QColor):
            painter.save()

            # Fill background with highlight color
            painter.fillRect(option.rect, highlight_color)

            # Draw text
            text = index.data(Qt.DisplayRole)
            if text:
                text_color = option.palette.text().color()
                painter.setPen(text_color)

                font = index.data(Qt.FontRole)
                if font:
                    painter.setFont(font)

                text_rect = option.rect.adjusted(4, 0, -4, 0)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, str(text))

            painter.restore()
        else:
            super().paint(painter, option, index)


class TreeHighlightController(QObject):
    """
    Controller for highlighting items in a QStandardItemModel-backed tree.

    Usage:
        controller = TreeHighlightController(model)
        controller.highlight_item("ITEM-001", "yellow")
        controller.clear_all()
    """

    def __init__(self, model: QStandardItemModel):
        """
        Args:
            model: The QStandardItemModel used by the tree view.
        """
        super().__init__()
        self._model = model

    @property
    def model(self) -> QStandardItemModel:
        return self._model

    @model.setter
    def model(self, value: QStandardItemModel):
        self._model = value

    def highlight_item(self, item_id: str, color: str = "yellow") -> None:
        """
        Highlight all instances of an item in the tree.

        Args:
            item_id: Item ID to highlight (matched against Qt.UserRole).
            color: Color name from HIGHLIGHT_COLORS, or "clear" to remove.
        """
        items = self._find_items_by_id(item_id)
        bg_color = HIGHLIGHT_COLORS.get(color, HIGHLIGHT_COLORS["yellow"])

        for item in items:
            if item:
                self._highlight_row(item, bg_color)

    def _highlight_row(self, item: QStandardItem, color: Optional[QColor]) -> None:
        """Highlight all columns in a row."""
        row = item.row()
        parent = item.parent() if item.parent() else self._model.invisibleRootItem()

        for col in range(self._model.columnCount()):
            col_item = parent.child(row, col)
            if col_item:
                col_item.setData(color, HIGHLIGHT_ROLE)
                if color:
                    font = col_item.font()
                    font.setBold(True)
                    col_item.setFont(font)

    def clear_all(self) -> None:
        """Clear all highlighting from the tree."""
        try:
            root = self._model.invisibleRootItem()
            if root:
                self._clear_recursive(root)
        except RuntimeError:
            logger.debug("Skipping highlight clear (model items deleted)")

    def _clear_recursive(self, item: QStandardItem) -> None:
        """Recursively clear highlights."""
        try:
            row_count = item.rowCount()
        except RuntimeError:
            return

        for row in range(row_count):
            try:
                child = item.child(row, 0)
                if child:
                    for col in range(self._model.columnCount()):
                        col_item = item.child(row, col)
                        if col_item:
                            col_item.setData(None, HIGHLIGHT_ROLE)
                            font = col_item.font()
                            font.setBold(False)
                            col_item.setFont(font)
                    self._clear_recursive(child)
            except RuntimeError:
                continue

    def _find_items_by_id(self, item_id: str) -> List[QStandardItem]:
        """Find all tree items with the given ID stored at UserRole."""
        items = []
        root = self._model.invisibleRootItem()
        self._find_recursive(root, item_id, items)
        return items

    def _find_recursive(self, item: QStandardItem, item_id: str,
                        results: List[QStandardItem]) -> None:
        try:
            row_count = item.rowCount()
        except RuntimeError:
            return

        for row in range(row_count):
            try:
                child = item.child(row, 0)
                if child:
                    if child.data(Qt.UserRole) == item_id:
                        results.append(child)
                    self._find_recursive(child, item_id, results)
            except RuntimeError:
                continue
