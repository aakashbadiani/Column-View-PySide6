# DataProvider Protocol -- Documentation

## Overview

The DataProvider and ThumbnailProvider protocols define how external data
sources connect to ClawTreeViewPackage widgets. This decouples the widgets
from any specific backend, database, or file format.

## DataProvider Protocol

Required by TreeModel and TreeRefreshController.

```python
class DataProvider(Protocol):
    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        """Return all items as {item_id: item_data_dict}."""
        ...

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Return data for a single item, or None."""
        ...
```

### Item Data Format

Each item_data dict must contain:
- A field matching `TreeModel.id_field` (default "ID")
- Optional `children` key: `List[str]` of child item IDs

All other keys are treated as column data, matched by header name.

Example:
```python
{
    "ID": "ASM-001",
    "Name": "Main Assembly",
    "Type": "Assembly",
    "Status": "Active",
    "children": ["PRT-001", "PRT-002"],
}
```

### DictDataProvider

Built-in implementation backed by a Python dict:

```python
from ClawTreeViewPackage import DictDataProvider

provider = DictDataProvider({
    "A": {"ID": "A", "Name": "Root", "children": ["B"]},
    "B": {"ID": "B", "Name": "Child", "children": []},
})

# Mutate at runtime
provider.add_item("C", {"ID": "C", "Name": "New", "children": []})
provider.remove_item("B")
provider.set_data({...})  # Replace all data
```

## ThumbnailProvider Protocol

Optional. Required only if you want thumbnails in the ColumnView.

```python
class ThumbnailProvider(Protocol):
    def get_thumbnails(self, item_id: str) -> List[Path]:
        """Return list of thumbnail file paths. First = primary."""
        ...

    def save_thumbnail(self, item_id: str, image_data: bytes,
                       extension: str = "png") -> Optional[Path]:
        """Save thumbnail, return path or None."""
        ...

    def delete_thumbnail(self, item_id: str, thumbnail_path: Path) -> bool:
        """Delete thumbnail. Return True if successful."""
        ...

    def set_primary_thumbnail(self, item_id: str,
                              thumbnail_path: Path) -> bool:
        """Set as primary (first). Return True if successful."""
        ...
```

### Implementing a ThumbnailProvider

```python
from pathlib import Path

class FilesystemThumbnailProvider:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def get_thumbnails(self, item_id):
        item_dir = self.base_dir / item_id
        if not item_dir.exists():
            return []
        return sorted(item_dir.glob("*.png"))

    def save_thumbnail(self, item_id, image_data, extension="png"):
        item_dir = self.base_dir / item_id
        item_dir.mkdir(parents=True, exist_ok=True)
        count = len(list(item_dir.glob(f"*.{extension}")))
        path = item_dir / f"thumb_{count:03d}.{extension}"
        path.write_bytes(image_data)
        return path

    def delete_thumbnail(self, item_id, thumbnail_path):
        thumbnail_path.unlink(missing_ok=True)
        return True

    def set_primary_thumbnail(self, item_id, thumbnail_path):
        item_dir = self.base_dir / item_id
        primary = item_dir / f"thumb_000{thumbnail_path.suffix}"
        if thumbnail_path != primary:
            thumbnail_path.rename(primary)
        return True
```

## Connecting Providers to Widgets

### TreeView

```python
provider = DictDataProvider(data)
tree_model = TreeModel(id_field="ID")
tree_model.build_tree(qt_model, provider)
```

### ColumnView with Thumbnails

```python
thumb_provider = FilesystemThumbnailProvider(Path("./thumbnails"))

column_mgr = ColumnViewManager(
    model=qt_model,
    thumbnail_provider=thumb_provider,
)
```

### Standalone ThumbnailWidget

```python
widget = ThumbnailWidget()
widget.set_thumbnail_provider(thumb_provider)
widget.set_item("ITEM-001")
```

## Custom ID Fields

By default, TreeModel uses "ID" as the item identifier field.
Override with:

```python
tree_model = TreeModel(id_field="Part Number")
tree_model.set_headers(["Part Number", "Description", "Rev"])
```

## Custom Children Key

By default, children are looked up under the "children" key.
Override with:

```python
tree_model.build_tree(qt_model, provider, children_key="sub_items")
```
