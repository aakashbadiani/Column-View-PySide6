"""
ThumbnailRenderService -- Cached pixmap loading and consistent rendering.

Provides:
- LRU cached pixmap loading with aspect ratio preservation
- Consistent border/background/placeholder rendering
- DPI-aware sizing
"""

import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QColor, QPainter

logger = logging.getLogger(__name__)


class ThumbnailRenderService:
    """
    Centralized service for rendering thumbnails consistently.

    Features:
    - LRU cached pixmap loading (max 100 thumbnails)
    - Consistent aspect ratio handling
    - Unified styling (borders, backgrounds)
    - Placeholder generation
    """

    BORDER_COLOR = QColor(180, 180, 180)
    BORDER_WIDTH = 1
    BACKGROUND_COLOR = QColor(240, 240, 240)
    PLACEHOLDER_BG_COLOR = QColor(200, 200, 200)
    PLACEHOLDER_TEXT_COLOR = QColor(100, 100, 100)

    def __init__(self):
        self._cache_clear_count = 0
        logger.debug("ThumbnailRenderService initialized")

    @lru_cache(maxsize=100)
    def load_thumbnail(self, thumbnail_path: str, target_width: int, target_height: int) -> Optional[QPixmap]:
        """
        Load and scale a thumbnail with caching.

        Args:
            thumbnail_path: Path to thumbnail file (string for hashability).
            target_width: Target width in pixels.
            target_height: Target height in pixels.

        Returns:
            Scaled QPixmap or None if loading fails.
        """
        try:
            path_obj = Path(thumbnail_path)
            if not path_obj.exists():
                return None

            pixmap = QPixmap(str(path_obj))
            if pixmap.isNull():
                return None

            scaled = pixmap.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            return scaled

        except Exception as e:
            logger.error("Failed to load thumbnail %s: %s", thumbnail_path, e)
            return None

    def render_thumbnail(self, pixmap: QPixmap, target_rect: QRect, painter: QPainter) -> None:
        """
        Render a thumbnail pixmap centered within target rect with border.

        Args:
            pixmap: The thumbnail pixmap.
            target_rect: Rectangle to render within.
            painter: QPainter instance.
        """
        if pixmap is None or pixmap.isNull():
            self.render_placeholder(target_rect, painter)
            return

        x = target_rect.x() + (target_rect.width() - pixmap.width()) // 2
        y = target_rect.y() + (target_rect.height() - pixmap.height()) // 2

        painter.drawPixmap(x, y, pixmap)
        painter.setPen(self.BORDER_COLOR)
        painter.drawRect(x, y, pixmap.width(), pixmap.height())

    def render_placeholder(self, target_rect: QRect, painter: QPainter, text: str = "No\nImage") -> None:
        """Render a placeholder for missing thumbnails."""
        painter.fillRect(target_rect, self.PLACEHOLDER_BG_COLOR)
        painter.setPen(self.BORDER_COLOR)
        painter.drawRect(target_rect)
        painter.setPen(self.PLACEHOLDER_TEXT_COLOR)
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(target_rect, Qt.AlignCenter, text)

    def create_placeholder_pixmap(self, width: int, height: int, text: str = "No\nImage") -> QPixmap:
        """Create a pixmap with placeholder graphics."""
        pixmap = QPixmap(width, height)
        pixmap.fill(self.PLACEHOLDER_BG_COLOR)

        painter = QPainter(pixmap)
        try:
            painter.setPen(self.BORDER_COLOR)
            painter.drawRect(0, 0, width - 1, height - 1)
            painter.setPen(self.PLACEHOLDER_TEXT_COLOR)
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(0, 0, width, height, Qt.AlignCenter, text)
        finally:
            painter.end()

        return pixmap

    def clear_cache(self) -> None:
        """Clear the thumbnail cache."""
        self.load_thumbnail.cache_clear()
        self._cache_clear_count += 1
        logger.debug("Thumbnail cache cleared (count: %d)", self._cache_clear_count)

    def get_cache_info(self) -> dict:
        """Get cache statistics."""
        info = self.load_thumbnail.cache_info()
        return {
            'hits': info.hits,
            'misses': info.misses,
            'size': info.currsize,
            'maxsize': info.maxsize,
        }


# Singleton
_service_instance: Optional[ThumbnailRenderService] = None


def get_thumbnail_service() -> ThumbnailRenderService:
    """Get the singleton ThumbnailRenderService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ThumbnailRenderService()
    return _service_instance
