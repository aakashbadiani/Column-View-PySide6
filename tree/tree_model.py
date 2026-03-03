"""
TreeModel -- Data-agnostic model adapter for the tree view.

Handles:
- Loading data from a DataProvider into a QStandardItemModel
- Row creation with configurable column headers
- Recursive hierarchy building from parent-child relationships
- Index-to-ID and ID-to-index mapping
"""

import json
import logging
from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItem, QStandardItemModel

logger = logging.getLogger(__name__)


class TreeModel:
    """
    Data-agnostic model adapter that populates a QStandardItemModel
    from a DataProvider.

    The model assumes each item has:
    - A unique ID stored in one of the header columns (default: first column)
    - An optional 'children' key containing a list of child item IDs
    """

    def __init__(self, id_field: str = "ID"):
        """
        Args:
            id_field: The key in item data dicts that holds the unique ID.
        """
        self.id_field = id_field
        self.header_labels: List[str] = []
        self.all_items: Dict[str, Any] = {}
        logger.debug("TreeModel initialized (id_field=%s)", id_field)

    def set_headers(self, headers: List[str]) -> None:
        """Set column headers for the model."""
        self.header_labels = list(headers)

    def get_headers(self) -> List[str]:
        """Get current column headers."""
        return list(self.header_labels)

    def create_row_items(self, item_data: Dict[str, Any], context_path: Optional[str] = None) -> List[QStandardItem]:
        """
        Create a row of QStandardItem objects for an item.

        Args:
            item_data: Dictionary with item fields matching header_labels.
            context_path: Optional hierarchical path context (stored in UserRole+1).

        Returns:
            List of QStandardItem, one per header column.
        """
        items = []
        item_id = item_data.get(self.id_field, "")

        for col_index, header in enumerate(self.header_labels):
            value = ""
            if header in item_data:
                raw = item_data[header]
                if isinstance(raw, (list, dict)):
                    value = json.dumps(raw)
                elif not isinstance(raw, str):
                    value = str(raw)
                else:
                    value = raw

            item = QStandardItem(value)
            item.setData(item_id, Qt.UserRole)
            if context_path:
                item.setData(context_path, Qt.UserRole + 1)

            if col_index == 0:
                item.setEditable(False)

            items.append(item)

        return items

    def get_sibling_items(self, item_data: Dict[str, Any], context_path: Optional[str] = None) -> List[QStandardItem]:
        """
        Create sibling QStandardItems (columns 1..N) for a row.

        Args:
            item_data: Dictionary with item fields.
            context_path: Optional hierarchical path context.

        Returns:
            List of QStandardItem for columns 1 through len(headers)-1.
        """
        item_id = item_data.get(self.id_field, "")
        siblings = []

        for col_index in range(1, len(self.header_labels)):
            header = self.header_labels[col_index]
            value = ""
            if header in item_data:
                raw = item_data[header]
                if isinstance(raw, (list, dict)):
                    value = json.dumps(raw)
                elif not isinstance(raw, str):
                    value = str(raw)
                else:
                    value = raw

            item = QStandardItem(value)
            item.setData(item_id, Qt.UserRole)
            if context_path:
                item.setData(context_path, Qt.UserRole + 1)
            siblings.append(item)

        return siblings

    def clear_model(self, model: QStandardItemModel) -> None:
        """Clear model contents but preserve headers."""
        model.clear()
        model.setHorizontalHeaderLabels(self.header_labels)

    def build_tree(self, model: QStandardItemModel, data_provider,
                   root_ids: Optional[List[str]] = None,
                   children_key: str = "children") -> None:
        """
        Build the full tree hierarchy in the model from a DataProvider.

        Args:
            model: The QStandardItemModel to populate.
            data_provider: Object implementing DataProvider protocol.
            root_ids: List of top-level item IDs. If None, auto-detects roots.
            children_key: Key in item data that holds child ID list.
        """
        self.clear_model(model)
        self.all_items = data_provider.get_all_items()

        if not self.all_items:
            logger.debug("No items from data provider, tree is empty")
            return

        # Determine top-level items
        if root_ids is None:
            root_ids = self._find_root_ids(children_key)

        # Build hierarchy
        for item_id in root_ids:
            item_data = self.all_items.get(item_id)
            if not item_data:
                continue

            row_items = self.create_row_items(item_data)
            model.appendRow(row_items)

            self._add_children(row_items[0], item_id, context_path="",
                               children_key=children_key)

        logger.debug("Tree built: %d root items, %d total items",
                     len(root_ids), len(self.all_items))

    def _find_root_ids(self, children_key: str) -> List[str]:
        """Auto-detect root items (items that are not children of any other item)."""
        all_children = set()
        for item_data in self.all_items.values():
            for child_id in item_data.get(children_key, []):
                all_children.add(child_id)

        roots = [iid for iid in self.all_items if iid not in all_children]
        return sorted(roots)

    def _add_children(self, parent_item: QStandardItem, parent_id: str,
                      context_path: str, children_key: str) -> None:
        """Recursively add children to a parent item."""
        parent_data = self.all_items.get(parent_id, {})
        children = parent_data.get(children_key, [])

        if not children or not isinstance(children, list):
            return

        child_context = f"{context_path}/{parent_id}" if context_path else parent_id

        for child_id in children:
            child_data = self.all_items.get(child_id)
            if not child_data:
                continue

            row_items = self.create_row_items(child_data, context_path=child_context)
            parent_item.appendRow(row_items)

            self._add_children(row_items[0], child_id, child_context, children_key)

    # --- Qt Model Helper Methods ---

    @staticmethod
    def get_index(model: QStandardItemModel, row: int, column: int,
                  parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Return model index for given row/column under parent."""
        if not model.hasIndex(row, column, parent):
            return QModelIndex()
        return model.index(row, column, parent)

    @staticmethod
    def get_item_from_index(model: QStandardItemModel, index: QModelIndex) -> Optional[QStandardItem]:
        """Retrieve QStandardItem from a QModelIndex."""
        return model.itemFromIndex(index)

    @staticmethod
    def get_data(model: QStandardItemModel, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for an index and role."""
        if not index.isValid():
            return None
        return model.data(index, role)

    @staticmethod
    def set_data(model: QStandardItemModel, index: QModelIndex,
                 value: Any, role: int = Qt.EditRole) -> bool:
        """Set data for an index and role."""
        return model.setData(index, value, role)
