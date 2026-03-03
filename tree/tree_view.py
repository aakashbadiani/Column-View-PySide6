"""
ClawTreeView -- Data-agnostic QTreeView widget.

Extends QTreeView with:
- Item click signal (emits QModelIndex)
- Alternating row colors
- Context menu support
- All-columns focus
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QModelIndex, Signal
from PySide6.QtWidgets import QTreeView, QHeaderView

logger = logging.getLogger(__name__)


class ClawTreeView(QTreeView):
    """
    Custom QTreeView widget for displaying hierarchical data.

    Signals:
        itemClicked(QModelIndex): Emitted when an item is clicked.
    """

    itemClicked = Signal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAllColumnsShowFocus(True)
        self.setSelectionBehavior(QTreeView.SelectRows)
        logger.debug("ClawTreeView initialized")

    def mousePressEvent(self, event):
        """Emit itemClicked on valid click, then delegate to default."""
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            self.itemClicked.emit(index)
        super().mousePressEvent(event)

    def configure_header(self, resize_mode: QHeaderView.ResizeMode = QHeaderView.ResizeToContents):
        """
        Configure header resize behavior.

        Args:
            resize_mode: How columns should resize. Default is ResizeToContents.
        """
        header = self.header()
        if header:
            header.setSectionResizeMode(resize_mode)
