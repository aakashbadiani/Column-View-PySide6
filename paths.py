"""
Centralized path management for ClawTreeViewPackage.
Single source of truth for all paths and directory creation.
"""

import sys
from pathlib import Path


class PackagePathManager:
    """
    Centralized path management for ClawTreeViewPackage.
    All folder creation logic is consolidated here.
    """

    def __init__(self):
        self.is_frozen = getattr(sys, 'frozen', False)

        if self.is_frozen:
            self.package_root = Path(sys.executable).parent
        else:
            self.package_root = Path(__file__).parent

        # State persistence directory
        self.state_dir = self.package_root / "_state"

        # State file for UI persistence (expansion state, etc.)
        self.state_file = self.state_dir / "ui_state.json"

        # Cache directory for thumbnails, rendered pixmaps, etc.
        self.cache_dir = self.state_dir / "cache"

        # Thumbnail cache subdirectory
        self.thumbnail_cache_dir = self.cache_dir / "thumbnails"

    def ensure_directories(self):
        """
        Create all required directories if they don't exist.
        This is THE ONLY place where directories should be created.
        """
        required_directories = [
            self.state_dir,
            self.cache_dir,
            self.thumbnail_cache_dir,
        ]

        for directory in required_directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_state_file(self) -> Path:
        """Get path to the UI state persistence file."""
        return self.state_file

    def get_cache_dir(self) -> Path:
        """Get path to the cache directory."""
        return self.cache_dir

    def get_thumbnail_cache_dir(self) -> Path:
        """Get path to the thumbnail cache directory."""
        return self.thumbnail_cache_dir


# Singleton instance
PATHS = PackagePathManager()
