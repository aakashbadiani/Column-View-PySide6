"""
ColumnView Example -- ClawTreeViewPackage

Demonstrates the ColumnViewManager with:
- Shared QStandardItemModel between tree and column view
- Thumbnail display (using ThumbnailProvider protocol)
- Selection synchronization between tree and column view
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QVBoxLayout, QWidget, QPushButton
)
from PySide6.QtGui import QStandardItemModel
from PySide6.QtCore import Qt

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))

from ClawTreeViewPackage import (
    ClawTreeView,
    TreeModel,
    DictDataProvider,
    HighlightDelegate,
    LevelManager,
    ColumnViewManager,
    PATHS,
)


SAMPLE_DATA = {
    "ROOT": {
        "ID": "ROOT",
        "Name": "Vehicle",
        "children": ["CHASSIS", "ENGINE"],
    },
    "CHASSIS": {
        "ID": "CHASSIS",
        "Name": "Chassis Assembly",
        "children": ["FRAME", "SUSPENSION"],
    },
    "ENGINE": {
        "ID": "ENGINE",
        "Name": "Engine Assembly",
        "children": ["BLOCK", "HEAD"],
    },
    "FRAME": {
        "ID": "FRAME",
        "Name": "Main Frame",
        "children": [],
    },
    "SUSPENSION": {
        "ID": "SUSPENSION",
        "Name": "Front Suspension",
        "children": [],
    },
    "BLOCK": {
        "ID": "BLOCK",
        "Name": "Engine Block",
        "children": [],
    },
    "HEAD": {
        "ID": "HEAD",
        "Name": "Cylinder Head",
        "children": [],
    },
}


class ColumnViewExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClawTreeView + ColumnView Example")
        self.resize(1000, 600)

        PATHS.ensure_directories()

        self.data_provider = DictDataProvider(SAMPLE_DATA)

        # Shared model
        self.qt_model = QStandardItemModel()
        self.tree_model = TreeModel(id_field="ID")
        self.tree_model.set_headers(["ID", "Name"])
        self.tree_model.build_tree(self.qt_model, self.data_provider)

        # Tree view (left)
        self.tree = ClawTreeView()
        self.tree.setModel(self.qt_model)
        self.tree.setItemDelegate(HighlightDelegate(self.tree))

        # Level controls
        self.level_mgr = LevelManager(self.tree, self.qt_model)
        level_layout = self.level_mgr.create_level_controls()
        self.level_mgr.update_level_buttons()
        self.level_mgr.expand_to_level(2)

        # Column view (right) -- no thumbnail provider, just hierarchical navigation
        self.column_mgr = ColumnViewManager(
            parent=None,
            model=self.qt_model,
            tree_view=self.tree,
        )
        self.column_mgr.item_selected.connect(self._on_column_selection)

        # Layout
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addLayout(level_layout)
        left_layout.addWidget(self.tree)

        splitter.addWidget(left)
        splitter.addWidget(self.column_mgr.get_widget())
        splitter.setSizes([400, 600])

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)

    def _on_column_selection(self, index):
        item_id = index.data(Qt.UserRole)
        print(f"Column view selected: {item_id}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColumnViewExample()
    window.show()
    sys.exit(app.exec())
