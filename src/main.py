"""
mDirt — Minecraft Datapack Editor
Entry point and main window.

The window is intentionally thin: it owns the controllers and wires signals.
All element logic lives in src/controllers/, all data in src/models/project.py.
"""
import importlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from controllers.archetype import ArchetypeController
from controllers.block import BlockController
from controllers.equipment import EquipmentController
from controllers.item import ItemController
from controllers.painting import PaintingController
from controllers.recipe import RecipeController
from controllers.structure import StructureController

from core.project_manager import ProjectManager
from core.settings_controller import SettingsController

from generation.text_generator import TextGenerator
from generation.potion_generator import PotionGenerator, PotionEffectWidget, PotionColorPicker

from settings import SettingsManager
from ui.ui import Ui_MainWindow
from utils.alert import alert
from utils.const import APP_VERSION, OBFUSCATE_PROPERTY, MINECRAFT_COLORS
from utils.enums import ElementPage


class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ── Paths ─────────────────────────────────────────────────────────
        if getattr(sys, "frozen", False):
            self.main_dir = Path(sys._MEIPASS)
        else:
            self.main_dir = Path(__file__).resolve().parent.parent

        # ── Core services ─────────────────────────────────────────────────
        self.settings = SettingsManager()
        self.auto_save_timer = QTimer(self)
        self.settings_ctrl = SettingsController(
            QApplication.instance(), self.ui, self.settings,
            self.auto_save_timer, self.main_dir,
        )
        self.pm = ProjectManager(self.ui, self.main_dir, self.settings)

        # ── Logging ───────────────────────────────────────────────────────
        self._setup_logging()

        # ── UI bootstrap ──────────────────────────────────────────────────
        self.ui.menuNew_Element.setEnabled(False)
        self.ui.menuTools.setEnabled(False)
        self.settings_ctrl.disableUnusedSettings()
        self.settings_ctrl.refreshSettings()

        os.makedirs(self.main_dir / "workspaces", exist_ok=True)
        self.settings_ctrl.loadThemes(self.main_dir / "assets" / "themes")
        self._load_fonts()
        self._load_welcome_screen()

        icon = self.main_dir / "assets" / "icon.png"
        self.setWindowIcon(QIcon(str(icon)))

        # ── Controllers ───────────────────────────────────────────────────
        project = self.pm.project
        md = self.main_dir
        self.block_ctrl    = BlockController(self.ui, project, md)
        self.item_ctrl     = ItemController(self.ui, project, md)
        self.recipe_ctrl   = RecipeController(self.ui, project, md)
        self.painting_ctrl = PaintingController(self.ui, project, md)
        self.struct_ctrl   = StructureController(self.ui, project, md)
        self.equip_ctrl    = EquipmentController(self.ui, project, md)
        self.arch_ctrl     = ArchetypeController(self.ui, project, md)

        # ── Tools ─────────────────────────────────────────────────────────
        family = QFontDatabase.applicationFontFamilies(self._font_ids[0])[0]
        self.minecraft_font = QFont(family, 12)
        self.text_gen = TextGenerator(self.ui, OBFUSCATE_PROPERTY, MINECRAFT_COLORS)
        self.potion_gen: PotionGenerator | None = None
        self._effect_widgets: list = []

        # ── Signal wiring ─────────────────────────────────────────────────
        self._connect_signals()

        # ── Restore last session ──────────────────────────────────────────
        self.pm.update_versioned_elements()
        if self.settings.get("general", "open_last_project"):
            last_ns = self.settings.get("data", "last_project_namespace")
            last_path = self.settings.get("data", "last_project_path")
            if last_ns and os.path.exists(last_path):
                self.pm.load(last_ns)

        self.auto_save_timer.timeout.connect(self._save_project)
        self.settings_ctrl.setAutoSaveInterval()
        self._check_updates()

    # ── Setup helpers ─────────────────────────────────────────────────────

    def _setup_logging(self):
        logger = logging.getLogger("mDirt")
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh = logging.FileHandler("mdirt.log", mode="w")
        fh.setFormatter(fmt)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
        level = logging.DEBUG if self.settings.get("file_export", "verbose_logging") else logging.WARNING
        logger.setLevel(level)
        self.logger = logger

    def _load_fonts(self):
        font_dir = self.main_dir / "assets" / "fonts"
        self._font_ids = []
        for f in os.listdir(font_dir):
            if f.endswith(".otf"):
                fid = QFontDatabase.addApplicationFont(str(font_dir / f))
                if fid != -1:
                    self._font_ids.append(fid)

    def _load_welcome_screen(self):
        html_file = self.main_dir / "src" / "ui" / "welcome_screen.html"
        with open(html_file, "r") as f:
            self._welcome_html = f.read()
        if self.settings.get("appearance", "show_tips"):
            self.ui.textEdit.setHtml(self._welcome_html)
            self.ui.textEdit.setOpenExternalLinks(True)

    def _check_updates(self):
        if not self.settings.get("network", "check_updates"):
            return
        if sys.platform != "win32":
            return
        updater = self.main_dir.parent / "mDirtUpdater.exe"
        if updater.exists():
            subprocess.Popen(str(updater))
        else:
            alert("The mDirt Updater is missing! Reinstall mDirt to fix it.", "critical")

    # ── Signal connections ────────────────────────────────────────────────

    def _connect_signals(self):
        # Menu: project
        self.ui.actionNew_Project.triggered.connect(self.pm.open_project_menu)
        self.ui.createProjectButton.clicked.connect(self.pm.new_project)
        self.ui.actionOpen_Project.triggered.connect(self.pm.load_project_ui)
        self.ui.actionSave_2.triggered.connect(self._save_project)
        self.ui.actionExport_Project.triggered.connect(self._generate)
        self.ui.actionSettings.triggered.connect(self.settings_ctrl.openSettings)

        # Element tree
        self.ui.elementViewer.itemDoubleClicked.connect(self._on_element_clicked)

        # Menu: new element
        self.ui.actionBlock.triggered.connect(self.block_ctrl.new)
        self.ui.actionItem.triggered.connect(self.item_ctrl.new)
        self.ui.actionRecipe.triggered.connect(self.recipe_ctrl.new)
        self.ui.actionPainting.triggered.connect(self.painting_ctrl.new)
        self.ui.actionStructure.triggered.connect(self.struct_ctrl.new)
        self.ui.actionEquipmentSet.triggered.connect(self.equip_ctrl.new)
        self.ui.actionSulfurCubeArchetype.triggered.connect(self.arch_ctrl.new)

        # Tools
        self.ui.actionText_Generator.triggered.connect(self._open_text_generator)
        self.ui.actionPotion_Generator.triggered.connect(self._open_potion_generator)

        # Text generator
        self.ui.textGeneratorBold.clicked.connect(self.text_gen.tg_ToggleBold)
        self.ui.textGeneratorItalic.clicked.connect(self.text_gen.tg_ToggleItalic)
        self.ui.textGeneratorUnderline.clicked.connect(self.text_gen.tg_ToggleUnderline)
        self.ui.textGeneratorStrikethrough.clicked.connect(self.text_gen.tg_ToggleStrikethrough)
        self.ui.textGeneratorObfuscated.clicked.connect(self.text_gen.tg_ToggleObfuscate)
        self.ui.textGeneratorColor.clicked.connect(self.text_gen.tg_Color)
        self.ui.textGeneratorTextBox.textChanged.connect(self.text_gen.tg_UpdateTextComponentOutput)
        self.ui.textGeneratorCopy.clicked.connect(self.text_gen.tg_CopyOutput)
        self.ui.textGeneratorOutput.setReadOnly(True)

        # Potion generator
        self.ui.potionAddEffect.clicked.connect(self._add_potion_effect)
        self.ui.potionColor.clicked.connect(self._pick_potion_color)
        self.ui.potionGenerate.clicked.connect(self._generate_potion)
        self.ui.potionCopy.clicked.connect(self._copy_potion_output)
        self.ui.potionOutput.setReadOnly(True)

        # Settings path buttons
        self.ui.settingsWorkspacePathButton.clicked.connect(self._pick_workspace_dir)
        self.ui.settingsDefaultExportButton.clicked.connect(self._pick_export_dir)

    # ── Qt events ────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self.pm.project.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Exit anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            event.accept() if reply == QMessageBox.Yes else event.ignore()
        else:
            event.accept()

    # ── Element tree dispatcher ────────────────────────────────────────────

    def _on_element_clicked(self, item, column):
        parent = item.parent()
        if parent is None:
            return
        category = parent.text(column).lower()
        name = item.text(column)
        dispatch = {
            "blocks":     self.block_ctrl.edit,
            "items":      self.item_ctrl.edit,
            "recipes":    self.recipe_ctrl.edit,
            "paintings":  self.painting_ctrl.edit,
            "structures": self.struct_ctrl.edit,
            "equipment":  self.equip_ctrl.edit,
            "archetypes": self.arch_ctrl.edit,
        }
        handler = dispatch.get(category)
        if handler:
            handler(name)

    # ── Save ──────────────────────────────────────────────────────────────

    def _save_project(self):
        if self.pm.project.is_loaded:
            self.pm.save()

    # ── Settings path pickers ─────────────────────────────────────────────

    def _pick_workspace_dir(self):
        loc = QFileDialog.getExistingDirectory(self, "Select Workspace Directory", "")
        if loc:
            self.ui.settingsWorkspacePathButton.setText(loc)

    def _pick_export_dir(self):
        loc = QFileDialog.getExistingDirectory(self, "Select Export Directory", "")
        if loc:
            self.ui.settingsDefaultExportButton.setText(loc)

    # ── Pack generation ───────────────────────────────────────────────────

    def _generate(self):
        if not self.pm.project.is_loaded:
            alert("No project is open!")
            return

        self.ui.statusbar.showMessage("Exporting project…", 2000)
        project = self.pm.project
        version = project.pack_details.version.replace(".", "_")

        prefix = "src." if getattr(sys, "frozen", False) else ""
        GeneratorClass = importlib.import_module(
            f"{prefix}generation.v{version}.generator"
        ).Generator

        export_loc = self.settings.get("file_export", "default_export_location")
        if export_loc == "default":
            export_loc = self.main_dir / "exports"
            os.makedirs(export_loc, exist_ok=True)

        gen = GeneratorClass(
            APP_VERSION,
            project.pack_details.to_dict(),
            project.data_format,
            project.resource_format,
            project.header,
            project.blocks,
            project.items,
            project.recipes,
            project.paintings,
            project.mc_data,
            export_loc,
            project.structures,
            project.equipment,
            project.archetypes,
        )
        gen.generateDatapack()

        pack_name = project.pack_details.name
        dp_path = os.path.join(export_loc, pack_name)
        rp_path = os.path.join(export_loc, f"{pack_name} Resource Pack")

        shutil.make_archive(f"{dp_path} Data Pack", "zip", dp_path)
        shutil.make_archive(rp_path, "zip", rp_path)
        shutil.rmtree(dp_path)
        shutil.rmtree(rp_path)

        dp_dest = QFileDialog.getExistingDirectory(self, "Export Data Pack To:", "")
        rp_dest = QFileDialog.getExistingDirectory(self, "Export Resource Pack To:", "")
        shutil.move(f"{dp_path} Data Pack.zip", os.path.join(dp_dest, f"{pack_name} Data Pack.zip"))
        shutil.move(f"{rp_path}.zip", os.path.join(rp_dest, f"{pack_name} Resource Pack.zip"))

        alert("Pack generated successfully!")

    # ── Text generator ────────────────────────────────────────────────────

    def _open_text_generator(self):
        self.ui.elementEditor.setCurrentIndex(ElementPage.TEXT_GENERATOR)
        self.ui.textGeneratorTextBox.setFont(self.minecraft_font)
        self.ui.textGeneratorTextBox.setStyleSheet("background-color: #1e1e1e; color: white;")

    # ── Potion generator ──────────────────────────────────────────────────

    def _open_potion_generator(self):
        self.ui.potionEffectBox.clear()
        for effect in self.pm.project.mc_data.get("effects", []):
            self.ui.potionEffectBox.addItem(effect.replace("_", " ").capitalize())
        self.potion_gen = PotionGenerator()
        self._effect_widgets = []
        self.ui.elementEditor.setCurrentIndex(ElementPage.POTION_GENERATOR)

    def _add_potion_effect(self):
        if self.potion_gen is None:
            return
        effect_id = self.ui.potionEffectBox.currentText()
        if self.potion_gen.hasEffect(effect_id):
            QMessageBox.warning(self, "Duplicate", f"{effect_id} is already added.")
            return
        widget = PotionEffectWidget(effect_id, self._remove_potion_effect)
        pos = max(0, self.ui.verticalLayout_4.count() - 1)
        self.ui.verticalLayout_4.insertWidget(pos, widget)
        self._effect_widgets.append(widget)
        self.potion_gen.addEffect(effect_id)
        self.ui.potionScrollArea.ensureWidgetVisible(widget)

    def _remove_potion_effect(self, widget: PotionEffectWidget):
        if widget in self._effect_widgets:
            self._effect_widgets.remove(widget)
            self.potion_gen.removeEffect(widget.effectId)
            widget.deleteLater()

    def _pick_potion_color(self):
        color = PotionColorPicker.showColorDialog(self)
        if color is not None:
            self.potion_gen.setColor(color)
            self.ui.potionColor.setStyleSheet(PotionColorPicker.colorToStylesheet(color))

    def _generate_potion(self):
        if self.potion_gen is None:
            return
        self.potion_gen.setName(self.ui.potionName.text())
        self.potion_gen.setPotionType(self.ui.potionType.currentText())
        self.potion_gen.clearEffects()
        for w in self._effect_widgets:
            self.potion_gen.addEffect(w.getPotionEffect())
        self.ui.potionOutput.setText(self.potion_gen.generateCommand())

    def _copy_potion_output(self):
        QApplication.clipboard().setText(self.ui.potionOutput.text())


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Window()
    window.show()
    sys.exit(app.exec())
