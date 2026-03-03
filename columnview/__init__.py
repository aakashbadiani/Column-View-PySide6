"""
ColumnView subpackage for ClawTreeViewPackage.

Contains:
- ClawColumnView: Custom QColumnView preventing white overlay on persistent editors
- ColumnViewManager: Manages QColumnView with thumbnail delegates
- ThumbnailWidget: Reusable widget for displaying/cycling thumbnails
- ThumbnailColumnDelegate: Renders thumbnail previews in column view
- ThumbnailRenderService: Cached pixmap loading and rendering
- ThumbnailWidgetFactory: Standardized thumbnail widget creation
"""

from .column_view import ClawColumnView
from .column_manager import ColumnViewManager
from .thumbnail_widget import ThumbnailWidget
from .thumbnail_delegate import ThumbnailColumnDelegate
from .thumbnail_renderer import ThumbnailRenderService, get_thumbnail_service
from .thumbnail_factory import ThumbnailWidgetFactory, get_thumbnail_factory

__all__ = [
    "ClawColumnView",
    "ColumnViewManager",
    "ThumbnailWidget",
    "ThumbnailColumnDelegate",
    "ThumbnailRenderService",
    "get_thumbnail_service",
    "ThumbnailWidgetFactory",
    "get_thumbnail_factory",
]
