from pathlib import Path

from PySide6.QtWidgets import QTreeWidgetItem

from controllers.base import BaseElementController
from utils.drop_handler import DropHandler
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


# (asset subtype, project key, label widget attr)
_ITEM_SLOTS = [
    ("helmet",     "helmet",     "helmetItemLabel"),
    ("chestplate", "chestplate", "chestplateItemLabel"),
    ("leggings",   "leggings",   "leggingsItemLabel"),
    ("boots",      "boots",      "bootsItemLabel"),
    ("horseArmor", "horseArmor", "horseArmorItemLabel"),
]
_MODEL_SLOTS = [
    ("humanoid",          "h",         "chestplateModelLabel"),
    ("humanoid_leggings", "h_l",       "leggingsModelLabel"),
    ("horseArmor1",       "horseArmor","horseArmorModelLabel"),
]


class EquipmentController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self._setup_buttons()
        self.ui.equipmentConfirmButton.clicked.connect(self.confirm)

    # ── Button wiring ─────────────────────────────────────────────────────

    def _setup_buttons(self):
        self._drop_handlers = []
        for slot_name, proj_key, label_attr in _ITEM_SLOTS:
            btn = getattr(self.ui, f"{slot_name}Item")
            label = getattr(self.ui, label_attr)
            btn.clicked.connect(
                lambda checked=False, k=proj_key, l=label: self._pick_item_texture(k, l)
            )
            h = DropHandler(btn, ".png", lambda p, k=proj_key, l=label: self._pick_item_texture(k, l, p))
            self._drop_handlers.append(h)

        for type_key, proj_key, label_attr in _MODEL_SLOTS:
            btn = getattr(self.ui, {
                "humanoid": "chestplateModel",
                "humanoid_leggings": "leggingsModel",
                "horseArmor1": "horseArmorModel",
            }[type_key])
            label = getattr(self.ui, label_attr)
            btn.clicked.connect(
                lambda checked=False, k=proj_key, l=label: self._pick_model_texture(k, l)
            )
            h = DropHandler(btn, ".png", lambda p, k=proj_key, l=label: self._pick_model_texture(k, l, p))
            self._drop_handlers.append(h)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.EQUIPMENT)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        base_dur = self.ui.equipmentDurability.value()
        include_horse = self.ui.groupBox.isChecked()
        name = self.ui.equipmentName.text()
        is_new = name not in self.project.equipment

        self.project.equipment[name] = {
            "name": name,
            "displayName": self.ui.equipmentDisplayName.text(),
            "armor": {
                "helmet":     self.ui.helmetArmor.value(),
                "chestplate": self.ui.chestplateArmor.value(),
                "leggings":   self.ui.leggingsArmor.value(),
                "boots":      self.ui.bootsArmor.value(),
                "horse_armor":self.ui.horseArmor.value(),
            },
            "toughness":    self.ui.equipmentArmorToughness.value(),
            "kb_resistance": self.ui.equipmentKBResistance.value(),
            "durability": {
                "helmet":     int(0.6875 * base_dur),
                "chestplate": int(base_dur),
                "leggings":   int(0.9375 * base_dur),
                "boots":      int(0.8125 * base_dur),
                "horse_armor": 1,
            },
            "itemTextures":  dict(self.project.equipment_textures),
            "modelTextures": dict(self.project.equipment_models),
            "includeHorse":  "true" if include_horse else "false",
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("equipment", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.equipment[name]
        self.clear()

        self.ui.equipmentDisplayName.setText(props["displayName"])
        self.ui.equipmentName.setText(props["name"])
        self.ui.helmetArmor.setValue(props["armor"]["helmet"])
        self.ui.chestplateArmor.setValue(props["armor"]["chestplate"])
        self.ui.leggingsArmor.setValue(props["armor"]["leggings"])
        self.ui.bootsArmor.setValue(props["armor"]["boots"])
        self.ui.equipmentArmorToughness.setValue(props["toughness"])
        self.ui.equipmentKBResistance.setValue(props["kb_resistance"])
        self.ui.equipmentDurability.setValue(props["durability"]["chestplate"])
        self.ui.groupBox.setChecked(props["includeHorse"] == "true")

        self.project.equipment_textures = dict(props["itemTextures"])
        self.project.equipment_models = dict(props["modelTextures"])

        for slot_name, proj_key, label_attr in _ITEM_SLOTS:
            path = self.project.equipment_textures.get(proj_key)
            if path:
                self._show_pixmap(getattr(self.ui, label_attr), path)

        for _, proj_key, label_attr in _MODEL_SLOTS:
            path = self.project.equipment_models.get(proj_key)
            if path:
                self._show_pixmap(getattr(self.ui, label_attr), path)

        self.ui.elementEditor.setCurrentIndex(ElementPage.EQUIPMENT)

    def clear(self):
        FieldResetter.clear_line_edits(self.ui.equipmentName, self.ui.equipmentDisplayName)
        FieldResetter.clear_labels(
            self.ui.chestplateModelLabel, self.ui.leggingsModelLabel,
            self.ui.helmetItemLabel, self.ui.chestplateItemLabel,
            self.ui.leggingsItemLabel, self.ui.bootsItemLabel,
            self.ui.horseArmorItemLabel, self.ui.horseArmorModelLabel,
        )
        FieldResetter.reset_spin_boxes(
            self.ui.helmetArmor, self.ui.chestplateArmor,
            self.ui.leggingsArmor, self.ui.bootsArmor,
            self.ui.horseArmor, self.ui.equipmentArmorToughness,
            self.ui.equipmentKBResistance, self.ui.equipmentDurability,
        )
        self.project.equipment_textures = {}
        self.project.equipment_models = {}

    # ── Texture picking ───────────────────────────────────────────────────

    def _pick_item_texture(self, proj_key: str, label, path: str = None):
        if path is None:
            path = self._pick_file("Open Texture", "PNG Files (*.png)")
            if not path:
                return
        dest = self._copy_asset(path, "equipment")
        self.project.equipment_textures[proj_key] = dest
        self._show_pixmap(label, dest)

    def _pick_model_texture(self, proj_key: str, label, path: str = None):
        if path is None:
            path = self._pick_file("Open Texture", "PNG Files (*.png)")
            if not path:
                return
        dest = self._copy_asset(path, "equipment")
        self.project.equipment_models[proj_key] = dest
        self._show_pixmap(label, dest)

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.equipmentName, "abcdefghijklmnopqrstuvwxyz _-!0123456789", "Equipment Name"
        ):
            return False
        if not FieldValidator.validate_text_field(
            self.ui.equipmentDisplayName,
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789",
            "Display Name",
        ):
            return False
        required = ["helmet", "chestplate", "leggings", "boots"]
        for slot in required:
            if not self.project.equipment_textures.get(slot):
                alert(f"Item Texture: {slot.capitalize()} is empty!")
                return False
        if not self.project.equipment_models.get("h"):
            alert("Model Texture: Humanoid is empty!")
            return False
        if not self.project.equipment_models.get("h_l"):
            alert("Model Texture: Humanoid Leggings is empty!")
            return False
        if self.ui.groupBox.isChecked():
            if not self.project.equipment_textures.get("horseArmor"):
                alert("Item Texture: Horse is empty!")
                return False
            if not self.project.equipment_models.get("horseArmor"):
                alert("Model Texture: Horse is empty!")
                return False
        return True
