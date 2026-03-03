"""
Tree subpackage for ClawTreeViewPackage.

Contains:
- ClawTreeView: Custom QTreeView widget with signals and keyboard-first design
- TreeModel: Data-agnostic model adapter for loading hierarchical data
- TreeHighlightController / HighlightDelegate: Row highlighting system
- LevelManager: Expand/collapse level controls with positive and negative buttons
- TreeRefreshController: Handles tree refresh with expansion state preservation
"""

from .tree_view import ClawTreeView
from .tree_model import TreeModel
from .tree_highlight import TreeHighlightController, HighlightDelegate, HIGHLIGHT_ROLE, HIGHLIGHT_COLORS
from .tree_level import LevelManager
from .tree_refresh import TreeRefreshController

__all__ = [
    "ClawTreeView",
    "TreeModel",
    "TreeHighlightController",
    "HighlightDelegate",
    "HIGHLIGHT_ROLE",
    "HIGHLIGHT_COLORS",
    "LevelManager",
    "TreeRefreshController",
]
