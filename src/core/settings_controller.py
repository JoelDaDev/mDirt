from PySide6.QtGui import QFont, Qt
from utils.enums import ElementPage
from utils.alert import alert
from pathlib import Path

class SettingsController:
    def __init__(self, app, ui, settings, autoSaveTimer, mainDirectory):
        self.app = app
        self.ui = ui
        self.settings = settings
        self.autoSaveTimer = autoSaveTimer
        self.mainDirectory = mainDirectory
        self.connectEvents()
    
    def connectEvents(self):
        self.ui.settingsApplyButton.clicked.connect(self.saveSettings)
        self.ui.settingsRestoreDefaultsButton.clicked.connect(self.restoreSettings)
        self.ui.settingsCancelButton.clicked.connect(self.cancelSettings)

    def loadThemes(self, path):
            self.themes = {}
            folder = Path(path)
            for file_path in folder.glob("*.qss"):
                self.themes[file_path.name.removesuffix('.qss').replace('_', ' ').capitalize()] = str(file_path.absolute())

    def openSettings(self):
        self.refreshSettings()
        self.ui.elementEditor.setCurrentIndex(ElementPage.SETTINGS)
    
    def saveSettings(self):
        self.settings.set('general', 'auto_save_interval', self.ui.settingsAutoSaveInt.currentText())
        self.settings.set('general', 'open_last_project', self.ui.settingsOpenLastCheckbox.isChecked())
        self.settings.set('general', 'workspace_path', self.ui.settingsWorkspacePathButton.text())
        self.settings.set('general', 'language', self.ui.settingsLanguageCombo.currentText())
        self.settings.set('appearance', 'theme', self.ui.settingsThemeCombo.currentText())
        self.settings.set('appearance', 'font_size', self.ui.settingsFontSizeSlider.value())
        self.settings.set('appearance', 'show_tips', self.ui.settingsTipsCheckbox.isChecked())
        self.settings.set('editor', 'confirm_deletes', self.ui.settingsConfirmElementDeleteCheckbox.isChecked())
        self.settings.set('editor', 'enable_experiments', self.ui.settingsExperimentsCheckbox.isChecked())
        self.settings.set('file_export', 'default_export_location', self.ui.settingsDefaultExportButton.text())
        self.settings.set('file_export', 'pack_format_override', self.ui.settingsPackFormatOverride.text())
        self.settings.set('file_export', 'verbose_logging', self.ui.settingsVerboseLoggingCheckbox.isChecked())
        self.settings.set('network', 'check_updates', self.ui.settingsCheckUpdatesCheckbox.isChecked())
        self.settings.set('network', 'custom_update_url', self.ui.settingsUpdateURL.text())
        self.settings.set('network', 'get_betas', self.ui.settingsBetaUpdatesCheckbox.isChecked())

        self.settings.save_settings()
        self.refreshSettings()

        alert("Settings updated!")

    def restoreSettings(self):
        self.settings.reset_to_defaults()
        self.refreshSettings()
        alert("Settings have been restored to defaults!")

    def cancelSettings(self):
        self.ui.elementEditor.setCurrentIndex(ElementPage.HOME)

    def refreshSettings(self):
        self.loadThemes(self.mainDirectory / 'assets' / 'themes')
        self.ui.settingsThemeCombo.clear()
        for theme in self.themes:
            self.ui.settingsThemeCombo.addItem(theme)
        
        self.ui.settingsThemeCombo.addItem('Dark')
        self.ui.settingsThemeCombo.addItem('Light')

        self.ui.settingsAutoSaveInt.setCurrentText(self.settings.get('general', 'auto_save_interval'))
        self.ui.settingsOpenLastCheckbox.setChecked(self.settings.get('general', 'open_last_project'))
        self.ui.settingsWorkspacePathButton.setText(self.settings.get('general', 'workspace_path'))
        self.ui.settingsLanguageCombo.setCurrentText(self.settings.get('general', 'language'))
        self.ui.settingsThemeCombo.setCurrentText(self.settings.get('appearance', 'theme'))
        self.ui.settingsFontSizeSlider.setValue(self.settings.get('appearance', 'font_size'))
        self.ui.settingsTipsCheckbox.setChecked(self.settings.get('appearance', 'show_tips'))
        self.ui.settingsConfirmElementDeleteCheckbox.setChecked(self.settings.get('editor', 'confirm_deletes'))
        self.ui.settingsExperimentsCheckbox.setChecked(self.settings.get('editor', 'enable_experiments'))
        self.ui.settingsDefaultExportButton.setText(self.settings.get('file_export', 'default_export_location'))
        self.ui.settingsPackFormatOverride.setText(self.settings.get('file_export', 'pack_format_override'))
        self.ui.settingsVerboseLoggingCheckbox.setChecked(self.settings.get('file_export', 'verbose_logging'))
        self.ui.settingsCheckUpdatesCheckbox.setChecked(self.settings.get('network', 'check_updates'))
        self.ui.settingsUpdateURL.setText(self.settings.get('network', 'custom_update_url'))
        self.ui.settingsBetaUpdatesCheckbox.setChecked(self.settings.get('network', 'get_betas'))

        self.setAutoSaveInterval()
        self.workspacePath = self.settings.get('general', 'workspace_path')
        self.app.setFont(QFont("Segoe UI", self.settings.get('appearance', 'font_size')))
        theme = self.settings.get('appearance', 'theme')
        self.app.setStyleSheet("QPushButton:flat{background-color: transparent; border: 2px solid black;}")
        if theme == "Dark":
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
            self.app.setStyle('Fusion')
        elif theme == "Light":
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)
            self.app.setStyle('Fusion')
        elif theme in self.themes.keys():
            themePath = self.themes[theme]
            with open(themePath, 'r') as f: # Add error checking here
                themeQSS = f.read()
                self.app.setStyleSheet(themeQSS)

    def disableUnusedSettings(self):
        self.ui.settingsLanguageCombo.setDisabled(True)
        self.ui.settingsExperimentsCheckbox.setDisabled(True)
        self.ui.settingsPackFormatOverride.setDisabled(True)
        self.ui.settingsUpdateURL.setDisabled(True)

    def setAutoSaveInterval(self):
        mode = self.settings.get('general', 'auto_save_interval').lower()
        if mode == "1 minute":
            self.autoSaveTimer.start(60 * 1000)
        elif mode == "5 minutes":
            self.autoSaveTimer.start(5 * 60 * 1000)
        elif mode == "off":
            self.autoSaveTimer.stop()
