"""
ColumnViewManager -- Manages QColumnView with thumbnail delegates.

Features:
- Thumbnail display for hierarchical items
- Persistent editor management (ThumbnailWidget on selection only)
- Selection chain support for path navigation
- Tree view synchronization
- Context menu support
"""

import logging
from typing import Optional, Set

from PySide6.QtCore import Qt, QModelIndex, Signal, QPersistentModelIndex, QObject, QEvent, QPoint
from PySide6.QtWidgets import QWidget, QAbstractItemView

from .thumbnail_delegate import ThumbnailColumnDelegate
from .column_view import ClawColumnView

logger = logging.getLogger(__name__)


class ColumnViewManager(QObject):
    """
    Manages QColumnView for displaying hierarchical data with thumbnails.

    Editors (ThumbnailWidget) are ONLY created for selected items, not on hover.

    Signals:
        item_selected(QModelIndex): Emitted when an item is selected.
        context_menu_requested(QPoint, QModelIndex): Emitted for context menus.
    """

    item_selected = Signal(QModelIndex)
    context_menu_requested = Signal(QPoint, QModelIndex)

    def __init__(self, parent: Optional[QWidget] = None, model=None,
                 tree_view=None, thumbnail_provider=None, get_display_text=None):
        """
        Args:
            parent: Parent widget.
            model: QAbstractItemModel to use.
            tree_view: Optional QTreeView for selection synchronization.
            thumbnail_provider: Optional ThumbnailProvider for thumbnails.
            get_display_text: Optional callable(item_id, display_text) -> str.
        """
        super().__init__()

        self.tree_view = tree_view

        self.column_view = ClawColumnView(parent)

        self.delegate = ThumbnailColumnDelegate(
            self.column_view,
            thumbnail_provider=thumbnail_provider,
            get_display_text=get_display_text,
        )
        self.column_view.setItemDelegate(self.delegate)

        if model:
            self.column_view.setModel(model)

        self.column_view.setResizeGripsVisible(False)
        self.column_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.column_view.setMouseTracking(True)
        if self.column_view.viewport():
            self.column_view.viewport().setMouseTracking(True)

        self.hover_index = None
        self.open_editors: Set[QPersistentModelIndex] = set()

        self.column_view.clicked.connect(self._on_item_clicked)
        self.column_view.entered.connect(self._on_item_hovered)

        selection_model = self.column_view.selectionModel()
        if selection_model:
            selection_model.currentChanged.connect(self._on_selection_changed)

        viewport = self.column_view.viewport()
        if viewport:
            viewport.installEventFilter(self)

        for sb in (self.column_view.horizontalScrollBar(), self.column_view.verticalScrollBar()):
            if sb:
                sb.valueChanged.connect(self._on_scroll)

        self.column_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.column_view.customContextMenuRequested.connect(self._on_context_menu)

        logger.debug("ColumnViewManager initialized")

    def get_widget(self) -> ClawColumnView:
        """Get the column view widget for embedding in a layout."""
        return self.column_view

    def set_thumbnail_provider(self, provider) -> None:
        """Set the thumbnail provider on both manager and delegate."""
        self.delegate.set_thumbnail_provider(provider)

    def _close_editor(self, index: QModelIndex):
        if not index.isValid():
            return
        persistent = QPersistentModelIndex(index)
        self.column_view.unregister_editor(index)
        self.column_view.closePersistentEditor(index)
        self.open_editors.discard(persistent)
        rect = self.column_view.visualRect(index)
        self.column_view.viewport().update(rect)

    def _open_editor(self, index: QModelIndex):
        if not index.isValid():
            return
        persistent = QPersistentModelIndex(index)
        if not self.column_view.isPersistentEditorOpen(index):
            self.column_view.openPersistentEditor(index)
            self.column_view.register_editor(index)
            self.open_editors.add(persistent)
            editor = self.column_view.indexWidget(index)
            if editor:
                editor.raise_()
            rect = self.column_view.visualRect(index)
            self.column_view.viewport().update(rect)

    def _on_scroll(self, value):
        self.hover_index = None

    def _on_context_menu(self, position: QPoint):
        index = self.column_view.indexAt(position)
        if index.isValid():
            sel = self.column_view.selectionModel()
            if sel and sel.currentIndex() != index:
                from PySide6.QtCore import QItemSelectionModel
                sel.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
            global_pos = self.column_view.viewport().mapToGlobal(position)
            self.context_menu_requested.emit(global_pos, index)

    def _on_item_clicked(self, index: QModelIndex):
        pass  # Selection handled by _on_selection_changed

    def _on_item_hovered(self, index: QModelIndex):
        if not index.isValid():
            self.hover_index = None
            return
        if self.hover_index != index:
            self.hover_index = index

    def _on_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        sel = self.column_view.selectionModel()
        if not sel:
            return

        # Close previous editor if in same column
        if previous.isValid() and current.isValid() and previous.parent() == current.parent():
            self._close_editor(previous)

        selected_indexes = sel.selectedIndexes()
        selected_persistent = {QPersistentModelIndex(idx) for idx in selected_indexes if idx.isValid()}

        # Close editors not in selection
        for persistent_idx in list(self.open_editors):
            if persistent_idx not in selected_persistent:
                if persistent_idx.isValid():
                    self._close_editor(QModelIndex(persistent_idx))

        # Open editor for current item only
        if current.isValid():
            self._open_editor(current)

        if current.isValid():
            self._sync_selection_to_tree(current)
            self.item_selected.emit(current)

    def _sync_selection_to_tree(self, index: QModelIndex):
        """Sync column view selection to tree view."""
        if not self.tree_view or not index.isValid():
            return
        try:
            tree_sel = self.tree_view.selectionModel()
            if tree_sel:
                from PySide6.QtCore import QItemSelectionModel
                tree_sel.setCurrentIndex(
                    index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
                )
        except Exception as e:
            logger.error("Failed to sync selection to tree: %s", e)

    def refresh_view(self):
        """Refresh the column view display."""
        try:
            for persistent_idx in list(self.open_editors):
                if persistent_idx.isValid():
                    self._close_editor(QModelIndex(persistent_idx))
            self.delegate.clear_cache()
            self.column_view.reset()
        except Exception as e:
            logger.error("Failed to refresh column view: %s", e)

    def set_root_index(self, index: QModelIndex):
        """Set root index for the column view."""
        self.column_view.setRootIndex(index)

    def get_selected_item_id(self) -> Optional[str]:
        """Get the currently selected item's ID."""
        sel = self.column_view.selectionModel()
        if not sel:
            return None
        current = sel.currentIndex()
        if not current.isValid():
            return None
        return current.data(Qt.UserRole)

    def navigate_to_item(self, item_id: str) -> bool:
        """Navigate column view to show a specific item."""
        model = self.column_view.model()
        if not model:
            return False

        root = model.invisibleRootItem() if hasattr(model, 'invisibleRootItem') else None
        index = self._find_item_index(item_id, root)

        if index and index.isValid():
            sel = self.column_view.selectionModel()
            if sel:
                from PySide6.QtCore import QItemSelectionModel
                sel.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                return True
        return False

    def _find_item_index(self, item_id: str, root_item) -> Optional[QModelIndex]:
        if not root_item:
            return None
        model = self.column_view.model()
        if not model:
            return None

        def search(parent_item):
            for row in range(parent_item.rowCount()):
                child = parent_item.child(row, 0)
                if child:
                    if child.data(Qt.UserRole) == item_id:
                        return model.indexFromItem(child)
                    result = search(child)
                    if result:
                        return result
            return None

        return search(root_item)

    def select_index(self, index: QModelIndex):
        """Select an index in the column view."""
        if not index.isValid():
            return
        sel = self.column_view.selectionModel()
        if sel:
            from PySide6.QtCore import QItemSelectionModel
            sel.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def restore_selection_path(self, path_list: list) -> bool:
        """
        Restore column view to show a specific selection path.

        Args:
            path_list: List of item IDs from root to target.

        Returns:
            True if restoration succeeded.
        """
        if not path_list:
            return False

        model = self.column_view.model()
        if not model:
            return False

        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QItemSelectionModel

            sel = self.column_view.selectionModel()
            if not sel:
                return False

            root = model.invisibleRootItem() if hasattr(model, 'invisibleRootItem') else None
            if not root:
                return False

            current_parent = root
            last_valid = None
            path_indexes = []

            sel.clearSelection()

            for item_id in path_list:
                found = None
                for row in range(current_parent.rowCount()):
                    child = current_parent.child(row, 0)
                    if child and child.data(Qt.UserRole) == item_id:
                        found = model.indexFromItem(child)
                        current_parent = child
                        break

                if found and found.isValid():
                    path_indexes.append(found)
                    sel.setCurrentIndex(found, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                    last_valid = found
                    QApplication.processEvents()
                else:
                    break

            for idx in path_indexes:
                if idx.isValid():
                    sel.select(idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)

            return last_valid is not None

        except Exception as e:
            logger.error("Failed to restore selection path: %s", e, exc_info=True)
            return False
