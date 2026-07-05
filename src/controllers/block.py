import os
import shutil
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem

from controllers.base import BaseElementController
from utils.drop_handler import DropHandler
from utils.enums import BlockFace, ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


class BlockController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self._setup_drop_handlers()
        self.ui.blockModel.currentTextChanged.connect(self._on_model_changed)
        self.ui.blockConfirmButton.clicked.connect(self.confirm)

    # ── Drop handler wiring ───────────────────────────────────────────────

    def _setup_drop_handlers(self):
        face_buttons = {
            BlockFace.TOP:    self.ui.blockTextureButtonTop,
            BlockFace.LEFT:   self.ui.blockTextureButtonLeft,
            BlockFace.BACK:   self.ui.blockTextureButtonBack,
            BlockFace.RIGHT:  self.ui.blockTextureButtonRight,
            BlockFace.FRONT:  self.ui.blockTextureButtonFront,
            BlockFace.BOTTOM: self.ui.blockTextureButtonBottom,
        }
        self._drop_handlers = []
        for face, btn in face_buttons.items():
            btn.clicked.connect(lambda checked=False, f=face: self.pick_texture(f))
            handler = DropHandler(btn, ".png", lambda p, f=face: self.pick_texture(f, p))
            self._drop_handlers.append(handler)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self._populate_drop()
        self.ui.elementEditor.setCurrentIndex(ElementPage.BLOCKS)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        name = self.ui.blockName.text()
        is_new = name not in self.project.blocks
        self.project.blocks[name] = {
            "name": name,
            "displayName": self.ui.blockDisplayName.text(),
            "baseBlock": self.ui.blockBaseBlock.text(),
            "textures": dict(self.project.block_textures),
            "placeSound": self.ui.blockPlaceSound.text(),
            "blockDrop": self.ui.blockDropBox.currentText(),
            "directional": "true" if self.ui.blockDirectional.isChecked() else "false",
            "model": self.ui.blockModel.currentText(),
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("blocks", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.blocks[name]
        self.clear()
        self._populate_drop()

        self.ui.blockName.setText(props["name"])
        self.ui.blockDisplayName.setText(props["displayName"])
        self.ui.blockBaseBlock.setText(props["baseBlock"])
        self.ui.blockDropBox.setCurrentText(props["blockDrop"])
        self.ui.blockPlaceSound.setText(props.get("placeSound", ""))
        self.ui.blockDirectional.setChecked(props["directional"] == "true")
        self.ui.blockModel.setCurrentText(props["model"])

        self.project.block_textures = dict(props.get("textures", {}))
        for face_key, path in self.project.block_textures.items():
            self._show_pixmap(self._face_label(BlockFace(int(face_key))), path)

        self.ui.elementEditor.setCurrentIndex(ElementPage.BLOCKS)

    def clear(self):
        FieldResetter.clear_line_edits(
            self.ui.blockName, self.ui.blockDisplayName,
            self.ui.blockBaseBlock, self.ui.blockPlaceSound,
        )
        FieldResetter.reset_combo_boxes(self.ui.blockDropBox, self.ui.blockModel)
        FieldResetter.clear_labels(
            self.ui.blockTextureLabelTop, self.ui.blockTextureLabelLeft,
            self.ui.blockTextureLabelBack, self.ui.blockTextureLabelRight,
            self.ui.blockTextureLabelFront, self.ui.blockTextureLabelBottom,
        )
        FieldResetter.uncheck_boxes(self.ui.blockDirectional)
        FieldResetter.clear_tree_selection(self.ui.elementViewer)
        self.project.block_textures = {}

    # ── Texture picking ───────────────────────────────────────────────────

    def pick_texture(self, face: BlockFace, path: str = None):
        if path is None:
            path = self._pick_file("Open Texture", "PNG Files (*.png)")
            if not path:
                return
        dest = self._copy_asset(path, "blocks")
        self.project.block_textures[face] = dest
        self._show_pixmap(self._face_label(face), dest)

    def _face_label(self, face: BlockFace):
        return {
            BlockFace.TOP:    self.ui.blockTextureLabelTop,
            BlockFace.LEFT:   self.ui.blockTextureLabelLeft,
            BlockFace.BACK:   self.ui.blockTextureLabelBack,
            BlockFace.RIGHT:  self.ui.blockTextureLabelRight,
            BlockFace.FRONT:  self.ui.blockTextureLabelFront,
            BlockFace.BOTTOM: self.ui.blockTextureLabelBottom,
        }[face]

    # ── Custom model ──────────────────────────────────────────────────────

    def _on_model_changed(self):
        if self.ui.blockModel.currentText() != "Custom":
            return
        path = self._pick_file("Open JSON Model", "JSON Files (*.json)")
        if not path:
            return
        dest = self._copy_asset(path, "blocks")
        self.ui.blockModel.addItem(dest)
        self.ui.blockModel.setCurrentText(dest)

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        ok = True
        ok &= FieldValidator.validate_text_field(
            self.ui.blockDisplayName,
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789",
            "Display Name",
        )
        ok &= FieldValidator.validate_text_field(
            self.ui.blockName, "abcdefghijklmnopqrstuvwxyz_0123456789", "Name"
        )
        ok &= FieldValidator.validate_dropdown_selection(
            self.ui.blockBaseBlock, list(self.project.mc_data["blocks"]), "Base Block"
        )
        return ok

    # ── Drop-box population ───────────────────────────────────────────────

    def _populate_drop(self):
        self.ui.blockDropBox.clear()
        self.ui.blockDropBox.addItem("self")
        for name in self.project.blocks:
            self.ui.blockDropBox.addItem(name)
        for name in self.project.items:
            self.ui.blockDropBox.addItem(name)
        for name, equip in self.project.equipment.items():
            for slot in ["helmet", "chestplate", "leggings", "boots", "horse_armor"]:
                if equip["includeHorse"] != "true" and slot == "horse_armor":
                    continue
                self.ui.blockDropBox.addItem(f'{equip["name"]}_{slot}')
        for item in self.project.mc_data.get("items", []):
            self.ui.blockDropBox.addItem(item)
