from pathlib import Path

from PySide6.QtWidgets import QTreeWidgetItem

from controllers.base import BaseElementController
from utils.drop_handler import DropHandler
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


class ItemController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self.ui.itemTextureButton.clicked.connect(self.pick_texture)
        self.ui.itemConfirmButton.clicked.connect(self.confirm)
        self._drop = DropHandler(self.ui.itemTextureButton, ".png", self.pick_texture)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.ITEMS)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        name = self.ui.itemName.text()
        is_new = name not in self.project.items
        self.project.items[name] = {
            "name": name,
            "displayName": self.ui.itemDisplayName.text(),
            "baseItem": self.ui.itemBaseItem.text(),
            "texture": self.project.item_texture,
            "model": self.ui.itemModel.currentText().lower(),
            "stackSize": self.ui.itemStackSize.value(),
            "rightClick": {
                "enabled": "true" if self.ui.itemRightClickCheck.isChecked() else "false",
                "function": self.ui.itemRightClickFunc.toPlainText(),
                "mode": self.ui.itemRightClickMode.currentText().lower(),
            },
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("items", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.items[name]
        self.clear()

        self.ui.itemName.setText(props["name"])
        self.ui.itemDisplayName.setText(props["displayName"])
        self.ui.itemBaseItem.setText(props["baseItem"])
        self.ui.itemModel.setCurrentText(props["model"])
        self.ui.itemStackSize.setValue(props["stackSize"])
        self.ui.itemRightClickFunc.setPlainText(props["rightClick"]["function"])
        self.ui.itemRightClickMode.setCurrentText(props["rightClick"]["mode"])
        self.ui.itemRightClickCheck.setChecked(props["rightClick"]["enabled"] == "true")

        self.project.item_texture = props["texture"]
        self._show_pixmap(self.ui.itemTexture, props["texture"])

        self.ui.elementEditor.setCurrentIndex(ElementPage.ITEMS)

    def clear(self):
        FieldResetter.clear_line_edits(
            self.ui.itemName, self.ui.itemDisplayName, self.ui.itemBaseItem
        )
        FieldResetter.reset_combo_boxes(self.ui.itemModel, self.ui.itemRightClickMode)
        FieldResetter.reset_spin_boxes(self.ui.itemStackSize)
        FieldResetter.clear_text_edits(self.ui.itemRightClickFunc)
        FieldResetter.clear_labels(self.ui.itemTexture)
        FieldResetter.uncheck_boxes(self.ui.itemRightClickCheck)
        FieldResetter.clear_tree_selection(self.ui.elementViewer)
        self.project.item_texture = None

    # ── Texture picking ───────────────────────────────────────────────────

    def pick_texture(self, path: str = None):
        if path is None:
            path = self._pick_file("Open Texture", "PNG Files (*.png)")
            if not path:
                return
        dest = self._copy_asset(path, "items")
        self.project.item_texture = dest
        self._show_pixmap(self.ui.itemTexture, dest)

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.itemDisplayName,
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789",
            "Display Name",
        ):
            return False
        if not FieldValidator.validate_text_field(
            self.ui.itemName, "abcdefghijklmnopqrstuvwxyz_0123456789", "Item Name"
        ):
            return False
        if self.ui.itemBaseItem.text() not in self.project.mc_data.get("items", []):
            self.ui.itemBaseItem.setStyleSheet("QLineEdit { border: 1px solid red; }")
            alert("Please input a valid Minecraft item in the Base Item field!")
            return False
        self.ui.itemBaseItem.setStyleSheet("")
        if self.project.item_texture is None:
            self.ui.itemTextureButton.setStyleSheet("QPushButton { border: 1px solid red; }")
            alert("Please select a texture!")
            return False
        self.ui.itemTextureButton.setStyleSheet("")
        return True
