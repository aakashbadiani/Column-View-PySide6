"""
Basic TreeView Example -- ClawTreeViewPackage

Demonstrates loading hierarchical data into ClawTreeView with:
- DictDataProvider for data
- TreeModel for model building
- LevelManager for expand/collapse controls
- HighlightDelegate for item highlighting
- TreeRefreshController for refresh with state preservation
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtGui import QStandardItemModel

# Adjust import path if running from examples/ directory
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))

from ClawTreeViewPackage import (
    ClawTreeView,
    TreeModel,
    DictDataProvider,
    HighlightDelegate,
    TreeHighlightController,
    LevelManager,
    TreeRefreshController,
    PATHS,
)


# --- Sample Data ---
SAMPLE_DATA = {
    "PRJ-001": {
        "ID": "PRJ-001",
        "Name": "Project Alpha",
        "Type": "Project",
        "children": ["ASM-001", "ASM-002"],
    },
    "ASM-001": {
        "ID": "ASM-001",
        "Name": "Main Assembly",
        "Type": "Assembly",
        "children": ["PRT-001", "PRT-002", "PRT-003"],
    },
    "ASM-002": {
        "ID": "ASM-002",
        "Name": "Sub Assembly",
        "Type": "Assembly",
        "children": ["PRT-004", "PRT-005"],
    },
    "PRT-001": {
        "ID": "PRT-001",
        "Name": "Bolt M8x20",
        "Type": "Part",
        "children": [],
    },
    "PRT-002": {
        "ID": "PRT-002",
        "Name": "Washer M8",
        "Type": "Part",
        "children": [],
    },
    "PRT-003": {
        "ID": "PRT-003",
        "Name": "Bracket L-Shape",
        "Type": "Part",
        "children": [],
    },
    "PRT-004": {
        "ID": "PRT-004",
        "Name": "Shaft 10mm",
        "Type": "Part",
        "children": [],
    },
    "PRT-005": {
        "ID": "PRT-005",
        "Name": "Bearing 6200",
        "Type": "Part",
        "children": [],
    },
}


class ExampleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClawTreeView -- Basic Example")
        self.resize(700, 500)

        # Ensure package directories exist
        PATHS.ensure_directories()

        # Set up data provider
        self.data_provider = DictDataProvider(SAMPLE_DATA)

        # Set up model
        self.qt_model = QStandardItemModel()
        self.tree_model = TreeModel(id_field="ID")
        self.tree_model.set_headers(["ID", "Name", "Type"])

        # Set up tree view
        self.tree = ClawTreeView()
        self.tree.setModel(self.qt_model)
        delegate = HighlightDelegate(self.tree)
        self.tree.setItemDelegate(delegate)

        # Build tree
        self.tree_model.build_tree(self.qt_model, self.data_provider)

        # Set up level manager
        self.level_manager = LevelManager(self.tree, self.qt_model)
        level_layout = self.level_manager.create_level_controls()
        self.level_manager.update_level_buttons()
        self.level_manager.expand_to_level(2)

        # Set up highlight controller
        self.highlight_ctrl = TreeHighlightController(self.qt_model)

        # Set up refresh controller
        self.refresh_ctrl = TreeRefreshController(
            self.qt_model, self.tree, self.tree_model, self.data_provider
        )

        # Buttons
        btn_layout = QHBoxLayout()
        btn_highlight = QPushButton("Highlight PRT-001")
        btn_highlight.clicked.connect(lambda: self.highlight_ctrl.highlight_item("PRT-001", "yellow"))
        btn_clear = QPushButton("Clear Highlights")
        btn_clear.clicked.connect(self.highlight_ctrl.clear_all)
        btn_refresh = QPushButton("Refresh Tree")
        btn_refresh.clicked.connect(self.refresh_ctrl.refresh)
        btn_layout.addWidget(btn_highlight)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_refresh)

        # Layout
        main = QVBoxLayout()
        main.addLayout(level_layout)
        main.addWidget(self.tree)
        main.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(main)
        self.setCentralWidget(container)

        # Connect click signal
        self.tree.itemClicked.connect(self._on_item_clicked)

    def _on_item_clicked(self, index):
        item_id = index.data(0x0100)  # Qt.UserRole
        print(f"Clicked: {item_id}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.show()
    sys.exit(app.exec())
