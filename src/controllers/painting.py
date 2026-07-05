from pathlib import Path

from PySide6.QtWidgets import QTreeWidgetItem

from controllers.base import BaseElementController
from utils.drop_handler import DropHandler
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


class PaintingController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self.ui.paintingTextureButton.clicked.connect(self.pick_texture)
        self.ui.paintingConfirmButton.clicked.connect(self.confirm)
        self._drop = DropHandler(self.ui.paintingTextureButton, ".png", self.pick_texture)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.PAINTINGS)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        name = self.ui.paintingName.text()
        is_new = name not in self.project.paintings
        self.project.paintings[name] = {
            "name": name,
            "displayName": self.ui.paintingDisplayName.text(),
            "width": self.ui.paintingWidth.value(),
            "height": self.ui.paintingHeight.value(),
            "placeable": "true" if self.ui.paintingPlaceable.isChecked() else "false",
            "texture": self.project.painting_texture,
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("paintings", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.paintings[name]
        self.clear()

        self.ui.paintingDisplayName.setText(props["displayName"])
        self.ui.paintingName.setText(props["name"])
        self.ui.paintingWidth.setValue(props["width"])
        self.ui.paintingHeight.setValue(props["height"])
        self.ui.paintingPlaceable.setChecked(props["placeable"] == "true")

        self.project.painting_texture = props["texture"]
        self._show_pixmap(self.ui.paintingTexture, props["texture"])

        self.ui.elementEditor.setCurrentIndex(ElementPage.PAINTINGS)

    def clear(self):
        FieldResetter.clear_line_edits(
            self.ui.paintingDisplayName, self.ui.paintingName
        )
        FieldResetter.reset_spin_boxes(self.ui.paintingWidth, self.ui.paintingHeight)
        FieldResetter.clear_labels(self.ui.paintingTexture)
        FieldResetter.uncheck_boxes(self.ui.paintingPlaceable)
        self.project.painting_texture = None

    # ── Texture picking ───────────────────────────────────────────────────

    def pick_texture(self, path: str = None):
        if path is None:
            path = self._pick_file("Open Texture", "PNG Files (*.png)")
            if not path:
                return
        dest = self._copy_asset(path, "paintings")
        self.project.painting_texture = dest
        self._show_pixmap(self.ui.paintingTexture, dest)

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.paintingDisplayName,
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789",
            "Display Name",
        ):
            return False
        if not FieldValidator.validate_text_field(
            self.ui.paintingName, "abcdefghijklmnopqrstuvwxyz_0123456789", "Painting Name"
        ):
            return False
        if self.project.painting_texture is None:
            self.ui.paintingTextureButton.setStyleSheet("QPushButton { border: 1px solid red; }")
            alert("Please select a texture!")
            return False
        self.ui.paintingTextureButton.setStyleSheet("")
        return True
