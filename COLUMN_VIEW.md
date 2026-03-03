# ClawColumnView -- Column View Widget Documentation

## Origin

Extracted from `100 Code/src/ui_columnview/`. The original BOM-specific logic
(Interface() calls, PATHS.get_part_dir, user config persistence, thumbnail
file naming conventions) has been removed. The widget now uses a
ThumbnailProvider protocol for any thumbnail source.

## Architecture

```
columnview/
  column_view.py          -- ClawColumnView (QColumnView subclass)
  column_manager.py       -- ColumnViewManager (orchestrator)
  thumbnail_widget.py     -- ThumbnailWidget (display/cycling widget)
  thumbnail_delegate.py   -- ThumbnailColumnDelegate (paint + editor)
  thumbnail_renderer.py   -- ThumbnailRenderService (cached loading)
  thumbnail_factory.py    -- ThumbnailWidgetFactory (standardized sizes)
```

## Components

### ClawColumnView (`column_view.py`)

Custom QColumnView solving Qt's editor overlay problem:
- Prevents white selection background from obscuring editor widgets
- `drawRow()` skips painting for items with persistent editors
- Preserves selection when clicking empty space
- Event filter on child QListView viewports (dynamically created)
- Editor index tracking for efficient geometry updates

### ColumnViewManager (`column_manager.py`)

Orchestrates the column view with:
- Thumbnail delegates
- Persistent editor management (ThumbnailWidget on selection ONLY)
- Selection chain support (multiple path items)
- Tree view synchronization (column selection -> tree selection)
- Context menu signal

Signals:
- `item_selected(QModelIndex)` -- fired when selection changes
- `context_menu_requested(QPoint, QModelIndex)` -- for custom menus

Key methods:
- `get_widget()` -- returns the ClawColumnView for layout embedding
- `navigate_to_item(item_id)` -- programmatic navigation
- `restore_selection_path(["ROOT", "CHILD", "LEAF"])` -- path restoration
- `set_thumbnail_provider(provider)` -- set/change thumbnail source

### ThumbnailWidget (`thumbnail_widget.py`)

Reusable thumbnail display widget:
- Left-click: Cycle through multiple thumbnails
- Ctrl+Left-click: Emit expand request signal
- Right-click: Context menu (paste, make primary, delete)
- Dynamic sizing with configurable min width/height
- Requires a ThumbnailProvider via `set_thumbnail_provider()`

### ThumbnailColumnDelegate (`thumbnail_delegate.py`)

Custom QStyledItemDelegate:
- `paint()`: Renders thumbnail preview for unselected items
- `createEditor()`: Creates ThumbnailWidget for selected items
- `sizeHint()`: Fixed 140x180 per item
- Optional `get_display_text` callback for custom text below thumbnails
- Thumbnail path caching for performance

### ThumbnailRenderService (`thumbnail_renderer.py`)

Cached pixmap loading (LRU, max 100):
- `load_thumbnail(path, width, height)` -- loads and scales
- `render_thumbnail(pixmap, rect, painter)` -- centered with border
- `render_placeholder(rect, painter)` -- placeholder for missing
- `clear_cache()` / `get_cache_info()`

### ThumbnailWidgetFactory (`thumbnail_factory.py`)

Standardized sizes:
- `create_for_main_view()` -- 120x120
- `create_for_dialog()` -- 112x112
- `create_for_column_view()` -- 100x100
- `create_for_large()` -- 200x200
- `create_custom(min_width, min_height)` -- any size

## Data Flow

```
ThumbnailProvider.get_thumbnails(item_id)
    |
    v
ThumbnailColumnDelegate  -->  ThumbnailRenderService (cached)
    |                              |
    |  (selected)                  v
    v                         QPixmap rendering
ThumbnailWidget
    |
    v
ThumbnailProvider.save_thumbnail() / delete_thumbnail()
```

## Usage Pattern

```python
from ClawTreeViewPackage import (
    ColumnViewManager, TreeModel, DictDataProvider
)
from PySide6.QtGui import QStandardItemModel

# Same model as tree view
qt_model = QStandardItemModel()
# ... build tree ...

# Column view
column_mgr = ColumnViewManager(
    parent=some_widget,
    model=qt_model,
    tree_view=tree_widget,  # optional, for selection sync
)

# Add to layout
layout.addWidget(column_mgr.get_widget())

# Handle selection
column_mgr.item_selected.connect(on_selection_changed)

# Navigate programmatically
column_mgr.navigate_to_item("ITEM-005")
```

### With Thumbnails

```python
class MyThumbnailProvider:
    def get_thumbnails(self, item_id):
        return list(Path(f"thumbnails/{item_id}").glob("*.png"))

    def save_thumbnail(self, item_id, data, ext="png"):
        path = Path(f"thumbnails/{item_id}/thumb.{ext}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def delete_thumbnail(self, item_id, path):
        path.unlink(missing_ok=True)
        return True

    def set_primary_thumbnail(self, item_id, path):
        # Move to first position
        return True

provider = MyThumbnailProvider()

column_mgr = ColumnViewManager(
    parent=some_widget,
    model=qt_model,
    thumbnail_provider=provider,
)
```

## Editor Behavior

- Editors (ThumbnailWidget) are created ONLY on selection
- Hover does NOT create editors, only paints thumbnails
- Selection changes close editors not in the current selection path
- The current (final) item in the path gets the interactive editor
- Intermediate path items are rendered by the delegate's paint()

## Removed from Original

- `Interface()` backend calls (replaced by ThumbnailProvider protocol)
- `PATHS.get_part_dir()` for thumbnail lookup (provider handles this)
- User config for thumbnail index persistence
- BOM-specific part data fetching in delegate paint()
- Debug background colors (red tinted) from factory
- Hardcoded thumbnail file naming conventions
