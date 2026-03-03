# QtColumnView

A standalone PySide6 column view widget with thumbnail support, extracted from a production BOM (Bill of Materials) application.

## What It Is

A `QColumnView` subclass that solves real problems Qt's built-in column view has:
- White selection background obscuring editor widgets
- Thumbnail display with click-to-cycle behaviour
- Selection synchronisation with an external tree view
- Persistent editor management (editors created on selection, not hover)
- Programmatic navigation and path restoration

## Install

```bash
pip install pyside6
```

Clone this repo and import directly -- no package install required yet.

## Quick Start

```python
from QtTreeViewPackage import ColumnViewManager, TreeModel, DictDataProvider
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication

app = QApplication([])
qt_model = QStandardItemModel()

# Build your tree model
data_provider = DictDataProvider(your_data_dict)
tree_model = TreeModel(id_field="ID")
tree_model.set_headers(["ID", "Name"])
tree_model.build_tree(qt_model, data_provider)

# Column view
column_mgr = ColumnViewManager(parent=None, model=qt_model)
column_mgr.item_selected.connect(lambda idx: print(idx.data()))

widget = column_mgr.get_widget()
widget.show()
app.exec()
```

## With Thumbnails

Implement the `ThumbnailProvider` protocol:

```python
class MyProvider:
    def get_thumbnails(self, item_id): return list(Path(f"thumbs/{item_id}").glob("*.png"))
    def save_thumbnail(self, item_id, data, ext="png"): ...
    def delete_thumbnail(self, item_id, path): ...
    def set_primary_thumbnail(self, item_id, path): ...

column_mgr = ColumnViewManager(parent=None, model=qt_model, thumbnail_provider=MyProvider())
```

## Run the Example

```bash
python examples/example_column_view.py
```

## Structure

```
columnview/
    column_view.py          -- QtColumnView (QColumnView subclass)
    column_manager.py       -- ColumnViewManager (orchestrator)
    thumbnail_widget.py     -- ThumbnailWidget (click-to-cycle display)
    thumbnail_delegate.py   -- ThumbnailColumnDelegate (paint + editor)
    thumbnail_renderer.py   -- ThumbnailRenderService (LRU cached loading)
    thumbnail_factory.py    -- ThumbnailWidgetFactory (standard sizes)
tree/
    tree_model.py           -- TreeModel (QStandardItemModel builder)
    tree_view.py            -- QtTreeView
    tree_highlight.py       -- HighlightDelegate
    tree_level.py           -- LevelManager
    tree_refresh.py         -- RefreshManager
data_provider.py            -- DictDataProvider + ThumbnailProvider protocol
examples/
    example_column_view.py  -- Column view with tree sync
    example_tree_basic.py   -- Tree view only
```

## Requirements

- Python 3.10+
- PySide6

## License

MIT

