"""
ClawTreeViewPackage -- Data-agnostic TreeView and ColumnView widgets for PySide6.

Extracted and refactored from a production application.
All project-specific logic has been removed. These widgets accept any compatible
data table via the DataProvider protocol.

Public API:

  Tree Widgets:
    ClawTreeView           -- QTreeView with click signal and keyboard-first design
    TreeModel              -- Data-agnostic model adapter
    TreeRefreshController  -- Refresh with expansion state preservation
    TreeHighlightController-- Item highlighting by ID
    HighlightDelegate      -- Custom delegate for highlight rendering
    LevelManager           -- Expand/collapse level buttons

  Column View Widgets:
    ClawColumnView         -- QColumnView preventing editor overlay issues
    ColumnViewManager      -- Manages column view with thumbnail delegates
    ThumbnailWidget        -- Reusable thumbnail display/cycling widget
    ThumbnailColumnDelegate-- Thumbnail rendering in column view
    ThumbnailRenderService -- Cached pixmap loading service
    ThumbnailWidgetFactory -- Standardized widget creation

  Data Layer:
    DataProvider           -- Protocol for data sources
    ThumbnailProvider      -- Protocol for thumbnail sources
    DictDataProvider       -- Simple dict-backed data provider

  Paths:
    PATHS                  -- Centralized path management singleton
"""

# Tree
from .tree.tree_view import ClawTreeView
from .tree.tree_model import TreeModel
from .tree.tree_refresh import TreeRefreshController
from .tree.tree_highlight import TreeHighlightController, HighlightDelegate, HIGHLIGHT_ROLE, HIGHLIGHT_COLORS
from .tree.tree_level import LevelManager

# Column View
from .columnview.column_view import ClawColumnView
from .columnview.column_manager import ColumnViewManager
from .columnview.thumbnail_widget import ThumbnailWidget
from .columnview.thumbnail_delegate import ThumbnailColumnDelegate
from .columnview.thumbnail_renderer import ThumbnailRenderService, get_thumbnail_service
from .columnview.thumbnail_factory import ThumbnailWidgetFactory, get_thumbnail_factory

# Data
from .data_provider import DataProvider, ThumbnailProvider, DictDataProvider

# Paths
from .paths import PATHS, PackagePathManager

__all__ = [
    # Tree
    "ClawTreeView",
    "TreeModel",
    "TreeRefreshController",
    "TreeHighlightController",
    "HighlightDelegate",
    "HIGHLIGHT_ROLE",
    "HIGHLIGHT_COLORS",
    "LevelManager",
    # Column View
    "ClawColumnView",
    "ColumnViewManager",
    "ThumbnailWidget",
    "ThumbnailColumnDelegate",
    "ThumbnailRenderService",
    "get_thumbnail_service",
    "ThumbnailWidgetFactory",
    "get_thumbnail_factory",
    # Data
    "DataProvider",
    "ThumbnailProvider",
    "DictDataProvider",
    # Paths
    "PATHS",
    "PackagePathManager",
]

