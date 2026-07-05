"""
Handles all project file I/O and version management.
Contains no UI logic — receives a Project model and a UI reference only
for status-bar messages and the element-tree widget.
"""
import datetime
import json
import os
import string

import requests
from PySide6.QtWidgets import QWidget, QMessageBox, QTreeWidgetItem

from models.project import Project, PackDetails
from module import ModuleDownloader
from utils.alert import alert
from utils.const import API_URL, ISSUE_URL, APP_VERSION
from utils.field_validator import FieldValidator
from utils.enums import ElementPage


class ProjectManager:

    def __init__(self, ui, main_dir, settings):
        self.ui = ui
        self.main_dir = main_dir
        self.settings = settings
        self.project = Project()

    # ── Version management ────────────────────────────────────────────────

    def pull_supported_versions(self, remote: bool = True):
        ver_path = self.main_dir / "lib" / "version_list.json"
        with open(ver_path, "r") as f:
            local_json = json.load(f)
        local_versions = local_json["versions"]

        if not remote:
            self.project.version_json = local_json
            self._supported = local_versions
            return

        self.ui.statusbar.showMessage("Pulling version list…", 2000)
        supported = {}
        try:
            resp = requests.get(f"{API_URL}/version_list.json", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            self.project.version_json = data
            supported = data.get("versions", {})
        except requests.exceptions.RequestException as e:
            alert(f"Failed to fetch version list: {e}\n\nFalling back to local data.")
            self.project.version_json = local_json
            self._supported = local_versions
            return
        except ValueError:
            alert("Received invalid JSON from server.\n\nFalling back to local data.")
            self.project.version_json = local_json
            self._supported = local_versions
            return

        merged = {v: "online" for v in supported}
        merged.update({v: "local" for v in local_versions})
        self._supported = merged

    def pull_data(self):
        """Download (if needed) the MC data JSON for the current project version."""
        self.ui.statusbar.showMessage("Pulling version data…", 2000)
        version = self.project.pack_details.version
        local = self.main_dir / "lib" / f"{version}_data.json"

        if not local.exists():
            url = f"{API_URL}/{version}_data.json"
            resp = requests.get(url)
            if resp.status_code != 200:
                alert(
                    f"Failed to download data for version {version} (HTTP {resp.status_code}).\n"
                    f"Check your connection and try again."
                )
                return
            local.write_bytes(resp.content)
            try:
                json.loads(local.read_text())
            except json.JSONDecodeError:
                local.unlink()
                alert("Downloaded data file is corrupt. Try again or report this issue.")
                return
            self._grab_module()

        with open(local, "r") as f:
            self.project.mc_data = json.load(f)

    def _grab_module(self):
        self.ui.statusbar.showMessage("Pulling generator module…", 2000)
        version = f'v{self.project.pack_details.version.replace(".", "_")}'
        target = self.main_dir / "src" / "generation"
        downloader = ModuleDownloader(target_dir=str(target))
        downloader.download_and_extract(version)

    # ── Project setup UI ──────────────────────────────────────────────────

    def open_project_menu(self):
        self.pull_supported_versions(remote=True)
        self.ui.packVersion.clear()
        for version, source in self._supported.items():
            label = f"🌐 {version}" if source == "online" else version
            self.ui.packVersion.addItem(label)
        self.ui.elementEditor.setCurrentIndex(ElementPage.PROJECT_SETUP)

    def validate_pack_details(self) -> bool:
        ok = True
        ok &= FieldValidator.validate_text_field(
            self.ui.packName,
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789",
            "Name",
        )
        ok &= FieldValidator.validate_text_field(
            self.ui.packNamespace, "abcdefghijklmnopqrstuvwxyz_0123456789", "Namespace"
        )
        ok &= FieldValidator.validate_text_field(
            self.ui.packDescription, string.printable, "Description"
        )
        ok &= FieldValidator.validate_text_field(
            self.ui.packAuthor, "abcdefghijklmnopqrstuvwxyz_0123456789", "Author"
        )
        return ok

    def new_project(self):
        if not self.validate_pack_details():
            return

        raw_version = self.ui.packVersion.currentText()
        is_remote = raw_version.startswith("🌐")
        version = raw_version.removeprefix("🌐 ")

        if is_remote:
            answer = QMessageBox.question(
                None,
                "Confirm Remote Download",
                "That version is not installed locally. Download it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                QMessageBox.information(None, "Cancelled", "Select a different version.")
                return
            self._install_versions_json()

        self.project.pack_details = PackDetails(
            name=self.ui.packName.text(),
            namespace=self.ui.packNamespace.text(),
            description=self.ui.packDescription.text(),
            author=self.ui.packAuthor.text(),
            version=version,
        )
        self.pull_data()
        self._setup_project_data()
        self.save()

        self.ui.menuNew_Element.setEnabled(True)
        self.ui.menuTools.setEnabled(True)
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
        self.ui.textEdit.setHtml("<h1>Welcome to mDirt. Create a new Element to get started.</h1>")
        self.update_versioned_elements()

    def _install_versions_json(self):
        path = self.main_dir / "lib" / "version_list.json"
        with open(path, "w") as f:
            json.dump(self.project.version_json, f)

    # ── Project data initialisation ───────────────────────────────────────

    def _setup_project_data(self):
        version = self.project.pack_details.version
        data_path = self.main_dir / "lib" / f"{version}_data.json"
        with open(data_path, "r") as f:
            self.project.mc_data = json.load(f)

        ver_info = self.project.version_json["versions"][version]
        self.project.data_format = ver_info["data_format"]
        self.project.resource_format = ver_info["resource_format"]
        self.project.reset_elements()
        self.project.is_loaded = True
        self.project.header = (
            "#####################################\n"
            f"#   This File Was Created By mDirt  #\n"
            f"#              {APP_VERSION}              #\n"
            "#    Copyright 2026 by JoelDaDev    #\n"
            "#####################################\n"
        )

        self._ensure_trees()

    def _ensure_trees(self):
        """Create element-category tree items if they don't exist yet."""
        if self.project.trees:
            return
        categories = ["blocks", "items", "recipes", "paintings", "structures", "equipment", "archetypes"]
        for cat in categories:
            self.project.trees[cat] = QTreeWidgetItem(self.ui.elementViewer, [cat.capitalize()])

    def update_versioned_elements(self):
        self.ui.actionSulfurCubeArchetype.setEnabled(False)
        try:
            version = self.project.pack_details.version
            elements = self.project.version_json["versions"][version].get("enable_elements", [])
            self.ui.actionSulfurCubeArchetype.setEnabled("sulfur_cube_archetype" in elements)
        except (AttributeError, KeyError):
            pass

    # ── Save ──────────────────────────────────────────────────────────────

    def save(self):
        self.ui.statusbar.showMessage("Saving…", 2000)
        workspace = self.settings.get("general", "workspace_path")
        ns = self.project.pack_details.namespace

        if workspace == "default" or not os.path.exists(workspace):
            project_dir = self.main_dir / "workspaces" / ns
        else:
            project_dir = self.main_dir / workspace / ns

        project_dir.mkdir(parents=True, exist_ok=True)

        # project.dat
        with open(project_dir / "project.dat", "w") as f:
            json.dump(
                {
                    "app_version": APP_VERSION,
                    "metadata": {
                        "last_edited": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    },
                    "packDetails": self.project.pack_details.to_dict(),
                },
                f, indent=4,
            )

        # Element files
        for name, data in [
            ("blocks",     self.project.blocks),
            ("items",      self.project.items),
            ("recipes",    self.project.recipes),
            ("paintings",  self.project.paintings),
            ("structures", self.project.structures),
            ("equipment",  self.project.equipment),
            ("archetypes", self.project.archetypes),
        ]:
            with open(project_dir / f"{name}.json", "w") as f:
                json.dump(data, f, indent=4)

        # Asset directories
        for sub in ["blocks", "items", "paintings", "structures", "equipment", "archetypes"]:
            (project_dir / "assets" / sub).mkdir(parents=True, exist_ok=True)

        # Manifest
        manifest_path = self.main_dir / "workspaces" / "manifest.json"
        manifest = {"workspaces": []}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
            except json.JSONDecodeError:
                pass
        if ns not in manifest["workspaces"]:
            manifest["workspaces"].append(ns)
            manifest_path.write_text(json.dumps(manifest, indent=4))

        # Persist last project in settings
        self.settings.set("data", "last_project_path", str(project_dir))
        self.settings.set("data", "last_project_namespace", ns)
        self.settings.save_settings()

        self.project.unsaved_changes = False

    # ── Load ──────────────────────────────────────────────────────────────

    def load_project_ui(self):
        """Show the project picker popup."""
        from ui import load_project as lp
        self._picker = QWidget()
        form = lp.Ui_Form()
        form.setupUi(self._picker)

        manifest_path = self.main_dir / "workspaces" / "manifest.json"
        projects = []
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                projects = manifest.get("workspaces", [])
            except json.JSONDecodeError:
                alert("manifest.json is missing or corrupt.")

        form.listWidget.addItems(projects)

        def on_confirm():
            row = form.listWidget.currentRow()
            if row < 0 or form.listWidget.item(row) is None:
                alert("Please select a project first!")
                return
            ns = form.listWidget.item(row).text()
            self._picker.close()
            self.load(ns)

        form.pushButton.clicked.connect(on_confirm)
        self._picker.show()

    def load(self, namespace: str):
        if not namespace:
            alert("Please select a valid project!")
            return

        self.ui.statusbar.showMessage("Loading project…", 2000)
        project_dir = self.main_dir / "workspaces" / namespace
        if not project_dir.exists():
            alert("That project doesn't exist or is corrupted!")
            return

        with open(project_dir / "project.dat", "r") as f:
            dat = json.load(f)

        if dat.get("app_version") != APP_VERSION:
            alert("Warning: this project was created with a different version of mDirt and may behave unexpectedly.")

        self.project.pack_details = PackDetails.from_dict(dat["packDetails"])
        self.pull_supported_versions(remote=False)

        # Load mc_data without downloading
        version = self.project.pack_details.version
        data_path = self.main_dir / "lib" / f"{version}_data.json"
        with open(data_path, "r") as f:
            self.project.mc_data = json.load(f)

        ver_info = self.project.version_json["versions"][version]
        self.project.data_format = ver_info["data_format"]
        self.project.resource_format = ver_info["resource_format"]
        self.project.reset_elements()
        self.project.header = (
            "#####################################\n"
            f"#   This File Was Created By mDirt  #\n"
            f"#              {APP_VERSION}              #\n"
            "#    Copyright 2026 by JoelDaDev    #\n"
            "#####################################\n"
        )

        for attr in ["blocks", "items", "recipes", "paintings", "structures", "equipment", "archetypes"]:
            path = project_dir / f"{attr}.json"
            if path.exists():
                with open(path, "r") as f:
                    setattr(self.project, attr, json.load(f))

        self._ensure_trees()
        self._populate_trees()

        self.project.is_loaded = True
        self.project.unsaved_changes = False

        self.ui.menuNew_Element.setEnabled(True)
        self.ui.menuTools.setEnabled(True)
        self.update_versioned_elements()

    def _populate_trees(self):
        for cat in ["blocks", "items", "recipes", "paintings", "structures", "equipment", "archetypes"]:
            tree = self.project.trees.get(cat)
            if tree is None:
                continue
            tree.takeChildren()
            for name in getattr(self.project, cat):
                QTreeWidgetItem(tree, [name])
