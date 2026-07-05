from pathlib import Path

from PySide6.QtWidgets import QWidget, QTreeWidgetItem

from controllers.base import BaseElementController
from utils.enums import ElementPage
from utils.field_resetter import FieldResetter
from utils.field_validator import FieldValidator
from utils.alert import alert
from utils.const import APP_VERSION

from ui.ui_attribute import Ui_Form as AttributeForm


class AttributeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = AttributeForm()
        self.ui.setupUi(self)


class ArchetypeController(BaseElementController):

    def __init__(self, ui, project, main_dir: Path):
        super().__init__(ui, project, main_dir)
        self._attributes: dict = {}   # attribute name → AttributeWidget

        self.ui.archetypeAttributeButton.clicked.connect(self._add_attribute)
        self.ui.archetypeConfirmButton.clicked.connect(self.confirm)

    # ── Public interface ──────────────────────────────────────────────────

    def new(self):
        self.clear()
        self._populate_attributes()
        self._populate_damage_types()
        self.ui.elementEditor.setCurrentIndex(ElementPage.ARCHETYPE_GENERATOR)
        self.project.unsaved_changes = True

    def confirm(self) -> bool:
        if not self._validate():
            return False

        name = self.ui.archetypeName.text()
        is_new = name not in self.project.archetypes

        data = {
            "name": name,
            "item": self.ui.archetypeItem.text(),
            "buoyant": "true" if self.ui.archetypeBuoyant.isChecked() else "false",
            "vertical_power": self.ui.archetypeVerticalPower.value(),
            "horizontal_power": self.ui.archetypeHorizontalPower.value(),
        }

        if self.ui.archetypeExplosion.isChecked():
            data["explosion"] = {
                "causes_fire": "true" if self.ui.archetypeCausesFire.isChecked() else "false",
                "fuse": self.ui.archetypeFuse.value(),
                "power": self.ui.archetypePower.value(),
            }

        if self.ui.archetypeContactDamage.isChecked():
            data["contact_damage"] = {
                "amount": self.ui.archetypeAmount.value(),
                "attr_to_source": "true" if self.ui.archetypeAttributeToSource.isChecked() else "false",
                "damage_type": self.ui.archetypeDamgeType.currentText(),
            }

        attributes = {}
        author = self.project.pack_details.author
        for attr_name, widget in self._attributes.items():
            sign = -1 if widget.ui.attributeSign.currentText() == "-" else 1
            attributes[attr_name] = {
                "attribute": attr_name,
                "id": f"minecraft:{author}_{name}_{attr_name}",
                "amount": widget.ui.amountSpinBox.value() * sign,
                "operation": widget.ui.amountOperationBox.currentText(),
            }
        data["attributes"] = attributes

        self.project.archetypes[name] = data
        self.project.unsaved_changes = True

        if is_new:
            self._add_to_tree("archetypes", name)

        self.clear()
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        alert("Element added successfully!")
        return True

    def edit(self, name: str):
        props = self.project.archetypes[name]
        self.clear()
        self._populate_attributes()
        self._populate_damage_types()

        self.ui.archetypeName.setText(props["name"])
        self.ui.archetypeItem.setText(props["item"])
        self.ui.archetypeBuoyant.setChecked(props["buoyant"] == "true")
        self.ui.archetypeVerticalPower.setValue(props["vertical_power"])
        self.ui.archetypeHorizontalPower.setValue(props["horizontal_power"])

        has_explosion = "explosion" in props
        self.ui.archetypeExplosion.setChecked(has_explosion)
        if has_explosion:
            self.ui.archetypeCausesFire.setChecked(props["explosion"]["causes_fire"] == "true")
            self.ui.archetypeFuse.setValue(props["explosion"]["fuse"])
            self.ui.archetypePower.setValue(props["explosion"]["power"])

        has_contact = "contact_damage" in props
        self.ui.archetypeContactDamage.setChecked(has_contact)
        if has_contact:
            self.ui.archetypeAmount.setValue(props["contact_damage"]["amount"])
            self.ui.archetypeAttributeToSource.setChecked(
                props["contact_damage"]["attr_to_source"] == "true"
            )
            self.ui.archetypeDamgeType.setCurrentText(props["contact_damage"]["damage_type"])

        for attr_name, attr_data in props.get("attributes", {}).items():
            widget = self._create_attribute_widget(attr_name)
            widget.ui.amountSpinBox.setValue(abs(attr_data["amount"]))
            widget.ui.attributeSign.setCurrentText("-" if attr_data["amount"] < 0 else "+")
            widget.ui.amountOperationBox.setCurrentText(attr_data["operation"])

        self.ui.elementEditor.setCurrentIndex(ElementPage.ARCHETYPE_GENERATOR)

    def clear(self):
        FieldResetter.clear_labels(self.ui.archetypeName, self.ui.archetypeItem)
        FieldResetter.reset_spin_boxes(
            self.ui.archetypeHorizontalPower, self.ui.archetypeVerticalPower,
            self.ui.archetypeFuse, self.ui.archetypePower, self.ui.archetypeAmount,
        )
        FieldResetter.reset_combo_boxes(
            self.ui.archetypeDamgeType, self.ui.archetypeAttributeComboBox
        )
        FieldResetter.uncheck_boxes(
            self.ui.archetypeBuoyant, self.ui.archetypeExplosion,
            self.ui.archetypeContactDamage, self.ui.archetypeCausesFire,
            self.ui.archetypeAttributeToSource,
        )
        for widget in list(self._attributes.values()):
            self._remove_attribute_widget(widget)
        self._attributes = {}

    # ── Attribute widgets ─────────────────────────────────────────────────

    def _populate_attributes(self):
        self.ui.archetypeAttributeComboBox.clear()
        for attr in self.project.mc_data.get("attributes", []):
            self.ui.archetypeAttributeComboBox.addItem(attr)

    def _populate_damage_types(self):
        self.ui.archetypeDamgeType.clear()
        for dt in self.project.mc_data.get("damage_types", []):
            self.ui.archetypeDamgeType.addItem(dt)

    def _add_attribute(self):
        attr_name = self.ui.archetypeAttributeComboBox.currentText()
        if attr_name in self._attributes:
            return
        self._create_attribute_widget(attr_name)

    def _create_attribute_widget(self, attr_name: str) -> AttributeWidget:
        widget = AttributeWidget()
        widget.ui.attributeLabel.setText(attr_name)
        widget.ui.attributeRemove.clicked.connect(
            lambda: self._remove_named_attribute(attr_name, widget)
        )
        self._attributes[attr_name] = widget
        self.ui.attributeWidgetLayout.addWidget(widget)
        return widget

    def _remove_named_attribute(self, attr_name: str, widget: AttributeWidget):
        self._attributes.pop(attr_name, None)
        self._remove_attribute_widget(widget)

    def _remove_attribute_widget(self, widget: AttributeWidget):
        self.ui.attributeWidgetLayout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if not FieldValidator.validate_text_field(
            self.ui.archetypeName, "abcdefghijklmnopqrstuvwxyz _-!0123456789", "Archetype Name"
        ):
            return False
        if not FieldValidator.validate_text_field(
            self.ui.archetypeItem,
            "#abcdefghijklmnopqrstuvwxyz _-!0123456789:",
            "Archetype Item",
        ):
            return False
        return True
