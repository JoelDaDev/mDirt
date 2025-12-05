import datetime
import json
import os
import requests
import string
import string

from PySide6.QtWidgets import QWidget, QTreeWidgetItem, QMessageBox

from utils.field_validator import FieldValidator
from utils.enums import ElementPage
from utils.alert import alert

import ui.load_project as load_project

from module import ModuleDownloader

from utils.const import *

class ProjectManager():
    def __init__(self, ui, mainDirectory):
        super().__init__()
        self.ui = ui
        self.mainDirectory = mainDirectory

    #######################
    # SETUP PROJECT       #
    #######################

    def pullSupportedVersions(self, remote=True):
        verPath = self.mainDirectory / 'lib' / 'version_list.json'
        with open(verPath, 'r') as f:
            versionsa = json.load(f)
        versions = versionsa["versions"]

        if remote == False:
            self.version_json = versionsa
            self.supportedVersions = versions
            return

        self.ui.statusbar.showMessage("Pulling version list...", 2000)
        version_url = f'{LIB_URL}/version_list.json'
        
        try:
            response = requests.get(version_url, timeout=5)
            response.raise_for_status()

            data = response.json()
            self.version_json = data
            supportedVersions = data.get("versions", [])

        except requests.exceptions.RequestException as e:
            alert(f'Failed to download supported versions. Error: {e}\n\nPlease relaunch mDirt and try again. If the problem persists, report it here:\n{ISSUE_URL}')
        except ValueError:
            alert(f'Received invalid JSON from server.\n\nPlease try again or report the issue:\n{ISSUE_URL}')
        
        merged = {item: 'online' for item in supportedVersions}
        merged.update({item: 'local' for item in versions})
        self.supportedVersions = merged

    def installVersionsJson(self):
        path = self.mainDirectory / 'lib' / 'version_list.json'
        with open(path, 'w') as f:
            json.dump(self.version_json, f)

    def openProjectMenu(self):
        self.pullSupportedVersions()                   # Pulls the supported version list from the server.

        self.ui.packVersion.clear()
        for version, source in self.supportedVersions.items():
            label = f"🌐 {version}" if source == "online" else version
            self.ui.packVersion.addItem(label)     # Adds the versions to the dropdown.

        self.ui.elementEditor.setCurrentIndex(ElementPage.PROJECT_SETUP)
        self.unsavedChanges = True
    
    def validatePackDetails(self):
        if not FieldValidator.validate_text_field(self.ui.packName, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-!0123456789", "Name"):
            return 0
        if not FieldValidator.validate_text_field(self.ui.packNamespace, "abcdefghijklmnopqrstuvwxyz_0123456789", "Namespace"):
            return 0
        if not FieldValidator.validate_text_field(self.ui.packDescription, string.printable, "Description"):
            return 0
        if not FieldValidator.validate_text_field(self.ui.packAuthor, "abcdefghijklmnopqrstuvwxyz_0123456789", "Author"):
            return 0

        return 1

    def pullData(self, remote=True):
        self.ui.statusbar.showMessage("Pulling version data file...", 2000)
        version = self.packDetails["version"]
        local_path = self.mainDirectory / 'lib' / f'{version}_data.json'
        url = f'{LIB_URL}/{version}_data.json'

        if not os.path.exists(local_path):
            response = requests.get(url)
            if response.status_code == 200:
                os.makedirs("lib", exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(response.content)
            else:
                alert(f'Failed to download data file for version {version}. (HTTP {response.status_code}). \nCheck your internet connection, and relaunch mDirt. If the issue persists, report it here:\n{ISSUE_URL}')

            try: # Opens the JSON to ensure it is not corrupted.
                with open(local_path, "r") as f:
                    json.load(f)
            except json.JSONDecodeError:
                os.remove(local_path)
                alert(f'Downloaded data file is corrupt or invalid JSON.\nCheck your internet connection, and relaunch mDirt. If the issue persists, report it here:\n{ISSUE_URL}')
        
            self.grabModule()

    def grabModule(self):
        self.ui.statusbar.showMessage("Pulling version module...", 2000)
        version = f'v{self.packDetails["version"].replace(".", "_")}'
        dir = self.mainDirectory / 'src' / 'generation'
        self.moduleGrab = ModuleDownloader(target_dir=dir)
        self.moduleGrab.download_and_extract(version)
        
    def newProject(self):
        if self.validatePackDetails() == 0: return      # Make sure all fields aren't empty and only contain valid characters.
        
        if '🌐' in self.ui.packVersion.currentText():
            remote = True
        else: remote = False

        if remote:
            getRemote = QMessageBox.question(
                self,
                "Confirm Remote Download",
                "The version you have selected is not installed. Would you like to install it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if getRemote == QMessageBox.Yes:
                self.packDetails = {
                    "name": self.ui.packName.text(),
                    "namespace": self.ui.packNamespace.text(),
                    "description": self.ui.packDescription.text(),
                    "author": self.ui.packAuthor.text(),
                    "version": self.ui.packVersion.currentText().removeprefix('🌐 ')
                }

                self.installVersionsJson()
                self.pullData()
                self.setupProjectData()

                self.saveProjectAs()
                self.ui.menuNew_Element.setEnabled(True) # Enable the Element buttons so user can add things to their pack
                self.ui.menuTools.setEnabled(True)

                self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
                self.ui.textEdit.setHtml(f'<h1>Welcome to mDirt. Create a new Element to get started.</h1>')
            
            else:
                QMessageBox.information(self, 'Remote Download Cancelled',
                                        'Remote Download Cancelled. Please select a different version.')

        else:
            self.packDetails = {
                    "name": self.ui.packName.text(),
                    "namespace": self.ui.packNamespace.text(),
                    "description": self.ui.packDescription.text(),
                    "author": self.ui.packAuthor.text(),
                    "version": self.ui.packVersion.currentText()
                }
            self.setupProjectData()
            self.saveProjectAs()
            self.ui.menuNew_Element.setEnabled(True) # Enable the Element buttons so user can add things to their pack
            self.ui.menuTools.setEnabled(True)
            self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)
            self.ui.textEdit.setHtml(f'<h1>Welcome to mDirt. Create a new Element to get started.</h1>')

    def setupProjectData(self):
        with open(f'{self.mainDirectory}/lib/{self.packDetails["version"]}_data.json', "r") as f:
            self.data = json.load(f)
        
        self.dataFormat = self.version_json["dataformat"][self.packDetails["version"]]
        self.resourceFormat = self.version_json["resourceformat"][self.packDetails["version"]]

        self.ui.menuNew_Element.setEnabled(True)
        self.ui.menuTools.setEnabled(True)

        self.blocks = {}
        self.items = {}
        self.recipes = {}
        self.paintings = {}
        self.structures = {}
        self.equipment = {}

        self.exists = {}

        try:
            self.blocks_tree
        except:
            self.blocks_tree = QTreeWidgetItem(self.ui.elementViewer, ["Blocks"])
            self.items_tree = QTreeWidgetItem(self.ui.elementViewer, ["Items"])
            self.recipes_tree = QTreeWidgetItem(self.ui.elementViewer, ["Recipes"])
            self.paintings_tree = QTreeWidgetItem(self.ui.elementViewer, ["Paintings"])
            self.structures_tree = QTreeWidgetItem(self.ui.elementViewer, ["Structures"])
            self.equipment_tree = QTreeWidgetItem(self.ui.elementViewer, ["Equipment"])

        self.blockTexture = {}
        self.itemTexture = None
        self.recipe = {}
        self.paintingTexture = None
        self.structure = None
        self.equipmentTexture = {}
        self.equipmentModel = {}

        self.header = f"""#####################################
#   This File Was Created By mDirt  #
#               v{APP_VERSION}              #
#    Copyright 2025 by JoelDaDev    #
#####################################\n"""

    #######################
    # SAVE / LOAD         #
    #######################
    
    def saveProject(self):
        self.saveProjectAs()

    def saveProjectAs(self):
        self.ui.statusbar.showMessage("Saving...", 2000)
        if self.workspacePath == 'default':
            projectDirectory = self.mainDirectory / 'workspaces' / f'{self.packDetails["namespace"]}'
        else:
            if os.path.exists(self.workspacePath):
                projectDirectory = self.workspacePath
            else:
                projectDirectory = self.mainDirectory / 'workspaces' / f'{self.packDetails["namespace"]}'
        self.settings.set('data', 'last_project_path', str(projectDirectory))
        self.settings.set('data', 'last_project_namespace', self.packDetails["namespace"])
        self.settings.save_settings()
        
        os.makedirs(projectDirectory, exist_ok=True)

        with open(projectDirectory / 'project.dat', 'w') as file:
            data = {
            "app_version": APP_VERSION,
            "metadata": {
                "last_edited": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            "packDetails": self.packDetails
        }
            json.dump(data, file, indent=4)
            
        with open(projectDirectory / 'blocks.json', 'w') as file:
            json.dump(self.blocks, file, indent=4)
        with open(projectDirectory / 'items.json', 'w') as file:
            json.dump(self.items, file, indent=4)
        with open(projectDirectory / 'recipes.json', 'w') as file:
            json.dump(self.recipes, file, indent=4)
        with open(projectDirectory / 'paintings.json', 'w') as file:
            json.dump(self.paintings, file, indent=4)
        with open(projectDirectory / 'structures.json', 'w') as file:
            json.dump(self.structures, file, indent=4)
        with open(projectDirectory / 'equipment.json', 'w') as file:
            json.dump(self.equipment, file, indent=4)
        
        os.makedirs(projectDirectory / 'assets', exist_ok=True)
        os.makedirs(projectDirectory / 'assets' / 'blocks', exist_ok=True)
        os.makedirs(projectDirectory / 'assets' / 'items', exist_ok=True)
        os.makedirs(projectDirectory / 'assets' / 'paintings', exist_ok=True)
        os.makedirs(projectDirectory / 'assets' / 'structures', exist_ok=True)
        os.makedirs(projectDirectory / 'assets' / 'equipment', exist_ok=True)

        manifestPath = self.mainDirectory / 'workspaces' / 'manifest.json'

        # Load existing manifest if it exists, otherwise start fresh
        if os.path.exists(manifestPath):
            with open(manifestPath, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {"workspaces": []}

        # Add current workspace if it's not already listed
        namespace = self.packDetails["namespace"]
        if namespace not in manifest["workspaces"]:
            manifest["workspaces"].append(namespace)
            with open(manifestPath, 'w') as f:
                json.dump(manifest, f, indent=4)
        
        self.unsavedChanges = False
        
    def loadProjectUI(self):
        self.projectList = QWidget()
        self.projectForm = load_project.Ui_Form()
        self.projectForm.setupUi(self.projectList)

        manifest_path = self.mainDirectory / 'workspaces' / 'manifest.json'
        projects = []

        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                if "workspaces" in manifest and isinstance(manifest["workspaces"], list):
                    projects = manifest["workspaces"]
            except json.JSONDecodeError:
                alert("There was an error reading the manifest.json!\nIt is either missing or malformed.")

        self.projectForm.listWidget.clear()
        self.projectForm.listWidget.addItems(projects)

        self.projectForm.pushButton.clicked.connect(lambda: self.loadProject(self.projectForm.listWidget.item(self.projectForm.listWidget.currentRow()).text()))

        self.projectList.show()

    def loadProject(self, projectNamespace):
        if projectNamespace == "":
            alert("Please select a valid project!")
            return
        
        self.ui.statusbar.showMessage("Loading Project...", 2000)

        projectDirectory = self.mainDirectory / 'workspaces' / f'{projectNamespace}'
        if not os.path.exists(projectDirectory):
            alert("This project doesn't exist or is corrupted!")
            return
        
        with open(projectDirectory / 'project.dat', 'r') as file:
            data = json.load(file)
            self.packDetails = data["packDetails"]
        if data["app_version"] != APP_VERSION:
            alert("Warning: This project was created with a different version of the app, and may cause crashes or corruption!")
        
        self.pullSupportedVersions(remote=False)
        self.pullData(remote=False)
        self.setupProjectData()

        with open(projectDirectory / 'blocks.json', 'r') as file:
            self.blocks = json.load(file)
        with open(projectDirectory / 'items.json', 'r') as file:
            self.items = json.load(file)
        with open(projectDirectory / 'recipes.json', 'r') as file:
            self.recipes = json.load(file)
        with open(projectDirectory / 'paintings.json', 'r') as file:
            self.paintings = json.load(file)
        with open(projectDirectory / 'structures.json', 'r') as file:
            self.structures = json.load(file)
        with open(projectDirectory / 'equipment.json', 'r') as file:
            self.equipment = json.load(file)
        
        try:
            self.projectList.close()
        except:
            pass
       
        for item in self.blocks:
            QTreeWidgetItem(self.blocks_tree, [self.blocks[item]["name"]])
        
        for item in self.items:
            QTreeWidgetItem(self.items_tree, [self.items[item]["name"]])
        
        for item in self.recipes:
            QTreeWidgetItem(self.recipes_tree, [self.recipes[item]["name"]])
        
        for item in self.paintings:
            QTreeWidgetItem(self.paintings_tree, [self.paintings[item]["name"]])
        
        for item in self.structures:
            QTreeWidgetItem(self.structures_tree, [self.structures[item]["name"]])
        
        for item in self.equipment:
            QTreeWidgetItem(self.equipment_tree, [self.equipment[item]["name"]])
    