"""
SavePlus - File versioning tool for Maya 2025 (Python 3 with PySide6)
Maya 2025 - Python 3 and PySide6 Compatible Version
"""

import re
import os
import time
import traceback
import json
from datetime import datetime
from maya import cmds, mel

from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, 
                              QLabel, QDialog, QLineEdit, QHBoxLayout,
                              QCheckBox, QFileDialog, QMainWindow, QMenuBar,
                              QMenu, QStatusBar, QGridLayout, QFrame,
                              QGroupBox, QComboBox, QStyle, QSizePolicy,
                              QTextEdit, QSplitter, QToolButton, QSpinBox,
                              QMessageBox, QFormLayout, QScrollArea,
                              QApplication, QTabWidget, QListWidget,
                              QListWidgetItem, QTableWidget, QTableWidgetItem,
                              QHeaderView, QToolTip, QPlainTextEdit)
from PySide6 import QtCore
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QAction, QColor
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# Constants
VERSION = "1.2.1"
UNIQUE_IDENTIFIER = "SavePlus_v1_ToolButton"

# Enable debug mode - logs errors to Maya script editor
DEBUG_MODE = True

def debug_print(message):
    """Print debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        print(f"[SavePlus Debug] {message}")

class LogRedirector:
    """A class to redirect Maya's script output to a QTextEdit widget"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.orig_stdout = None
        self.orig_stderr = None
    
    def write(self, message):
        if self.text_widget:
            self.text_widget.append(message.rstrip())
            self.text_widget.verticalScrollBar().setValue(self.text_widget.verticalScrollBar().maximum())
    
    def flush(self):
        pass
    
    def start_redirect(self):
        import sys
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def stop_redirect(self):
        import sys
        if self.orig_stdout and self.orig_stderr:
            sys.stdout = self.orig_stdout
            sys.stderr = self.orig_stderr

class AboutDialog(QDialog):
    """About dialog for SavePlus"""
    
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle("About SavePlus")
        self.setMinimumWidth(300)
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("SavePlus")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        
        version = QLabel(f"Version {VERSION}")
        version.setAlignment(Qt.AlignCenter)
        
        desc = QLabel(
            "SavePlus provides a simple way to increment your save files.\n"
            "Based on the original MEL script by Neal Singleton."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        
        examples = QLabel(
            "Examples:\n"
            "filename.mb → filename02.mb\n"
            "filename5.mb → filename6.mb\n"
            "filename00002.mb → filename00003.mb\n"
            "scene45_99.mb → scene45_100.mb"
        )
        examples.setWordWrap(True)
        examples.setAlignment(Qt.AlignCenter)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(10)
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(examples)
        layout.addStretch()
        layout.addWidget(close_button)
        
        self.setLayout(layout)

class TimedWarningDialog(QDialog):
    """Warning dialog for save reminders"""
    
    def __init__(self, parent=None, first_time=False):
        super(TimedWarningDialog, self).__init__(parent)
        self.setWindowTitle("Save Reminder")
        self.setMinimumWidth(350)
        self.disable_warnings = False
        
        layout = QVBoxLayout(self)
        
        message_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(32, 32))
        
        message_text = "It's been 15 minutes since your last save.\nWould you like to save your work now?"
        if first_time:
            message_text = "You've enabled save reminders. You'll be reminded to save every 15 minutes."
        message = QLabel(message_text)
        message.setWordWrap(True)
        
        message_layout.addWidget(icon_label)
        message_layout.addWidget(message, 1)
        
        self.disable_checkbox = None
        if first_time:
            self.disable_checkbox = QCheckBox("Disable these reminders")
            self.disable_checkbox.setChecked(False)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Now" if not first_time else "Got it")
        save_button.clicked.connect(self.accept)
        if not first_time:
            remind_later_button = QPushButton("Remind Me Later")
            remind_later_button.clicked.connect(self.reject)
            button_layout.addWidget(remind_later_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        
        layout.addLayout(message_layout)
        if self.disable_checkbox:
            layout.addWidget(self.disable_checkbox)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_disable_warnings(self):
        if self.disable_checkbox:
            return self.disable_checkbox.isChecked()
        return False

class NoteInputDialog(QDialog):
    """Dialog for entering version notes"""
    
    def __init__(self, parent=None):
        super(NoteInputDialog, self).__init__(parent)
        self.setWindowTitle("Version Notes")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        help_label = QLabel("Enter notes for this version (optional):")
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setMinimumHeight(100)
        
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save with Notes")
        save_button.clicked.connect(self.accept)
        skip_button = QPushButton("Skip Notes")
        skip_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(skip_button)
        
        layout.addWidget(help_label)
        layout.addWidget(self.text_edit)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_notes(self):
        return self.text_edit.toPlainText()

class ZurbriggStyleCollapsibleHeader(QWidget):
    """Header widget for the collapsible frame in Zurbrigg style"""
    
    def __init__(self, title, parent=None):
        super(ZurbriggStyleCollapsibleHeader, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)
        
        self.icon_label = QLabel("-")
        self.icon_label.setFixedWidth(15)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        self.title_label = QLabel(title)
        bold_font = QFont()
        bold_font.setBold(True)
        self.title_label.setFont(bold_font)
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), palette.mid().color())
        self.setPalette(palette)
        
        self.setFixedHeight(26)
        self.is_expanded = True
    
    def update_state(self, is_expanded):
        self.is_expanded = is_expanded
        self.icon_label.setText("-" if is_expanded else "+")
    
    def mousePressEvent(self, event):
        if self.parent():
            self.parent().toggle_content()
        super(ZurbriggStyleCollapsibleHeader, self).mousePressEvent(event)

class ZurbriggStyleCollapsibleFrame(QWidget):
    """
    A collapsible frame widget that maintains a fixed position in layouts.
    """
    
    toggled = QtCore.Signal()
    
    def __init__(self, title, parent=None, collapsed=True):
        super(ZurbriggStyleCollapsibleFrame, self).__init__(parent)
        self.collapsed = collapsed
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        
        self.header = ZurbriggStyleCollapsibleHeader(title, self)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.content_widget.setVisible(not collapsed)
        self.header.update_state(not collapsed)
        
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content_widget)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def toggle_content(self):
        self.collapsed = not self.collapsed
        self.header.update_state(not self.collapsed)
        self.content_widget.setVisible(not self.collapsed)
        if not self.collapsed:
            self.content_widget.setMaximumHeight(16777215)
        else:
            self.content_widget.setMaximumHeight(0)
        self.toggled.emit()
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.content_layout.addLayout(layout)
    
    def sizeHint(self):
        size = super(ZurbriggStyleCollapsibleFrame, self).sizeHint()
        if self.collapsed:
            size.setHeight(self.header.height())
        return size
    
    def is_collapsed(self):
        return self.collapsed
    
    def set_collapsed(self, collapsed):
        if self.collapsed != collapsed:
            self.toggle_content()

class VersionHistoryModel:
    """Class to manage version history data"""
    
    def __init__(self):
        self.history_file = os.path.join(cmds.internalVar(userAppDir=True), "saveplus_history.json")
        self.versions = self.load_history()
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            debug_print(f"Error loading version history: {e}")
            return {}
    
    def save_history(self):
        try:
            dirname = os.path.dirname(self.history_file)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(self.history_file, 'w') as f:
                json.dump(self.versions, f, indent=2)
        except Exception as e:
            debug_print(f"Error saving version history: {e}")
    
    def add_version(self, file_path, notes=""):
        base_path = os.path.normpath(file_path)
        base_name = os.path.basename(base_path)
        directory = os.path.dirname(base_path)
        match = re.search(r'(\D*?)(\d+)([^/\\]*?)$', base_name)
        if match:
            group_key = os.path.join(directory, match.group(1))
        else:
            group_key = directory
        if group_key not in self.versions:
            self.versions[group_key] = []
        version_info = {
            "path": base_path,
            "filename": base_name,
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes
        }
        self.versions[group_key].insert(0, version_info)
        if len(self.versions[group_key]) > 50:
            self.versions[group_key] = self.versions[group_key][:50]
        self.save_history()
        return version_info
    
    def get_recent_versions(self, count=10):
        all_versions = []
        for group, versions in self.versions.items():
            all_versions.extend(versions)
        sorted_versions = sorted(all_versions, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_versions[:count]
    
    def get_versions_for_file(self, file_path):
        base_path = os.path.normpath(file_path)
        directory = os.path.dirname(base_path)
        base_name = os.path.basename(base_path)
        match = re.search(r'(\D*?)(\d+)([^/\\]*?)$', base_name)
        if match:
            group_key = os.path.join(directory, match.group(1))
            if group_key in self.versions:
                return self.versions[group_key]
        for group, versions in self.versions.items():
            for version in versions:
                if version.get('path') == base_path:
                    return versions
        return []
    
    def export_history(self, file_path):
        try:
            with open(file_path, 'w') as f:
                f.write("SavePlus Version History Export\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for group, versions in self.versions.items():
                    f.write(f"Group: {group}\n")
                    f.write("-" * 80 + "\n")
                    for idx, version in enumerate(versions):
                        f.write(f"Version {idx + 1}: {version.get('filename')}\n")
                        f.write(f"Date: {version.get('date')}\n")
                        f.write(f"Path: {version.get('path')}\n")
                        notes = version.get('notes', '').strip()
                        if notes:
                            f.write("Notes:\n")
                            f.write(f"{notes}\n")
                        f.write("-" * 40 + "\n")
                    f.write("\n")
            return True
        except Exception as e:
            debug_print(f"Error exporting history: {e}")
            return False

class SavePlusUI(MayaQWidgetDockableMixin, QMainWindow):
    """SavePlus UI Class - Modern interface with menus and log display"""
    
    OPT_VAR_ASSIGNMENT_LETTER = "SavePlusAssignmentLetter"
    OPT_VAR_ASSIGNMENT_NUMBER = "SavePlusAssignmentNumber"
    OPT_VAR_LAST_NAME = "SavePlusLastName"
    OPT_VAR_FIRST_NAME = "SavePlusFirstName"
    OPT_VAR_VERSION_TYPE = "SavePlusVersionType"
    OPT_VAR_VERSION_NUMBER = "SavePlusVersionNumber"
    OPT_VAR_ENABLE_TIMED_WARNING = "SavePlusEnableTimedWarning"
    
    OPT_VAR_DEFAULT_FILETYPE = "SavePlusDefaultFiletype"
    OPT_VAR_AUTO_SAVE_INTERVAL = "SavePlusAutoSaveInterval"
    OPT_VAR_DEFAULT_SAVE_PATH = "SavePlusDefaultSavePath"
    OPT_VAR_PROJECT_PATH = "SavePlusProjectPath"
    OPT_VAR_FILE_EXPANDED = "SavePlusFileExpanded"
    OPT_VAR_NAME_EXPANDED = "SavePlusNameExpanded"
    OPT_VAR_LOG_EXPANDED = "SavePlusLogExpanded"
    
    OPT_VAR_ENABLE_AUTO_BACKUP = "SavePlusEnableAutoBackup"
    OPT_VAR_BACKUP_INTERVAL = "SavePlusBackupInterval"
    OPT_VAR_ADD_VERSION_NOTES = "SavePlusAddVersionNotes"
    
    def __init__(self, parent=None):
        try:
            super(SavePlusUI, self).__init__(parent)
            debug_print("Initializing SavePlus UI")
            
            self.setWindowTitle("SavePlus")
            self.setMinimumWidth(550)
            self.setMinimumHeight(450)
            
            self.auto_resize_enabled = True
            self.selected_directory = None
            self.version_history = VersionHistoryModel()
            
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(0)
            
            self.create_menu_bar()
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # Create header
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(10, 5, 10, 5)
            
            title_layout = QVBoxLayout()
            title_layout.setSpacing(0)
            title_layout.setContentsMargins(0, 0, 0, 0)
            
            title = QLabel("SavePlus")
            title_font = title.font()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title.setFont(title_font)
            title.setStyleSheet("color: #2980b9;")
            
            version_label = QLabel(f"v{VERSION}")
            version_label.setStyleSheet("color: #7f8c8d; font-size: 9px;")
            version_label.setAlignment(Qt.AlignLeft)
            
            title_layout.addWidget(title)
            title_layout.addWidget(version_label)
            
            description = QLabel("Increment and save your Maya files")
            description.setStyleSheet("color: #555555; font-size: 11px;")
            description.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            header_layout.addLayout(title_layout)
            header_layout.addStretch()
            header_layout.addWidget(description)
            
            header_container = QFrame()
            header_container.setFrameShape(QFrame.StyledPanel)
            header_container.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 4px; }")
            header_container.setLayout(header_layout)
            main_layout.addWidget(header_container)
            
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
            main_layout.addWidget(separator)
            main_layout.addSpacing(5)
            
            # Create Tab Widget and individual tabs with their layouts
            self.tab_widget = QTabWidget()
            
            self.saveplus_tab = QWidget()
            self.saveplus_layout = QVBoxLayout(self.saveplus_tab)
            self.saveplus_layout.setContentsMargins(8, 8, 8, 8)
            self.saveplus_layout.setSpacing(8)
            
            self.history_tab = QWidget()
            self.history_layout = QVBoxLayout(self.history_tab)
            self.history_layout.setContentsMargins(8, 8, 8, 8)
            self.history_layout.setSpacing(8)
            
            self.preferences_tab = QWidget()
            self.preferences_layout = QVBoxLayout(self.preferences_tab)
            self.preferences_layout.setContentsMargins(8, 8, 8, 8)
            self.preferences_layout.setSpacing(10)
            
            self.tab_widget.addTab(self.saveplus_tab, "SavePlus")
            self.tab_widget.addTab(self.history_tab, "History")
            self.tab_widget.addTab(self.preferences_tab, "Preferences")
            main_layout.addWidget(self.tab_widget)
            
            # Add dummy content to History and Preferences tabs
            history_label = QLabel("History tab content placeholder")
            self.history_layout.addWidget(history_label)
            preferences_label = QLabel("Preferences tab content placeholder")
            self.preferences_layout.addWidget(preferences_label)
            
            # Create container for SavePlus tab content
            self.container_widget = QWidget()
            self.container_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            self.container_layout = QVBoxLayout(self.container_widget)
            self.container_layout.setContentsMargins(0, 0, 0, 0)
            self.container_layout.setSpacing(15)
            self.container_layout.setAlignment(Qt.AlignTop)
            
            # File Options section
            self.file_options_section = ZurbriggStyleCollapsibleFrame("File Options", collapsed=False)
            self.file_options_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            file_options = QWidget()
            file_layout = QFormLayout(file_options)
            file_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            filename_layout = QHBoxLayout()
            self.filename_input = QLineEdit()
            self.filename_input.setMinimumWidth(250)
            filename_layout.addWidget(self.filename_input)
            
            current_file = cmds.file(query=True, sceneName=True)
            if current_file:
                self.filename_input.setText(os.path.basename(current_file))
            
            browse_button = QPushButton("Browse Directory")
            browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
            browse_button.clicked.connect(self.browse_file)
            browse_button.setFixedWidth(120)
            filename_layout.addWidget(browse_button)
            
            self.filetype_combo = QComboBox()
            self.filetype_combo.addItems(["Maya ASCII (.ma)", "Maya Binary (.mb)"])
            self.filetype_combo.setFixedWidth(180)
            self.filetype_combo.currentIndexChanged.connect(self.update_filename_preview)
            
            self.use_current_dir = QCheckBox("Use current directory")
            self.use_current_dir.setChecked(True)
            
            self.enable_timed_warning = QCheckBox("Enable 15-minute save reminder")
            self.enable_timed_warning.setChecked(self.load_option_var(self.OPT_VAR_ENABLE_TIMED_WARNING, False))
            self.enable_timed_warning.stateChanged.connect(self.toggle_timed_warning)
            
            self.add_version_notes = QCheckBox("Add version notes when saving")
            self.add_version_notes.setChecked(self.load_option_var(self.OPT_VAR_ADD_VERSION_NOTES, False))
            self.add_version_notes.setToolTip("Add notes for each version to track changes")
            
            file_layout.addRow("Filename:", filename_layout)
            file_layout.addRow("File Type:", self.filetype_combo)
            file_layout.addRow("", self.use_current_dir)
            file_layout.addRow("", self.enable_timed_warning)
            file_layout.addRow("", self.add_version_notes)
            
            self.file_options_section.add_widget(file_options)
            self.container_layout.addWidget(self.file_options_section)
            self.file_options_section.toggled.connect(self.adjust_window_size)
            
            # Name Generator section
            self.name_gen_section = ZurbriggStyleCollapsibleFrame("Name Generator", collapsed=True)
            self.name_gen_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            name_gen = QWidget()
            name_gen_layout = QFormLayout(name_gen)
            name_gen_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            assignment_layout = QHBoxLayout()
            self.assignment_letter_combo = QComboBox()
            self.assignment_letter_combo.addItems(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
            saved_letter = self.load_option_var(self.OPT_VAR_ASSIGNMENT_LETTER, "A")
            index = self.assignment_letter_combo.findText(saved_letter)
            if index >= 0:
                self.assignment_letter_combo.setCurrentIndex(index)
            self.assignment_letter_combo.setFixedWidth(50)
            
            self.assignment_spinbox = QSpinBox()
            self.assignment_spinbox.setRange(1, 99)
            self.assignment_spinbox.setValue(self.load_option_var(self.OPT_VAR_ASSIGNMENT_NUMBER, 1))
            self.assignment_spinbox.setFixedWidth(50)
            
            assignment_layout.addWidget(self.assignment_letter_combo)
            assignment_layout.addWidget(self.assignment_spinbox)
            assignment_layout.addStretch()
            
            self.lastname_input = QLineEdit()
            self.lastname_input.setPlaceholderText("Last Name")
            self.lastname_input.setText(self.load_option_var(self.OPT_VAR_LAST_NAME, ""))
            self.lastname_input.setFixedWidth(200)
            
            self.firstname_input = QLineEdit()
            self.firstname_input.setPlaceholderText("First Name")
            self.firstname_input.setText(self.load_option_var(self.OPT_VAR_FIRST_NAME, ""))
            self.firstname_input.setFixedWidth(200)
            
            version_type_layout = QHBoxLayout()
            self.version_type_combo = QComboBox()
            self.version_type_combo.addItems(["wip", "final"])
            saved_type = self.load_option_var(self.OPT_VAR_VERSION_TYPE, "wip")
            index = self.version_type_combo.findText(saved_type)
            if index >= 0:
                self.version_type_combo.setCurrentIndex(index)
            self.version_type_combo.setFixedWidth(100)
            version_type_layout.addWidget(self.version_type_combo)
            version_type_layout.addStretch()
            
            version_number_layout = QHBoxLayout()
            self.version_number_spinbox = QSpinBox()
            self.version_number_spinbox.setRange(1, 99)
            self.version_number_spinbox.setValue(self.load_option_var(self.OPT_VAR_VERSION_NUMBER, 1))
            self.version_number_spinbox.setFixedWidth(50)
            version_number_layout.addWidget(self.version_number_spinbox)
            version_number_layout.addStretch()
            
            self.filename_preview = QLabel("No filename")
            self.filename_preview.setStyleSheet("color: #0066CC; font-weight: bold;")
            
            buttons_layout = QHBoxLayout()
            generate_button = QPushButton("Generate Filename")
            generate_button.clicked.connect(self.generate_filename)
            reset_button = QPushButton("Reset")
            reset_button.clicked.connect(self.reset_name_generator)
            buttons_layout.addStretch()
            buttons_layout.addWidget(generate_button)
            buttons_layout.addWidget(reset_button)
            
            name_gen_layout.addRow("Assignment:", assignment_layout)
            name_gen_layout.addRow("Last Name:", self.lastname_input)
            name_gen_layout.addRow("First Name:", self.firstname_input)
            name_gen_layout.addRow("Type:", version_type_layout)
            name_gen_layout.addRow("Version:", version_number_layout)
            name_gen_layout.addRow("Preview:", self.filename_preview)
            name_gen_layout.addRow("", buttons_layout)
            
            self.name_gen_section.add_widget(name_gen)
            self.container_layout.addWidget(self.name_gen_section)
            self.name_gen_section.toggled.connect(self.adjust_window_size)
            
            # Save buttons section
            buttons_layout2 = QHBoxLayout()
            buttons_layout2.setContentsMargins(0, 10, 0, 10)
            
            save_button = QPushButton("Save Plus")
            save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
            save_button.setMinimumHeight(40)
            save_button.clicked.connect(self.save_plus)
            
            save_new_button = QPushButton("Save As New")
            save_new_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            save_new_button.setMinimumHeight(40)
            save_new_button.clicked.connect(self.save_as_new)
            
            backup_button = QPushButton("Create Backup")
            backup_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
            backup_button.setMinimumHeight(40)
            backup_button.clicked.connect(self.create_backup)
            backup_button.setToolTip("Create a backup copy of the current file")
            
            buttons_layout2.addWidget(save_button)
            buttons_layout2.addWidget(save_new_button)
            buttons_layout2.addWidget(backup_button)
            self.container_layout.addLayout(buttons_layout2)
            
            # Log Output section
            self.log_section = ZurbriggStyleCollapsibleFrame("Log Output", collapsed=True)
            self.log_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            log_content = QWidget()
            log_layout = QVBoxLayout(log_content)
            
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setLineWrapMode(QTextEdit.NoWrap)
            self.log_text.setFixedHeight(150)
            
            log_controls = QHBoxLayout()
            self.log_to_script_editor_cb = QCheckBox("Log to Script Editor")
            self.log_to_script_editor_cb.setChecked(True)
            self.clear_log_button = QPushButton("Clear Log")
            self.clear_log_button.clicked.connect(self.clear_log)
            
            log_controls.addWidget(self.log_to_script_editor_cb)
            log_controls.addStretch()
            log_controls.addWidget(self.clear_log_button)
            
            log_layout.addWidget(self.log_text)
            log_layout.addLayout(log_controls)
            self.log_section.add_widget(log_content)
            self.container_layout.addWidget(self.log_section)
            self.log_section.toggled.connect(self.adjust_window_size)
            
            self.container_layout.addSpacing(20)
            
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(self.container_widget)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.saveplus_layout.addWidget(self.scroll_area)
            
            # Update preview and start log redirection
            self.update_filename_preview()
            self.log_redirector = LogRedirector(self.log_text)
            self.log_redirector.start_redirect()
            print("SavePlus UI initialized successfully")
            
            self.last_save_time = time.time()
            self.save_timer = QTimer(self)
            self.save_timer.timeout.connect(self.check_save_time)
            
            self.last_backup_time = time.time()
            self.backup_timer = QTimer(self)
            self.backup_timer.timeout.connect(self.check_backup_time)
            
            self.is_first_save = not current_file
            
            if self.enable_timed_warning.isChecked():
                self.save_timer.start(60000)
            # Assuming self.pref_enable_auto_backup is implemented in load_preferences
            if self.load_option_var(self.OPT_VAR_ENABLE_AUTO_BACKUP, False):
                self.backup_timer.start(60000)
            self.tab_widget.currentChanged.connect(self.on_tab_changed)
            self.load_preferences()
            QtCore.QTimer.singleShot(200, self.adjust_window_size)
            self.populate_history()
                
        except Exception as e:
            error_message = f"Error initializing SavePlus UI: {str(e)}"
            print(error_message)
            traceback.print_exc()
            cmds.confirmDialog(title="SavePlus Error", 
                               message=f"Error loading SavePlus: {str(e)}\n\nCheck script editor for details.", 
                               button=["OK"], defaultButton="OK")
    
    def toggle_timed_warning(self, state):
        if state:
            self.save_timer.start(60000)  # Check every minute
            debug_print("Timed warning enabled")
        else:
            self.save_timer.stop()
            debug_print("Timed warning disabled")
    
    def closeEvent(self, event):
        debug_print("Closing SavePlus UI")
        try:
            if hasattr(self, 'log_redirector') and self.log_redirector:
                self.log_redirector.stop_redirect()
            if hasattr(self, 'save_timer') and self.save_timer:
                self.save_timer.stop()
            if hasattr(self, 'backup_timer') and self.backup_timer:
                self.backup_timer.stop()
            self.auto_resize_enabled = False
        except Exception as e:
            debug_print(f"Error during close: {e}")
        super(SavePlusUI, self).closeEvent(event)
    
    def adjust_window_size(self):
        if self.auto_resize_enabled:
            self.adjustSize()
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        save_plus_action = QAction("Save Plus", self)
        save_plus_action.setShortcut("Ctrl+S")
        save_plus_action.triggered.connect(self.save_plus)
        file_menu.addAction(save_plus_action)
        
        save_as_action = QAction("Save As New", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_new)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("Create Backup", self)
        backup_action.setShortcut("Ctrl+B")
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Version History", self)
        export_action.triggered.connect(self.export_history)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    # Placeholder methods – implementations should be filled in as needed:
    def browse_file(self):
        pass
    
    def update_filename_preview(self):
        pass
    
    def generate_filename(self):
        pass
    
    def reset_name_generator(self):
        pass
    
    def save_plus(self):
        pass
    
    def save_as_new(self):
        pass
    
    def create_backup(self):
        pass
    
    def clear_log(self):
        self.log_text.clear()
    
    def check_save_time(self):
        pass
    
    def check_backup_time(self):
        pass
    
    def load_option_var(self, var_name, default):
        return default
    
    def populate_history(self):
        pass
    
    def on_tab_changed(self, index):
        pass
    
    def load_preferences(self):
        pass
    
    def save_preferences(self):
        pass
    
    def export_history(self):
        pass
        

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    # Use the existing QApplication instance if available
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = SavePlusUI()
    window.show()
    app.exec()  # No sys.exit() is called in Maya
