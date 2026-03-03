"""
ThumbnailWidgetFactory -- Centralized factory for creating ThumbnailWidget instances.

Standard sizes:
- MAIN_VIEW: 120x120
- DIALOG: 112x112
- COLUMN_VIEW: 100x100
- LARGE: 200x200
"""

import logging
from typing import Optional

from PySide6.QtWidgets import QWidget
from .thumbnail_widget import ThumbnailWidget

logger = logging.getLogger(__name__)


class ThumbnailWidgetFactory:
    """Factory for creating ThumbnailWidget with standardized sizing."""

    MAIN_VIEW_WIDTH = 120
    MAIN_VIEW_HEIGHT = 120

    DIALOG_WIDTH = 112
    DIALOG_HEIGHT = 112

    LARGE_WIDTH = 200
    LARGE_HEIGHT = 200

    COLUMN_VIEW_WIDTH = 100
    COLUMN_VIEW_HEIGHT = 100

    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100

    @classmethod
    def create_for_main_view(cls, parent: Optional[QWidget] = None) -> ThumbnailWidget:
        """Create thumbnail widget sized for main view (120x120)."""
        return ThumbnailWidget(parent=parent, min_width=cls.MAIN_VIEW_WIDTH, min_height=cls.MAIN_VIEW_HEIGHT)

    @classmethod
    def create_for_dialog(cls, parent: Optional[QWidget] = None) -> ThumbnailWidget:
        """Create thumbnail widget sized for dialogs (112x112)."""
        return ThumbnailWidget(parent=parent, min_width=cls.DIALOG_WIDTH, min_height=cls.DIALOG_HEIGHT)

    @classmethod
    def create_for_large(cls, parent: Optional[QWidget] = None) -> ThumbnailWidget:
        """Create thumbnail widget at large size (200x200)."""
        return ThumbnailWidget(parent=parent, min_width=cls.LARGE_WIDTH, min_height=cls.LARGE_HEIGHT)

    @classmethod
    def create_for_column_view(cls, parent: Optional[QWidget] = None) -> ThumbnailWidget:
        """Create thumbnail widget sized for column view delegate (100x100)."""
        return ThumbnailWidget(parent=parent, min_width=cls.COLUMN_VIEW_WIDTH, min_height=cls.COLUMN_VIEW_HEIGHT)

    @classmethod
    def create_custom(cls, parent: Optional[QWidget] = None,
                      min_width: Optional[int] = None,
                      min_height: Optional[int] = None) -> ThumbnailWidget:
        """Create thumbnail widget with custom sizing."""
        return ThumbnailWidget(parent=parent, min_width=min_width, min_height=min_height)


_factory_instance: Optional[ThumbnailWidgetFactory] = None


def get_thumbnail_factory() -> ThumbnailWidgetFactory:
    """Get the singleton thumbnail widget factory."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ThumbnailWidgetFactory()
    return _factory_instance
