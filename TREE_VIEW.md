# ClawTreeView -- Tree View Widget Documentation

## Origin

Extracted from a production codebase. The original BOM-specific logic
(Interface() calls, quantity links, project filtering, StyleManager coupling)
has been removed. The widget is now data-agnostic.

## Architecture

```
tree/
  tree_view.py        -- ClawTreeView (QTreeView subclass)
  tree_model.py       -- TreeModel (data adapter)
  tree_highlight.py   -- HighlightDelegate + TreeHighlightController
  tree_level.py       -- LevelManager (expand/collapse buttons)
  tree_refresh.py     -- TreeRefreshController (refresh with state preservation)
```

## Components

### ClawTreeView (`tree_view.py`)

Custom QTreeView with:
- `itemClicked` signal emitting QModelIndex on click
- Alternating row colors, all-columns focus, row selection
- `configure_header()` for quick header resize mode setup

### TreeModel (`tree_model.py`)

Data-agnostic model adapter. Populates a QStandardItemModel from any
DataProvider.

Key methods:
- `set_headers(["ID", "Name", "Type"])` -- define columns
- `build_tree(model, data_provider, root_ids=None, children_key="children")`
- `create_row_items(item_data, context_path=None)` -- manual row creation

Data is stored in QStandardItem roles:
- `Qt.UserRole` -- item ID
- `Qt.UserRole + 1` -- context path (hierarchical path string)

### HighlightDelegate (`tree_highlight.py`)

Custom QStyledItemDelegate using `HIGHLIGHT_ROLE` (UserRole + 100).
When a QColor is stored at this role, the delegate paints the background
manually, bypassing stylesheet conflicts.

### TreeHighlightController (`tree_highlight.py`)

Manages highlighting by item ID:
- `highlight_item("PRT-001", "yellow")` -- highlight all instances
- `clear_all()` -- remove all highlights

Available colors: yellow, red, green, blue, clear.

### LevelManager (`tree_level.py`)

Button-based expand/collapse controls:
- Positive buttons (1..N): Expand tree to level N
- Negative buttons (-1..-(N-1)): Collapse N levels from leaf nodes
- `level_changed` signal emitting the new level

Create controls with `create_level_controls()` which returns a QHBoxLayout.

### TreeRefreshController (`tree_refresh.py`)

Refreshes tree data while preserving expansion state:
- Saves expansion state by item ID paths before refresh
- Rebuilds tree from DataProvider
- Restores expansion state after rebuild

## Data Flow

```
DataProvider.get_all_items()
    |
    v
TreeModel.build_tree()
    |
    v
QStandardItemModel  <-->  ClawTreeView
                            |
                            v
                      HighlightDelegate (painting)
                      LevelManager (buttons)
                      TreeHighlightController (highlighting)
```

## Usage Pattern

```python
from ClawTreeViewPackage import (
    ClawTreeView, TreeModel, DictDataProvider,
    HighlightDelegate, LevelManager, TreeRefreshController
)
from PySide6.QtGui import QStandardItemModel

# Data
provider = DictDataProvider({
    "A": {"ID": "A", "Name": "Root", "children": ["B"]},
    "B": {"ID": "B", "Name": "Child", "children": []},
})

# Model
qt_model = QStandardItemModel()
tree_model = TreeModel(id_field="ID")
tree_model.set_headers(["ID", "Name"])
tree_model.build_tree(qt_model, provider)

# View
tree = ClawTreeView()
tree.setModel(qt_model)
tree.setItemDelegate(HighlightDelegate(tree))

# Controls
level_mgr = LevelManager(tree, qt_model)
level_mgr.create_level_controls()
level_mgr.update_level_buttons()
level_mgr.expand_to_level(1)
```

## Keyboard-First Design Notes

- All tree operations are accessible programmatically (no mouse required)
- LevelManager provides keyboard-accessible buttons
- Expansion state is preserved across data refreshes
- Item IDs stored in UserRole enable fast lookup without model traversal

## Removed from Original

- `Interface()` backend calls (replaced by DataProvider protocol)
- Quantity link detection and L<...> wrapping
- Path-specific quantity overrides
- StyleManager mode-based styling
- Project/focus filtering
- User config persistence
- BOM-specific row creation logic

