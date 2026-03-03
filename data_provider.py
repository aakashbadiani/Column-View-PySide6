"""
Data Provider Protocol for ClawTreeViewPackage.

Defines the interface that consumers must implement to feed data
into the TreeView and ColumnView widgets. This decouples the widgets
from any specific backend or data source.
"""

from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class DataProvider(Protocol):
    """
    Protocol defining how data is supplied to the tree/column widgets.

    Implement this protocol to connect any data source to the widgets.
    Only get_all_items() and get_item() are required. All other methods
    have sensible defaults if not implemented.
    """

    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        """
        Return all items as a flat dictionary.

        Returns:
            Dict mapping item_id -> item_data dict.
            Each item_data must contain at minimum:
                - An ID field (key name configured via headers)
                - 'children': List[str] of child item IDs (optional)
        """
        ...

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Return data for a single item.

        Args:
            item_id: The unique identifier for the item.

        Returns:
            Item data dictionary, or None if not found.
        """
        ...


@runtime_checkable
class ThumbnailProvider(Protocol):
    """
    Optional protocol for supplying thumbnails to the ColumnView.

    Implement this if you want thumbnail display in the column view.
    If not provided, column view renders without thumbnails.
    """

    def get_thumbnails(self, item_id: str) -> List[Path]:
        """
        Return list of thumbnail file paths for an item.

        Args:
            item_id: The unique identifier for the item.

        Returns:
            List of Path objects pointing to thumbnail images.
            First item is considered the "primary" thumbnail.
        """
        ...

    def save_thumbnail(self, item_id: str, image_data: bytes, extension: str = "png") -> Optional[Path]:
        """
        Save thumbnail image data for an item.

        Args:
            item_id: The unique identifier.
            image_data: Raw image bytes (PNG, JPG, etc.)
            extension: File extension without dot.

        Returns:
            Path to the saved thumbnail, or None on failure.
        """
        ...

    def delete_thumbnail(self, item_id: str, thumbnail_path: Path) -> bool:
        """
        Delete a specific thumbnail.

        Args:
            item_id: The unique identifier.
            thumbnail_path: Path to the thumbnail to delete.

        Returns:
            True if successful.
        """
        ...

    def set_primary_thumbnail(self, item_id: str, thumbnail_path: Path) -> bool:
        """
        Set a thumbnail as the primary (first) thumbnail.

        Args:
            item_id: The unique identifier.
            thumbnail_path: Path to the thumbnail to promote.

        Returns:
            True if successful.
        """
        ...


class DictDataProvider:
    """
    Simple data provider backed by a Python dictionary.

    Use this for quick prototyping or when your data is already
    in a dict-of-dicts format.
    """

    def __init__(self, data: Optional[Dict[str, Dict[str, Any]]] = None):
        self._data: Dict[str, Dict[str, Any]] = data or {}

    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        return self._data

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(item_id)

    def set_data(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Replace the entire dataset."""
        self._data = data

    def add_item(self, item_id: str, item_data: Dict[str, Any]) -> None:
        """Add or update a single item."""
        self._data[item_id] = item_data

    def remove_item(self, item_id: str) -> bool:
        """Remove an item. Returns True if it existed."""
        if item_id in self._data:
            del self._data[item_id]
            return True
        return False
