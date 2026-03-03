"""
ClawColumnView -- Custom QColumnView that prevents white overlay on persistent editors.

Features:
- Prevents selection background from obscuring editor widgets
- Maintains selection when clicking on empty space
- Event filter on child QListView viewports
- Efficient editor geometry tracking
"""

import logging

from PySide6.QtWidgets import QColumnView, QStyleOptionViewItem, QStyle, QApplication, QListView
from PySide6.QtCore import QModelIndex, Qt, QRect, QItemSelectionModel, QEvent
from PySide6.QtGui import QPainter, QMouseEvent

logger = logging.getLogger(__name__)


class ClawColumnView(QColumnView):
    """
    Custom QColumnView that prevents white selection overlay on persistent editors.

    Also preserves selection when clicking empty space (no item),
    and tracks editor geometries for efficient updates.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._editor_indexes = []
        self._filtered_viewports = set()
        self._viewport_to_listview = {}
        self._column_selections = {}

        if self.viewport():
            self.viewport().installEventFilter(self)
            self._filtered_viewports.add(self.viewport())

        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        logger.debug("ClawColumnView initialized")

    def _install_filters_on_child_listviews(self):
        """Find child QListViews and install event filters on their viewports."""
        for listview in self.findChildren(QListView):
            viewport = listview.viewport()
            if viewport and viewport not in self._filtered_viewports:
                viewport.installEventFilter(self)
                self._filtered_viewports.add(viewport)
                self._viewport_to_listview[viewport] = listview

    def showEvent(self, event):
        super().showEvent(event)
        self._install_filters_on_child_listviews()

    def mousePressEvent(self, event: QMouseEvent):
        """Prevent selection clearing on empty space click."""
        index = self.indexAt(event.pos())
        if not index.isValid():
            event.accept()
            return
        super().mousePressEvent(event)

    def eventFilter(self, obj, event: QEvent):
        """Event filter for child QListView viewports."""
        if event.type() != QEvent.MouseButtonPress:
            return super().eventFilter(obj, event)

        parent = obj.parent()
        if not isinstance(parent, QListView):
            return super().eventFilter(obj, event)

        our_listviews = self.findChildren(QListView)
        if parent not in our_listviews:
            return super().eventFilter(obj, event)

        listview = parent

        if obj not in self._filtered_viewports:
            self._filtered_viewports.add(obj)
            self._viewport_to_listview[obj] = listview

        index = listview.indexAt(event.pos())

        if index.isValid():
            self._column_selections[listview] = index
        else:
            saved_index = self._column_selections.get(listview)
            if saved_index and saved_index.isValid():
                listview.setCurrentIndex(saved_index)
            return True

        return super().eventFilter(obj, event)

    def setSelection(self, rect: QRect, flags: QItemSelectionModel.SelectionFlags):
        """Override to prevent clearing selection on empty space."""
        points = [rect.center(), rect.topLeft(), rect.topRight(),
                  rect.bottomLeft(), rect.bottomRight()]

        has_valid = any(self.indexAt(p).isValid() for p in points)
        if not has_valid:
            return

        super().setSelection(rect, flags)

    def drawRow(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Skip drawing for items with persistent editors."""
        if self.indexWidget(index) is not None:
            return
        super().drawRow(painter, option, index)

    def register_editor(self, index: QModelIndex):
        """Register an editor index for tracking."""
        if index.isValid() and index not in self._editor_indexes:
            self._editor_indexes.append(index)

    def unregister_editor(self, index: QModelIndex):
        """Unregister an editor index."""
        if index in self._editor_indexes:
            self._editor_indexes.remove(index)

    def _update_editor_geometries(self):
        """Update geometry for all tracked editors."""
        delegate = self.itemDelegate()
        if not delegate:
            return

        self._editor_indexes = [idx for idx in self._editor_indexes if idx.isValid()]

        for index in self._editor_indexes:
            editor = self.indexWidget(index)
            if editor:
                rect = self.visualRect(index)
                if not rect.isNull() and rect.isValid() and self.viewport().rect().intersects(rect):
                    if not editor.isVisible():
                        editor.show()
                    option = QStyleOptionViewItem()
                    option.rect = rect
                    option.state = QStyle.State_Enabled
                    delegate.updateEditorGeometry(editor, option, index)
                    editor.raise_()
                else:
                    if editor.isVisible():
                        editor.hide()

    def paintEvent(self, event):
        super().paintEvent(event)

        for listview in self.findChildren(QListView):
            viewport = listview.viewport()
            if viewport and viewport not in self._filtered_viewports:
                viewport.installEventFilter(self)
                self._filtered_viewports.add(viewport)
                self._viewport_to_listview[viewport] = listview

        self._update_editor_geometries()
