"""
TreeRefreshController -- Handles tree data refresh with expansion state preservation.

Coordinates:
- Data loading from a DataProvider
- Expansion state save/restore
- Model rebuild
"""

import logging
import time
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView

logger = logging.getLogger(__name__)


class TreeRefreshController(QObject):
    """
    Controller that refreshes tree data while preserving expansion state.

    Usage:
        controller = TreeRefreshController(model, tree_view, tree_model, data_provider)
        controller.refresh()
    """

    def __init__(self, model: QStandardItemModel, tree: QTreeView,
                 tree_model, data_provider):
        """
        Args:
            model: The QStandardItemModel.
            tree: The QTreeView widget.
            tree_model: TreeModel instance for row creation and hierarchy building.
            data_provider: Object implementing DataProvider protocol.
        """
        super().__init__()
        self.model = model
        self.tree = tree
        self.tree_model = tree_model
        self.data_provider = data_provider
        self._expanded_items: Dict = {}
        logger.debug("TreeRefreshController initialized")

    def refresh(self, root_ids: Optional[List[str]] = None,
                children_key: str = "children") -> None:
        """
        Refresh the tree view with current data, preserving expansion state.

        Args:
            root_ids: Optional list of root item IDs. None = auto-detect.
            children_key: Key in item data that holds child ID list.
        """
        start_time = time.time()
        logger.debug("Starting tree refresh")

        # Save expansion state
        self._expanded_items = {}
        for row in range(self.model.rowCount()):
            self._save_expansion_state(self.model.index(row, 0), [], self._expanded_items)

        # Close active editors
        try:
            self.tree.clearSelection()
        except Exception:
            pass

        # Rebuild tree
        self.tree_model.build_tree(self.model, self.data_provider,
                                   root_ids=root_ids, children_key=children_key)

        # Restore expansion state
        if self._expanded_items:
            for row in range(self.model.rowCount()):
                self._restore_expansion_state(self.model.index(row, 0), [], self._expanded_items)

        elapsed = time.time() - start_time
        logger.debug("Tree refresh completed in %.2fs", elapsed)

    def _save_expansion_state(self, index, path: List[str], expanded_items: Dict) -> None:
        """Recursively save expansion state using item IDs."""
        if not index.isValid():
            return

        item = self.model.itemFromIndex(index)
        if not item:
            return

        item_id = item.data(Qt.UserRole)
        current_path = path + [item_id]

        if self.tree.isExpanded(index):
            expanded_items[tuple(current_path)] = True

        for row in range(item.rowCount()):
            child_index = self.model.index(row, 0, index)
            self._save_expansion_state(child_index, current_path, expanded_items)

    def _restore_expansion_state(self, index, path: List[str], expanded_items: Dict) -> None:
        """Recursively restore expansion state using item IDs."""
        try:
            if not index.isValid():
                return

            item = self.model.itemFromIndex(index)
            if not item:
                return

            item_id = item.data(Qt.UserRole)
            if not item_id:
                return

            current_path = path + [item_id]

            if tuple(current_path) in expanded_items:
                try:
                    self.tree.expand(index)
                except Exception as e:
                    logger.warning("Could not expand item %s: %s", item_id, e)

            for row in range(item.rowCount()):
                child_index = self.model.index(row, 0, index)
                if child_index.isValid():
                    self._restore_expansion_state(child_index, current_path, expanded_items)

        except Exception as e:
            logger.error("Error in _restore_expansion_state: %s", e, exc_info=True)
