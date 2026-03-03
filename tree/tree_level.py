"""
LevelManager -- Tree expansion/collapse level controls.

Provides both positive (expand to level N) and negative (collapse N levels
from the bottom of each branch) operations, with button UI controls.
"""

import logging

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QStandardItemModel

logger = logging.getLogger(__name__)


class LevelManager(QObject):
    """
    Manages tree level expansion and collapse with button controls.

    Provides two button groups:
    - Positive buttons (1..max_level): Expand tree to that level
    - Negative buttons (-1..-(max-1)): Collapse N levels from leaf nodes

    Signals:
        level_changed(int): Emitted when expansion level changes.
            Positive values = expand-to-level. Negative = collapse-from-bottom.
    """

    level_changed = Signal(int)

    # Default button styling
    POSITIVE_ACTIVE_STYLE = """
        QPushButton {
            background-color: #99ccff;
            color: black;
            border: 1px solid #999;
            padding: 3px;
            border-radius: 2px;
            font-weight: bold;
            font-size: 11px;
        }
    """
    POSITIVE_INACTIVE_STYLE = """
        QPushButton {
            background-color: #ccffcc;
            color: black;
            border: 1px solid #999;
            padding: 3px;
            border-radius: 2px;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #99ff99;
        }
    """
    NEGATIVE_ACTIVE_STYLE = """
        QPushButton {
            background-color: #ffcc99;
            color: black;
            border: 1px solid #999;
            padding: 3px;
            border-radius: 2px;
            font-weight: bold;
            font-size: 11px;
        }
    """
    NEGATIVE_INACTIVE_STYLE = """
        QPushButton {
            background-color: #ccffcc;
            color: black;
            border: 1px solid #999;
            padding: 3px;
            border-radius: 2px;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #99ff99;
        }
    """

    def __init__(self, tree, model: QStandardItemModel, parent=None):
        """
        Args:
            tree: QTreeView instance.
            model: QStandardItemModel instance.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self.tree = tree
        self.model = model

        self.positive_buttons = []
        self.negative_buttons = []

        self.positive_layout = None
        self.negative_layout = None

        self.current_positive_level = -1
        self.current_negative_level = 0
        self.is_updating = False

        self._max_buttons = 10
        logger.debug("LevelManager initialized")

    def create_level_controls(self) -> QHBoxLayout:
        """
        Create the level control widget layout with positive and negative buttons.

        Returns:
            QHBoxLayout containing both button groups with a separator.
        """
        container = QHBoxLayout()
        container.setSpacing(10)
        container.setAlignment(Qt.AlignLeft)

        # Positive buttons section
        self.positive_widget = QWidget()
        self.positive_layout = QHBoxLayout()
        self.positive_layout.setSpacing(2)
        self.positive_layout.setAlignment(Qt.AlignLeft)
        self.positive_widget.setLayout(self.positive_layout)
        self.positive_widget.setMaximumWidth(400)

        # Separator
        self.separator = QLabel("|")
        self.separator.setStyleSheet("QLabel { color: #666; font-size: 18px; padding: 0 10px; }")

        # Negative buttons section
        self.negative_widget = QWidget()
        self.negative_layout = QHBoxLayout()
        self.negative_layout.setSpacing(2)
        self.negative_layout.setAlignment(Qt.AlignLeft)
        self.negative_widget.setLayout(self.negative_layout)
        self.negative_widget.setMaximumWidth(400)

        container.addWidget(self.positive_widget)
        container.addWidget(self.separator)
        container.addWidget(self.negative_widget)
        container.addStretch(1)

        return container

    def show_controls(self):
        """Show all level control widgets."""
        for w in (getattr(self, 'positive_widget', None),
                  getattr(self, 'separator', None),
                  getattr(self, 'negative_widget', None)):
            if w:
                w.show()

    def hide_controls(self):
        """Hide all level control widgets."""
        for w in (getattr(self, 'positive_widget', None),
                  getattr(self, 'separator', None),
                  getattr(self, 'negative_widget', None)):
            if w:
                w.hide()

    def update_level_buttons(self):
        """Update both positive and negative level buttons based on tree depth."""
        self._clear_buttons()

        max_level = min(self.get_max_tree_level(), self._max_buttons)

        # Positive buttons (1 to max_level)
        for level in range(1, max_level + 1):
            button = QPushButton(str(level))
            button.setFixedSize(25, 25)
            button.clicked.connect(lambda checked, l=level: self.expand_to_level(l))
            button.setStyleSheet(self.POSITIVE_INACTIVE_STYLE)
            self.positive_layout.addWidget(button)
            self.positive_buttons.append(button)

        # Negative buttons (-1 to -(max_level-1))
        negative_max = max(1, max_level - 1)
        for level in range(1, negative_max + 1):
            button = QPushButton(f"-{level}")
            button.setFixedSize(25, 25)
            button.clicked.connect(lambda checked, l=level: self.collapse_from_bottom(l))
            button.setStyleSheet(self.NEGATIVE_INACTIVE_STYLE)
            self.negative_layout.addWidget(button)
            self.negative_buttons.append(button)

        logger.debug("Created %d positive and %d negative level buttons",
                     len(self.positive_buttons), len(self.negative_buttons))

    def _clear_buttons(self):
        """Clear all existing buttons."""
        for button in self.positive_buttons:
            self.positive_layout.removeWidget(button)
            button.deleteLater()
        self.positive_buttons = []

        for button in self.negative_buttons:
            self.negative_layout.removeWidget(button)
            button.deleteLater()
        self.negative_buttons = []

    def expand_to_level(self, level: int):
        """
        Expand tree to a specific level, collapse deeper nodes.

        Args:
            level: 1-indexed level to expand to.
        """
        self.is_updating = True

        self.current_negative_level = 0
        self._update_negative_styles(0)

        level_index = level - 1

        def process_item(index, current_level=0):
            if current_level < level_index:
                self.tree.expand(index)
            else:
                self.tree.collapse(index)
            item = self.model.itemFromIndex(index)
            if item:
                for row in range(item.rowCount()):
                    child_index = self.model.index(row, 0, index)
                    process_item(child_index, current_level + 1)

        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            process_item(index, 0)

        self.is_updating = False
        self.current_positive_level = level_index
        self._update_positive_styles(level_index)
        self.level_changed.emit(level)
        logger.debug("Expanded tree to level %d", level)

    def collapse_from_bottom(self, levels_to_hide: int):
        """
        Collapse N levels from the bottom of each branch.

        Args:
            levels_to_hide: Number of levels to collapse from each leaf node.
        """
        self.is_updating = True

        self.current_positive_level = -1
        self._update_positive_styles(-1)

        def process_branch(index, current_depth=0, path_max_depth=None):
            if path_max_depth is None:
                path_max_depth = self._get_branch_max_depth(index)

            levels_to_show = max(0, path_max_depth - levels_to_hide)

            if current_depth < levels_to_show:
                self.tree.expand(index)
            else:
                self.tree.collapse(index)

            item = self.model.itemFromIndex(index)
            if item:
                for row in range(item.rowCount()):
                    child_index = self.model.index(row, 0, index)
                    process_branch(child_index, current_depth + 1, path_max_depth)

        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            process_branch(index, 0)

        self.is_updating = False
        self.current_negative_level = levels_to_hide
        self._update_negative_styles(levels_to_hide)
        self.level_changed.emit(-levels_to_hide)
        logger.debug("Collapsed %d levels from bottom", levels_to_hide)

    def get_max_tree_level(self) -> int:
        """Calculate maximum nesting level in the tree model."""
        def traverse(index, current_level=0, max_level=0):
            if not index.isValid():
                return max_level
            max_level = max(max_level, current_level)
            item = self.model.itemFromIndex(index)
            if item:
                for row in range(item.rowCount()):
                    child_index = self.model.index(row, 0, index)
                    max_level = traverse(child_index, current_level + 1, max_level)
            return max_level

        result = 0
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            result = traverse(index, 1, result)
        return result

    def get_current_expansion_level(self) -> int:
        """Get the current maximum expanded level in the tree."""
        max_expanded = 0

        def check(index, current_level=0):
            nonlocal max_expanded
            if self.tree.isExpanded(index):
                max_expanded = max(max_expanded, current_level + 1)
                item = self.model.itemFromIndex(index)
                if item:
                    for row in range(item.rowCount()):
                        child_index = self.model.index(row, 0, index)
                        check(child_index, current_level + 1)

        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            if self.tree.isExpanded(index):
                max_expanded = max(max_expanded, 1)
                check(index, 0)
        return max_expanded

    def _get_branch_max_depth(self, index, current_depth=0) -> int:
        """Get maximum depth of a branch starting from given index."""
        item = self.model.itemFromIndex(index)
        if not item or item.rowCount() == 0:
            return current_depth

        max_depth = current_depth
        for row in range(item.rowCount()):
            child_index = self.model.index(row, 0, index)
            child_depth = self._get_branch_max_depth(child_index, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth

    def _update_positive_styles(self, current_level: int):
        """Update visual style of positive level buttons."""
        target = current_level + 1
        for i, button in enumerate(self.positive_buttons):
            is_expanded = (i + 1) <= target
            button.setStyleSheet(
                self.POSITIVE_ACTIVE_STYLE if is_expanded else self.POSITIVE_INACTIVE_STYLE
            )

    def _update_negative_styles(self, active_level: int):
        """Update visual style of negative level buttons."""
        for i, button in enumerate(self.negative_buttons):
            is_active = (i + 1) == active_level
            button.setStyleSheet(
                self.NEGATIVE_ACTIVE_STYLE if is_active else self.NEGATIVE_INACTIVE_STYLE
            )

    def restore_from_config(self, config: dict):
        """
        Restore level state from a configuration dictionary.

        Args:
            config: Dict with optional 'tree_level' and 'tree_negative_level' keys.
        """
        negative_level = config.get('tree_negative_level', 0)
        if negative_level > 0:
            self.collapse_from_bottom(negative_level)
        else:
            positive_level = config.get('tree_level', -1)
            if positive_level >= 0:
                self.expand_to_level(positive_level + 1)
