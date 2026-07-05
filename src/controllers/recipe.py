from pathlib import Path

from PySide6.QtWidgets import QWidget, QTreeWidgetItem

from controllers.base import BaseElementController
import ui.select_item as select_item
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert


# Slot index → (label widget attr, category)
# Slots 0-8 are crafting inputs, 9 is crafting output.
# 10=smelting input, 11=smelting output, 12=stonecutting input, 13=stonecutting output.
_SLOT_LABELS = {
    0: "slot0", 1: "slot1", 2: "slot2",
    3: "slot3", 4: "slot4", 5: "slot5",
    6: "slot6", 7: "slot7", 8: "slot8",
    9: "slot9",
    10: "smeltingInput", 11: "smeltingOutput",
    12: "stoneCuttingInput", 13: "stoneCuttingOutput",
}
# Slots that accept custom elements as output
_OUTPUT_SLOTS = {9, 11, 13}


class RecipeController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self._pending_recipe: dict = {}
        self._popup: QWidget | None = None

        for slot_id in range(14):
            btn_attr = f"slot{slot_id}Button" if slot_id <= 9 else {
                10: "smeltingInputButton",
                11: "smeltingOutputButton",
                12: "stoneCuttingInputButton",
                13: "stoneCuttingOutputButton",
            }[slot_id]
            btn = getattr(self.ui, btn_attr)
            btn.clicked.connect(lambda checked=False, s=slot_id: self._open_item_picker(s))

        self.ui.recipeConfirmButton.clicked.connect(self.confirm)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.RECIPES)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        tab = self.ui.recipeSubTabs.tabText(self.ui.recipeSubTabs.currentIndex()).lower()
        if tab == "crafting":
            mode = "crafting"
            output_count = self.ui.slot9Count.value()
        elif tab == "smelting":
            mode = self.ui.smeltingModeBox.currentText().lower()
            output_count = ""
        else:
            mode = "stonecutting"
            output_count = self.ui.stoneCuttingCount.value()

        name = self.ui.recipeName.text()
        is_new = name not in self.project.recipes
        self.project.recipes[name] = {
            "name": name,
            "items": dict(self._pending_recipe),
            "outputCount": output_count,
            "exact": "true" if self.ui.exactlyRadio.isChecked() else "false",
            "shapeless": "true" if self.ui.shapelessRadio.isChecked() else "false",
            "type": mode,
        }
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("recipes", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.recipes[name]
        self.clear()

        self.ui.recipeName.setText(props["name"])
        self.ui.shapelessRadio.setChecked(props["shapeless"] == "true")
        self.ui.exactlyRadio.setChecked(props["exact"] == "true")

        count = props.get("outputCount") or 0
        count_int = int(count) if isinstance(count, (int, float)) else 0
        self.ui.slot9Count.setValue(count_int)
        self.ui.stoneCuttingCount.setValue(count_int)

        items = props.get("items", {})
        self._pending_recipe = {int(k): v for k, v in items.items()}
        for slot_id, label_attr in _SLOT_LABELS.items():
            label = getattr(self.ui, label_attr)
            label.setText(items.get(str(slot_id), ""))

        self.ui.elementEditor.setCurrentIndex(ElementPage.RECIPES)

    def clear(self):
        FieldResetter.clear_line_edits(
            self.ui.recipeName,
            self.ui.slot0, self.ui.slot1, self.ui.slot2,
            self.ui.slot3, self.ui.slot4, self.ui.slot5,
            self.ui.slot6, self.ui.slot7, self.ui.slot8,
            self.ui.slot9,
            self.ui.smeltingInput, self.ui.smeltingOutput,
            self.ui.stoneCuttingInput, self.ui.stoneCuttingOutput,
        )
        FieldResetter.reset_spin_boxes(self.ui.stoneCuttingCount, self.ui.slot9Count)
        FieldResetter.uncheck_boxes(self.ui.shapelessRadio, self.ui.exactlyRadio)
        self._pending_recipe = {}

    # ── Item picker popup ─────────────────────────────────────────────────

    def _open_item_picker(self, slot_id: int):
        self._popup = QWidget()
        form = select_item.Ui_Form()
        form.setupUi(self._popup)

        if slot_id in _OUTPUT_SLOTS:
            for name in self.project.blocks:
                form.itemsBox.addItem(name)
            for name in self.project.items:
                form.itemsBox.addItem(name)
            for equip_name, equip in self.project.equipment.items():
                for slot in ["helmet", "chestplate", "leggings", "boots", "horse_armor"]:
                    if equip["includeHorse"] != "true" and slot == "horse_armor":
                        continue
                    form.itemsBox.addItem(f'{equip["name"]}_{slot}')

        for item in self.project.mc_data.get("items", []):
            form.itemsBox.addItem(item)

        form.pushButton.clicked.connect(
            lambda: self._on_item_selected(slot_id, form.itemsBox.currentText())
        )
        self._popup.show()

    def _on_item_selected(self, slot_id: int, item: str):
        self._pending_recipe[slot_id] = item
        label_attr = _SLOT_LABELS[slot_id]
        getattr(self.ui, label_attr).setText(item)
        if self._popup:
            self._popup.close()
            self._popup = None

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.recipeName, "abcdefghijklmnopqrstuvwxyz_0123456789", "Recipe Name"
        ):
            return False
        tab = self.ui.recipeSubTabs.tabText(self.ui.recipeSubTabs.currentIndex()).lower()
        if tab == "crafting" and self.ui.slot9.text() == "":
            alert("Crafting recipes require an output in slot 9!")
            return False
        if tab == "smelting" and self.ui.smeltingOutput.text() == "":
            alert("Smelting recipes require an output!")
            return False
        if tab == "stonecutting" and self.ui.stoneCuttingOutput.text() == "":
            alert("Stonecutting recipes require an output!")
            return False
        return True
