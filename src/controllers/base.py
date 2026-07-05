"""
Abstract base class every element controller inherits from.

A controller owns all UI logic for one element type (Block, Item, etc.).
It reads from and writes to Project, leaving the Window class thin.
"""
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem

from models.project import Project


class BaseElementController(ABC):

    def __init__(self, ui, project: Project, main_dir: Path):
        self.ui = ui
        self.project = project
        self.main_dir = main_dir

    # ── Required overrides ────────────────────────────────────────────────

    @abstractmethod
    def new(self):
        """Prepare the UI for creating a new element."""

    @abstractmethod
    def confirm(self) -> bool:
        """Validate inputs, persist to project, clear UI. Return True on success."""

    @abstractmethod
    def edit(self, name: str):
        """Populate the editor UI from an existing element by name."""

    @abstractmethod
    def clear(self):
        """Reset all UI fields in this controller's editor to defaults."""

    # ── Shared helpers ────────────────────────────────────────────────────

    def _asset_dir(self, *parts) -> Path:
        """Return (and create) a path inside the current project's assets folder."""
        ns = self.project.pack_details.namespace
        path = self.main_dir / "workspaces" / ns / "assets" / Path(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _copy_asset(self, src: str, subdir: str) -> str:
        """Copy a file into the project asset folder and return the destination path."""
        dest = self._asset_dir(subdir) / os.path.basename(src)
        shutil.copyfile(src, dest)
        return str(dest)

    def _show_pixmap(self, label_widget, path: str, size: int = 50):
        """Load an image and display it in a QLabel."""
        pixmap = QPixmap.fromImage(QImage(path)).scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatio
        )
        label_widget.setPixmap(pixmap)

    def _pick_file(self, title: str, file_filter: str) -> str | None:
        """Open a file picker and return the chosen path, or None."""
        path, _ = QFileDialog.getOpenFileName(None, title, "", file_filter)
        return path if path else None

    def _add_to_tree(self, category: str, name: str):
        """Append a leaf node to the project tree under the given category."""
        tree = self.project.trees.get(category)
        if tree is not None:
            QTreeWidgetItem(tree, [name])

    def _rebuild_tree(self, category: str, data: dict):
        """Replace all leaf nodes under a category with the keys from data."""
        tree = self.project.trees.get(category)
        if tree is None:
            return
        tree.takeChildren()
        for name in data:
            QTreeWidgetItem(tree, [name])
