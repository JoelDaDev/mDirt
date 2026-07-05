import os
from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QTreeWidgetItem

from controllers.base import BaseElementController
from utils.drop_handler import DropHandler
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


class StructureController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self._biome_checkboxes: dict = {}

        self.ui.structureNBTButton.clicked.connect(self.pick_nbt)
        self.ui.structureConfirmButton.clicked.connect(self.confirm)
        self._drop = DropHandler(self.ui.structureNBTButton, ".nbt", self.pick_nbt)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self._load_biome_list()
        self.ui.elementEditor.setCurrentIndex(ElementPage.STRUCTURES)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        name = self.ui.structureName.text()
        is_new = name not in self.project.structures
        self.project.structures[name] = {
            "name": name,
            "structure": self.project.structure_path,
            "step": self.ui.structureLocation.currentText(),
            "terrain_adaptation": self.ui.structureTerrainAdaptation.currentText(),
            "start_height": self.ui.structureStartHeight.value(),
            "psth": self.ui.structurePSTH.currentText(),
            "spacing": self.ui.structureSpacing.value(),
            "seperation": self.ui.structureSeperation.value(),
            "biomes": self._checked_biomes(),
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("structures", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.structures[name]
        self.clear()
        self._load_biome_list()

        self.project.structure_path = props["structure"]
        self.ui.structureName.setText(props["name"])
        self.ui.structureNBTButton.setText(os.path.basename(props["structure"]))
        self.ui.structureLocation.setCurrentText(props["step"])
        self.ui.structureTerrainAdaptation.setCurrentText(props["terrain_adaptation"])
        self.ui.structureStartHeight.setValue(props["start_height"])
        self.ui.structurePSTH.setCurrentText(props["psth"])
        self.ui.structureSpacing.setValue(props["spacing"])
        self.ui.structureSeperation.setValue(props["seperation"])

        for biome in props.get("biomes", []):
            if biome in self._biome_checkboxes:
                self._biome_checkboxes[biome].setChecked(True)

        self.ui.elementEditor.setCurrentIndex(ElementPage.STRUCTURES)

    def clear(self):
        FieldResetter.clear_line_edits(self.ui.structureName)
        FieldResetter.reset_spin_boxes(
            self.ui.structureStartHeight,
            self.ui.structureSpacing,
            self.ui.structureSeperation,
        )
        FieldResetter.reset_combo_boxes(
            self.ui.structureLocation,
            self.ui.structureTerrainAdaptation,
            self.ui.structurePSTH,
        )
        self.ui.structureNBTButton.setText("...")
        self.ui.structureNBTButton.setStyleSheet("")
        self.project.structure_path = None
        self._clear_biome_list()

    # ── NBT picking ───────────────────────────────────────────────────────

    def pick_nbt(self, path: str = None):
        if path is None:
            path = self._pick_file("Open Structure File", "NBT Files (*.nbt)")
            if not path:
                return
        dest = self._copy_asset(path, "structures")
        self.project.structure_path = dest
        self.ui.structureNBTButton.setText(os.path.basename(dest))
        self.ui.structureNBTButton.setStyleSheet("")

    # ── Biome list ────────────────────────────────────────────────────────

    def _load_biome_list(self):
        self._clear_biome_list()
        for biome in self.project.mc_data.get("biomes", []):
            checkbox = QCheckBox(biome)
            self._biome_checkboxes[biome] = checkbox
            self.ui.verticalLayout_3.addWidget(checkbox)

    def _clear_biome_list(self):
        for cb in self._biome_checkboxes.values():
            self.ui.verticalLayout_3.removeWidget(cb)
            cb.deleteLater()
        self._biome_checkboxes = {}

    def _checked_biomes(self) -> list:
        return [b for b, cb in self._biome_checkboxes.items() if cb.isChecked()]

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.structureName, "abcdefghijklmnopqrstuvwxyz_0123456789", "Structure Name"
        ):
            return False
        if self.project.structure_path is None:
            self.ui.structureNBTButton.setStyleSheet("QPushButton { border: 1px solid red; }")
            alert("Please select a structure file!")
            return False
        return True
