"""
SavePlus Main - Main UI class and functionality for the SavePlus tool
Part of the SavePlus toolset for Maya 2025
"""

import os
import time
import traceback
from maya import cmds, mel

from PySide6.QtWidgets import (QPushButton, QVBoxLayout, QLabel, QLineEdit, 
                              QHBoxLayout, QCheckBox, QFileDialog, QMainWindow, 
                              QMenuBar, QStatusBar, QGridLayout, QFrame, QGroupBox, 
                              QComboBox, QStyle, QSizePolicy, QTextEdit, QSpinBox,
                              QMessageBox, QFormLayout, QScrollArea, QTabWidget, 
                              QListWidget, QListWidgetItem, QTableWidget, 
                              QTableWidgetItem, QHeaderView, QWidget, QDialog)
from PySide6 import QtCore
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import savePlus_core
import savePlus_ui_components

# Constants
VERSION = savePlus_core.VERSION
UNIQUE_IDENTIFIER = "SavePlus_v1_ToolButton"

class SavePlusUI(MayaQWidgetDockableMixin, QMainWindow):
    """SavePlus UI Class - Modern interface with menus and log display"""
    
    # Option variables for saving settings
    OPT_VAR_ASSIGNMENT_LETTER = "SavePlusAssignmentLetter"
    OPT_VAR_ASSIGNMENT_NUMBER = "SavePlusAssignmentNumber"
    OPT_VAR_LAST_NAME = "SavePlusLastName"
    OPT_VAR_FIRST_NAME = "SavePlusFirstName"
    OPT_VAR_VERSION_TYPE = "SavePlusVersionType"
    OPT_VAR_VERSION_NUMBER = "SavePlusVersionNumber"
    OPT_VAR_ENABLE_TIMED_WARNING = "SavePlusEnableTimedWarning"
    
    # Option variables for saving preferences
    OPT_VAR_DEFAULT_FILETYPE = "SavePlusDefaultFiletype"
    OPT_VAR_AUTO_SAVE_INTERVAL = "SavePlusAutoSaveInterval"
    OPT_VAR_DEFAULT_SAVE_PATH = "SavePlusDefaultSavePath"
    OPT_VAR_PROJECT_PATH = "SavePlusProjectPath"
    OPT_VAR_FILE_EXPANDED = "SavePlusFileExpanded"
    OPT_VAR_NAME_EXPANDED = "SavePlusNameExpanded"
    OPT_VAR_LOG_EXPANDED = "SavePlusLogExpanded"
    
    # New option variables
    OPT_VAR_ENABLE_AUTO_BACKUP = "SavePlusEnableAutoBackup"
    OPT_VAR_BACKUP_INTERVAL = "SavePlusBackupInterval"
    OPT_VAR_ADD_VERSION_NOTES = "SavePlusAddVersionNotes"
    
    def __init__(self, parent=None):
        try:
            super(SavePlusUI, self).__init__(parent)
            savePlus_core.debug_print("Initializing SavePlus UI")
            
            # Set window properties
            self.setWindowTitle("SavePlus")
            self.setMinimumWidth(550)
            self.setMinimumHeight(450)
            
            # Flag to control auto-resize behavior
            self.auto_resize_enabled = True
            
            # Directory selected with browse button
            self.selected_directory = None
            
            # Initialize version history manager
            self.version_history = savePlus_core.VersionHistoryModel()
            
            # Create a central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(0)
            
            # --- CREATE BASIC UI FIRST --- 
            
            # Create menu bar (basic UI component)
            self.create_menu_bar()
            
            # Create status bar (basic UI component)
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # --- CREATE HEADER ABOVE TABS ---
            
            # Create a modern header
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(10, 5, 10, 5)
            
            # Title with version
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
            
            # Description on the right
            description = QLabel("Increment and save your Maya files")
            description.setStyleSheet("color: #555555; font-size: 11px;")
            description.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Add to header layout
            header_layout.addLayout(title_layout)
            header_layout.addStretch()
            header_layout.addWidget(description)
            
            # Add header to main layout
            header_container = QFrame()
            header_container.setFrameShape(QFrame.StyledPanel)
            header_container.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 4px; }")
            header_container.setLayout(header_layout)
            
            main_layout.addWidget(header_container)
            
            # Create a subtle separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
            main_layout.addWidget(separator)
            main_layout.addSpacing(5)  # Add a small space after the separator
            
            # --- CREATE TABS ---
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            
            # Create SavePlus Tab
            self.saveplus_tab = QWidget()
            self.saveplus_layout = QVBoxLayout(self.saveplus_tab)
            self.saveplus_layout.setContentsMargins(8, 8, 8, 8)
            self.saveplus_layout.setSpacing(8)
            
            # Create History Tab
            self.history_tab = QWidget()
            self.history_layout = QVBoxLayout(self.history_tab)
            self.history_layout.setContentsMargins(8, 8, 8, 8)
            self.history_layout.setSpacing(8)
            
            # Create Preferences Tab
            self.preferences_tab = QWidget()
            self.preferences_layout = QVBoxLayout(self.preferences_tab)
            self.preferences_layout.setContentsMargins(8, 8, 8, 8)
            self.preferences_layout.setSpacing(10)
            
            # Add tabs to tab widget
            self.tab_widget.addTab(self.saveplus_tab, "SavePlus")
            self.tab_widget.addTab(self.history_tab, "History")
            self.tab_widget.addTab(self.preferences_tab, "Preferences")
            
            # Add tab widget to main layout
            main_layout.addWidget(self.tab_widget)
            
            # --- SAVEPLUS TAB CONTENT ---
            
            # Create container widget for scrollable content
            self.container_widget = QWidget()
            # Set a fixed policy to ensure elements stay at the top
            self.container_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            
            self.container_layout = QVBoxLayout(self.container_widget)
            self.container_layout.setContentsMargins(0, 0, 0, 0)
            self.container_layout.setSpacing(15)  # Increased spacing between sections
            self.container_layout.setAlignment(Qt.AlignTop)  # Keep elements aligned at the top
            
            # Create File Options section (expanded by default)
            self.file_options_section = savePlus_ui_components.ZurbriggStyleCollapsibleFrame("File Options", collapsed=False)
            self.file_options_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Create file options content
            file_options = QWidget()
            file_layout = QFormLayout(file_options)
            file_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # Add filename input field
            filename_layout = QHBoxLayout()
            self.filename_input = QLineEdit()
            self.filename_input.setMinimumWidth(250)
            filename_layout.addWidget(self.filename_input)
            
            # Add save location display label
            self.save_location_label = QLabel()
            self.save_location_label.setStyleSheet("color: #666666; font-size: 9px;")
            file_layout.addRow("Save Location:", self.save_location_label)

            # Get current file name if available
            current_file = cmds.file(query=True, sceneName=True)
            if current_file:
                self.filename_input.setText(os.path.basename(current_file))
            
            browse_button = QPushButton("Browse Directory")
            browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
            browse_button.clicked.connect(self.browse_file)
            browse_button.setFixedWidth(120)
            filename_layout.addWidget(browse_button)
            
            # Add file type selection
            self.filetype_combo = QComboBox()
            self.filetype_combo.addItems(["Maya ASCII (.ma)", "Maya Binary (.mb)"])
            self.filetype_combo.setFixedWidth(180)
            self.filetype_combo.currentIndexChanged.connect(self.update_filename_preview)
            
            # Add option to use the current directory
            self.use_current_dir = QCheckBox("Use current directory")
            self.use_current_dir.setChecked(True)
            
            # Create layout for save reminder controls
            save_reminder_layout = QHBoxLayout()
            save_reminder_layout.setContentsMargins(0, 0, 0, 0)

            # Add timed save reminder checkbox with updated label
            self.enable_timed_warning = QCheckBox("Enable save reminder every")
            self.enable_timed_warning.setChecked(self.load_option_var(self.OPT_VAR_ENABLE_TIMED_WARNING, False))
            self.enable_timed_warning.stateChanged.connect(self.toggle_timed_warning)
            save_reminder_layout.addWidget(self.enable_timed_warning)

            # Add spinner for reminder interval
            self.reminder_interval_spinbox = QSpinBox()
            self.reminder_interval_spinbox.setRange(1, 60)
            self.reminder_interval_spinbox.setValue(self.load_option_var(self.OPT_VAR_AUTO_SAVE_INTERVAL, 15))
            self.reminder_interval_spinbox.setSuffix(" minutes")
            self.reminder_interval_spinbox.setFixedWidth(100)
            self.reminder_interval_spinbox.valueChanged.connect(self.update_reminder_interval)
            save_reminder_layout.addWidget(self.reminder_interval_spinbox)
            save_reminder_layout.addStretch()
            
            # Add version notes option
            self.add_version_notes = QCheckBox("Add version notes when saving")
            self.add_version_notes.setChecked(self.load_option_var(self.OPT_VAR_ADD_VERSION_NOTES, False))
            self.add_version_notes.setToolTip("Add notes for each version to track changes")
            
            # Add to form layout
            file_layout.addRow("Filename:", filename_layout)
            file_layout.addRow("File Type:", self.filetype_combo)
            file_layout.addRow("", self.use_current_dir)
            file_layout.addRow("", save_reminder_layout)
            file_layout.addRow("", self.add_version_notes)
            
            self.file_options_section.add_widget(file_options)
            self.container_layout.addWidget(self.file_options_section)
            
            # Add file_options_section toggled signal connection
            self.file_options_section.toggled.connect(self.adjust_window_size)
            
            # Create Name Generator section (collapsed by default)
            self.name_gen_section = savePlus_ui_components.ZurbriggStyleCollapsibleFrame("Name Generator", collapsed=True)
            self.name_gen_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Create name generator content
            name_gen = QWidget()
            name_gen_layout = QFormLayout(name_gen)
            name_gen_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # Assignment letter and number
            assignment_layout = QHBoxLayout()
            
            # Assignment letter selection
            self.assignment_letter_combo = QComboBox()
            self.assignment_letter_combo.addItems(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
            saved_letter = self.load_option_var(self.OPT_VAR_ASSIGNMENT_LETTER, "A")
            index = self.assignment_letter_combo.findText(saved_letter)
            if index >= 0:
                self.assignment_letter_combo.setCurrentIndex(index)
            self.assignment_letter_combo.setFixedWidth(50)
            
            # Assignment number selection
            self.assignment_spinbox = QSpinBox()
            self.assignment_spinbox.setRange(1, 99)
            self.assignment_spinbox.setValue(self.load_option_var(self.OPT_VAR_ASSIGNMENT_NUMBER, 1))
            self.assignment_spinbox.setFixedWidth(50)
            
            assignment_layout.addWidget(self.assignment_letter_combo)
            assignment_layout.addWidget(self.assignment_spinbox)
            assignment_layout.addStretch()
            
            # Last name
            self.lastname_input = QLineEdit()
            self.lastname_input.setPlaceholderText("Last Name")
            self.lastname_input.setText(self.load_option_var(self.OPT_VAR_LAST_NAME, ""))
            self.lastname_input.setFixedWidth(200)
            
            # First name
            self.firstname_input = QLineEdit()
            self.firstname_input.setPlaceholderText("First Name")
            self.firstname_input.setText(self.load_option_var(self.OPT_VAR_FIRST_NAME, ""))
            self.firstname_input.setFixedWidth(200)
            
            # Version type
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
            
            # Version number
            version_number_layout = QHBoxLayout()
            self.version_number_spinbox = QSpinBox()
            self.version_number_spinbox.setRange(1, 99)
            self.version_number_spinbox.setValue(self.load_option_var(self.OPT_VAR_VERSION_NUMBER, 1))
            self.version_number_spinbox.setFixedWidth(50)
            version_number_layout.addWidget(self.version_number_spinbox)
            version_number_layout.addStretch()
            
            # Preview label
            self.filename_preview = QLabel("No filename")
            self.filename_preview.setStyleSheet("color: #0066CC; font-weight: bold;")
            
            # Generate and Reset buttons
            buttons_layout = QHBoxLayout()
            generate_button = QPushButton("Generate Filename")
            generate_button.clicked.connect(self.generate_filename)
            
            reset_button = QPushButton("Reset")
            reset_button.clicked.connect(self.reset_name_generator)
            
            buttons_layout.addStretch()
            buttons_layout.addWidget(generate_button)
            buttons_layout.addWidget(reset_button)
            
            # Add all to form layout
            name_gen_layout.addRow("Assignment:", assignment_layout)
            name_gen_layout.addRow("Last Name:", self.lastname_input)
            name_gen_layout.addRow("First Name:", self.firstname_input)
            name_gen_layout.addRow("Type:", version_type_layout)
            name_gen_layout.addRow("Version:", version_number_layout)
            name_gen_layout.addRow("Preview:", self.filename_preview)
            name_gen_layout.addRow("", buttons_layout)
            
            self.name_gen_section.add_widget(name_gen)
            self.container_layout.addWidget(self.name_gen_section)
            
            # Add name_gen_section toggled signal connection
            self.name_gen_section.toggled.connect(self.adjust_window_size)
            
            # Add save buttons
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 10, 0, 10)  # Add some vertical padding
            
            save_button = QPushButton("Save Plus")
            save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
            save_button.setMinimumHeight(40)
            save_button.clicked.connect(self.save_plus)
            
            save_new_button = QPushButton("Save As New")
            save_new_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            save_new_button.setMinimumHeight(40)
            save_new_button.clicked.connect(self.save_as_new)
            
            # New backup button
            backup_button = QPushButton("Create Backup")
            backup_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
            backup_button.setMinimumHeight(40)
            backup_button.clicked.connect(self.create_backup)
            backup_button.setToolTip("Create a backup copy of the current file")
            
            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(save_new_button)
            buttons_layout.addWidget(backup_button)
            
            self.container_layout.addLayout(buttons_layout)
            
            # Create Log section (collapsed by default)
            self.log_section = savePlus_ui_components.ZurbriggStyleCollapsibleFrame("Log Output", collapsed=True)
            self.log_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Create log content
            log_content = QWidget()
            log_layout = QVBoxLayout(log_content)
            
            # Create log text display with fixed height
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setLineWrapMode(QTextEdit.NoWrap)
            self.log_text.setFixedHeight(150)  # Fixed height for log
            
            # Log controls
            log_controls = QHBoxLayout()
            
            # Add log to script editor option
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
            
            # Add log_section toggled signal connection
            self.log_section.toggled.connect(self.adjust_window_size)
            
            # Add spacing at the bottom
            self.container_layout.addSpacing(20)
            
            # Create scroll area
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(self.container_widget)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Add scroll area to saveplus layout
            self.saveplus_layout.addWidget(self.scroll_area)
            
            # --- HISTORY TAB CONTENT ---
            
            # Create Recent Files group at the top of History tab
            recent_files_group = QGroupBox("Recent Files")
            recent_files_layout = QVBoxLayout(recent_files_group)
            
            # Recent files list
            self.recent_files_list = QListWidget()
            self.recent_files_list.setAlternatingRowColors(True)
            self.recent_files_list.setMaximumHeight(150)
            self.recent_files_list.itemDoubleClicked.connect(self.open_recent_file)
            self.populate_recent_files()
            
            # Recent files controls
            recent_controls_layout = QHBoxLayout()
            
            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(self.populate_recent_files)
            
            open_button = QPushButton("Open Selected")
            open_button.clicked.connect(self.open_selected_file)
            
            recent_controls_layout.addWidget(refresh_button)
            recent_controls_layout.addStretch()
            recent_controls_layout.addWidget(open_button)
            
            recent_files_layout.addWidget(self.recent_files_list)
            recent_files_layout.addLayout(recent_controls_layout)
            
            # Create a table for version history
            version_history_group = QGroupBox("Version History")
            version_history_layout = QVBoxLayout(version_history_group)
            
            self.history_table = QTableWidget()
            self.history_table.setColumnCount(4)
            self.history_table.setHorizontalHeaderLabels(["Filename", "Date", "Path", "Notes"])
            self.history_table.setAlternatingRowColors(True)
            self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make read-only
            self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.history_table.setSelectionMode(QTableWidget.SingleSelection)
            
            # Adjust column widths
            header = self.history_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            
            # History controls
            history_controls = QHBoxLayout()
            
            refresh_history_button = QPushButton("Refresh")
            refresh_history_button.clicked.connect(self.populate_history)
            
            open_history_button = QPushButton("Open Selected")
            open_history_button.clicked.connect(self.open_selected_history_file)
            
            export_history_button = QPushButton("Export History")
            export_history_button.clicked.connect(self.export_history)
            export_history_button.setToolTip("Export version history to a text file")
            
            history_controls.addWidget(refresh_history_button)
            history_controls.addStretch()
            history_controls.addWidget(open_history_button)
            history_controls.addWidget(export_history_button)
            
            # Add to version history layout
            version_history_layout.addWidget(self.history_table)
            version_history_layout.addLayout(history_controls)
            
            # Add both sections to history tab
            self.history_layout.addWidget(recent_files_group)
            self.history_layout.addWidget(version_history_group)
            
            # --- PREFERENCES TAB CONTENT ---
            
            # General Preferences
            general_group = QGroupBox("General Settings")
            general_layout = QFormLayout(general_group)
            
            # Default file type preference
            self.pref_default_filetype = QComboBox()
            self.pref_default_filetype.addItems(["Maya ASCII (.ma)", "Maya Binary (.mb)"])
            general_layout.addRow("Default File Type:", self.pref_default_filetype)
            
            # Auto-save settings
            self.pref_auto_save_interval = QSpinBox()
            self.pref_auto_save_interval.setRange(1, 60)
            self.pref_auto_save_interval.setValue(15)
            self.pref_auto_save_interval.setSuffix(" minutes")
            self.pref_auto_save_interval.setToolTip("Time between save reminders")
            general_layout.addRow("Auto-save Interval:", self.pref_auto_save_interval)
            
            # Auto-backup settings
            self.pref_enable_auto_backup = QCheckBox("Enable auto-backup")
            self.pref_enable_auto_backup.setChecked(self.load_option_var(self.OPT_VAR_ENABLE_AUTO_BACKUP, False))
            self.pref_enable_auto_backup.setToolTip("Automatically create backups at specified intervals")
            
            auto_backup_layout = QHBoxLayout()
            self.pref_backup_interval = QSpinBox()
            self.pref_backup_interval.setRange(5, 120)
            self.pref_backup_interval.setValue(self.load_option_var(self.OPT_VAR_BACKUP_INTERVAL, 30))
            self.pref_backup_interval.setSuffix(" minutes")
            auto_backup_layout.addWidget(self.pref_backup_interval)
            auto_backup_layout.addStretch()
            
            general_layout.addRow("", self.pref_enable_auto_backup)
            general_layout.addRow("Backup Interval:", auto_backup_layout)
            
            # Add to preferences layout
            self.preferences_layout.addWidget(general_group)
            
            # Path Preferences
            paths_group = QGroupBox("Path Settings")
            paths_layout = QFormLayout(paths_group)
            
            # Default save location
            default_location = QHBoxLayout()
            self.pref_default_path = QLineEdit()
            self.pref_default_path.setPlaceholderText("Default directory for saving files")
            browse_default_button = QPushButton("Browse...")
            browse_default_button.setFixedWidth(80)
            browse_default_button.clicked.connect(self.browse_default_save_location)
            default_location.addWidget(self.pref_default_path)
            default_location.addWidget(browse_default_button)
            
            paths_layout.addRow("Default Save Location:", default_location)
            
            # Project directory
            project_location = QHBoxLayout()
            self.pref_project_path = QLineEdit()
            self.pref_project_path.setPlaceholderText("Maya project directory")
            project_browse = QPushButton("Browse...")
            project_browse.setFixedWidth(80)
            project_browse.clicked.connect(self.browse_project_directory)
            project_location.addWidget(self.pref_project_path)
            project_location.addWidget(project_browse)
            
            paths_layout.addRow("Project Directory:", project_location)
            
            # Add to preferences layout
            self.preferences_layout.addWidget(paths_group)
            
            # UI Preferences
            ui_group = QGroupBox("UI Settings")
            ui_layout = QFormLayout(ui_group)
            
            # Default sections expanded
            self.pref_file_expanded = QCheckBox("File Options section expanded by default")
            self.pref_file_expanded.setChecked(True)
            ui_layout.addRow("", self.pref_file_expanded)
            
            self.pref_name_expanded = QCheckBox("Name Generator section expanded by default")
            ui_layout.addRow("", self.pref_name_expanded)
            
            self.pref_log_expanded = QCheckBox("Log Output section expanded by default")
            ui_layout.addRow("", self.pref_log_expanded)
            
            # Add to preferences layout
            ui_group.setLayout(ui_layout)
            self.preferences_layout.addWidget(ui_group)
            
            # Add spacer at the bottom
            self.preferences_layout.addStretch()
            
            # Add "Apply Settings" button
            apply_button = QPushButton("Apply Settings")
            apply_button.setFixedWidth(120)
            apply_button.clicked.connect(self.save_preferences)
            apply_button_layout = QHBoxLayout()
            apply_button_layout.addStretch()
            apply_button_layout.addWidget(apply_button)
            
            self.preferences_layout.addLayout(apply_button_layout)
            
            # Update filename preview initially
            self.update_filename_preview()
            
            # Setup log redirector
            self.log_redirector = savePlus_ui_components.LogRedirector(self.log_text)
            self.log_redirector.start_redirect()
            
            # Log initialization message
            print("SavePlus UI initialized successfully")
            print("Setting up temporary test interval for reminder")
            self.reminder_interval_spinbox.setValue(0.2)  # Set to 0.2 minutes (12 seconds) for testing
            self.enable_timed_warning.setChecked(True)  # Force enable for testing
            
            # Setup timer for save reminders
            self.last_save_time = time.time()
            self.save_timer = QTimer(self)
            self.save_timer.timeout.connect(self.check_save_time)

            # Enable this timer in Maya's event loop - ADD THIS CODE RIGHT HERE
            if hasattr(self, 'save_timer'):
                # Connect to Maya's main loop if needed
                try:
                    from maya import OpenMayaUI as omui
                    print("[SavePlus Debug] Connected timer to Maya's event loop")
                except Exception as e:
                    print(f"[SavePlus Debug] Using standard Qt timer: {e}")

            # Start timers if options are enabled
            if self.enable_timed_warning.isChecked():
                if not self.save_timer.isActive():
                    # For testing, check every 10 seconds instead of every minute
                    self.save_timer.start(10000)  # 10 seconds (change back to 60000 for production)
                    print("[SavePlus Debug] Timer started during initialization")
                    print(f"[SavePlus Debug] Current time: {time.ctime(self.last_save_time)}")
            
            # Setup timer for auto-backup
            self.last_backup_time = time.time()
            self.backup_timer = QTimer(self)
            self.backup_timer.timeout.connect(self.check_backup_time)
            
            # Flag to track first-time save
            self.is_first_save = not current_file
            
            if self.pref_enable_auto_backup.isChecked():
                self.backup_timer.start(60000)  # Check every minute
            
            # Connect tab changed signal to update history
            self.tab_widget.currentChanged.connect(self.on_tab_changed)
            
            # Load preferences
            self.load_preferences()
            
            # Schedule initial window sizing after UI is fully constructed
            QtCore.QTimer.singleShot(200, self.adjust_window_size)
            
            # Initial population of history
            self.populate_history()
                
        except Exception as e:
            error_message = f"Error initializing SavePlus UI: {str(e)}"
            print(error_message)
            traceback.print_exc()
            cmds.confirmDialog(title="SavePlus Error", 
                              message=f"Error loading SavePlus: {str(e)}\n\nCheck script editor for details.", 
                              button=["OK"], defaultButton="OK")

    def update_reminder_interval(self, value):
        """Update the save reminder interval"""
        # Save the new interval to preferences
        cmds.optionVar(iv=(self.OPT_VAR_AUTO_SAVE_INTERVAL, value))
        
        # Update the value in the preferences tab to keep them in sync
        if hasattr(self, 'pref_auto_save_interval'):
            self.pref_auto_save_interval.setValue(value)
        
        print(f"Save reminder interval updated to {value} minutes")

    def closeEvent(self, event):
        """Handle clean up when window is closed"""
        savePlus_core.debug_print("Closing SavePlus UI")
        try:
            # Stop redirecting output
            if hasattr(self, 'log_redirector') and self.log_redirector:
                self.log_redirector.stop_redirect()
            
            # Stop timers
            if hasattr(self, 'save_timer') and self.save_timer:
                self.save_timer.stop()
                
            if hasattr(self, 'backup_timer') and self.backup_timer:
                self.backup_timer.stop()
            
            # Disable auto resize to prevent errors during shutdown
            self.auto_resize_enabled = False
        except Exception as e:
            savePlus_core.debug_print(f"Error during close: {e}")
        
        super(SavePlusUI, self).closeEvent(event)
    
    def create_menu_bar(self):
        """Create the menu bar with all menu items"""
        menu_bar = self.menuBar()
        
        # File menu
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
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        prefs_action = QAction("Preferences", self)
        prefs_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(prefs_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About SavePlus", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def clear_log(self):
        """Clear the log display"""
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.clear()
    
    def browse_file(self):
        """Open file browser to select save location directory"""
        print("Opening file browser for save location directory...")
        
        # Use default path from preferences if available
        default_path = ""
        if hasattr(self, 'pref_default_path') and self.pref_default_path.text():
            default_path = self.pref_default_path.text()
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Location Directory", default_path
        )
        
        if directory:
            # Store the directory path but keep the current filename
            current_filename = os.path.basename(self.filename_input.text())
            
            # If we have a filename, combine with the new directory
            if current_filename:
                new_path = os.path.join(directory, current_filename)
                self.filename_input.setText(new_path)
                print(f"Selected directory: {directory}")
                print(f"Updated path: {new_path}")
            else:
                # If no filename set yet, just remember the directory for later
                self.selected_directory = directory
                print(f"Selected directory: {directory}")
                self.status_bar.showMessage(f"Directory set to: {directory}", 5000)
            
            # Uncheck the "use current directory" option since we've specified a custom one
            self.use_current_dir.setChecked(False)
            
            self.update_filename_preview()
            
            # Update save location display
            self.update_save_location_display()

    def update_save_location_display(self):
        """Update the display of the current save location"""
        if hasattr(self, 'save_location_label'):
            if self.selected_directory:
                self.save_location_label.setText(self.selected_directory)
            elif hasattr(self, 'pref_default_path') and self.pref_default_path.text() and self.use_current_dir.isChecked():
                self.save_location_label.setText(self.pref_default_path.text())
            else:
                current_file = cmds.file(query=True, sceneName=True)
                if current_file:
                    self.save_location_label.setText(os.path.dirname(current_file))
                else:
                    self.save_location_label.setText("Default Maya project")

    def browse_default_save_location(self):
        """Open file browser to select default save location directory"""
        print("Opening file browser for default save location...")
        current_path = self.pref_default_path.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Save Location", current_path
        )
        
        if directory:
            self.pref_default_path.setText(directory)
            print(f"Default save location set to: {directory}")
            self.status_bar.showMessage(f"Default save location set to: {directory}", 5000)
    
    def browse_project_directory(self):
        """Open file browser to select project directory"""
        print("Opening file browser for project directory...")
        current_path = self.pref_project_path.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", current_path
        )
        
        if directory:
            self.pref_project_path.setText(directory)
            print(f"Project directory set to: {directory}")
            self.status_bar.showMessage(f"Project directory set to: {directory}", 5000)
    
    def save_plus(self):
        """Execute the save plus operation with the specified filename"""
        print("Starting Save Plus operation...")
        # Reset the save timer immediately when save is attempted
        self.last_save_time = time.time()
        filename = self.filename_input.text()
        
        if not filename:
            message = "Error: Please enter a filename"
            self.status_bar.showMessage(message, 5000)
            print(message)
            return
        
        # Handle the file path
        current_file_path = cmds.file(query=True, sceneName=True)
        current_dir = ""
        
        # Check if this is a first save
        is_first_save = not current_file_path
        
        # If only a filename is provided (no path)
        if not os.path.dirname(filename):
            if self.selected_directory and not self.use_current_dir.isChecked():
                # Use the directory selected via Browse button
                filename = os.path.join(self.selected_directory, filename)
                print(f"Using selected directory: {self.selected_directory}")
            elif current_file_path and self.use_current_dir.isChecked():
                # Use current file's directory
                current_dir = os.path.dirname(current_file_path)
                filename = os.path.join(current_dir, filename)
                print(f"Using current directory: {current_dir}")
        
        # Apply selected file extension
        base_name, ext = os.path.splitext(filename)
        if not ext or (ext.lower() not in ['.ma', '.mb']):
            # Extension based on dropdown (.ma is first)
            ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
            filename = base_name + ext
            print(f"Applied file extension: {ext}")
        
        print(f"Attempting to save as: {filename}")
        
        # Get version notes if enabled
        version_notes = ""
        if self.add_version_notes.isChecked():
            notes_dialog = savePlus_ui_components.NoteInputDialog(self)
            if notes_dialog.exec() == QDialog.Accepted:
                version_notes = notes_dialog.get_notes()
                print("Version notes added")
            else:
                print("Skipped version notes")
        
        # Perform the save operation
        result, message, new_file_path = savePlus_core.save_plus_proc(filename)
        self.status_bar.showMessage(message, 5000)
        print(message)
        
        # Update the filename field with the new filename if successful
        if result:
            new_filename = cmds.file(query=True, sceneName=True)
            if new_filename:
                self.filename_input.setText(os.path.basename(new_filename))
                print(f"Updated filename to: {os.path.basename(new_filename)}")
                self.update_filename_preview()
                
                # Update version history
                self.version_history.add_version(new_file_path, version_notes)
                self.populate_recent_files()
                              
                # Reset the backup timer
                self.last_backup_time = time.time()
                
                # If this was a first-time save and warnings are enabled, show first-time warning
                if is_first_save and self.enable_timed_warning.isChecked():
                    self.show_first_time_warning()
    
    def save_as_new(self):
        """Save the file with the specified name without incrementing"""
        print("Starting Save As New operation...")
        # Reset the save timer immediately when save is attempted
        self.last_save_time = time.time()
        filename = self.filename_input.text()
        
        if not filename:
            message = "Error: Please enter a filename"
            self.status_bar.showMessage(message, 5000)
            print(message)
            return
        
        # Handle the file path
        current_file_path = cmds.file(query=True, sceneName=True)
        
        # Check if this is a first save
        is_first_save = not current_file_path
        
        # If only a filename is provided (no path)
        if not os.path.dirname(filename):
            if self.selected_directory and not self.use_current_dir.isChecked():
                # Use the directory selected via Browse button
                filename = os.path.join(self.selected_directory, filename)
                print(f"Using selected directory: {self.selected_directory}")
            elif current_file_path and self.use_current_dir.isChecked():
                # Use current file's directory
                current_dir = os.path.dirname(current_file_path)
                filename = os.path.join(current_dir, filename)
                print(f"Using current directory: {current_dir}")
        
        # Apply selected file extension
        base_name, ext = os.path.splitext(filename)
        if not ext or (ext.lower() not in ['.ma', '.mb']):
            # Extension based on dropdown (.ma is first)
            ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
            filename = base_name + ext
            print(f"Applied file extension: {ext}")
        
        print(f"Attempting to save as: {filename}")
        
        # Check if file exists - MODIFIED to give user options
        if os.path.exists(filename):
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("File Exists")
            msgBox.setText(f"The file {os.path.basename(filename)} already exists.\nWhat would you like to do?")

            overwriteButton = msgBox.addButton("Overwrite", QMessageBox.ActionRole)
            newNameButton = msgBox.addButton("Use New Name", QMessageBox.ActionRole)
            cancelButton = msgBox.addButton("Cancel", QMessageBox.RejectRole)

            msgBox.setDefaultButton(cancelButton)  # Set Cancel as default
            msgBox.exec()

            clickedButton = msgBox.clickedButton()

            if clickedButton == overwriteButton:
                choice = 0  # Maintain original choice values
            elif clickedButton == newNameButton:
                choice = 1
            else:
                choice = 2
            
            if choice == 0:  # Overwrite
                print(f"Overwriting existing file: {filename}")
                # Continue with save operation
            elif choice == 1:  # Use New Name
                # Generate a new unique filename
                base_dir = os.path.dirname(filename)
                base_name, ext = os.path.splitext(os.path.basename(filename))
                
                # Try to find a unique name by adding a number
                counter = 1
                new_filename = os.path.join(base_dir, f"{base_name}_{counter}{ext}")
                while os.path.exists(new_filename):
                    counter += 1
                    new_filename = os.path.join(base_dir, f"{base_name}_{counter}{ext}")
                
                filename = new_filename
                print(f"Using new unique filename: {filename}")
            else:  # Cancel
                message = "Save operation cancelled"
                self.status_bar.showMessage(message, 5000)
                print(message)
                return
        
        # Get version notes if enabled
        version_notes = ""
        if self.add_version_notes.isChecked():
            notes_dialog = savePlus_ui_components.NoteInputDialog(self)
            if notes_dialog.exec() == QDialog.Accepted:
                version_notes = notes_dialog.get_notes()
                print("Version notes added")
            else:
                print("Skipped version notes")
        
        # Make sure directory exists
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            try:
                print(f"Creating directory: {directory}")
                os.makedirs(directory)
            except OSError as e:
                message = f"Error: Could not create directory {directory}: {e}"
                self.status_bar.showMessage(message, 5000)
                print(message)
                return
        
        # Save the file
        try:
            cmds.file(rename=filename)
            
            # Explicitly specify the file type based on extension for proper saving
            if filename.lower().endswith('.ma'):
                cmds.file(save=True, type='mayaAscii')
            elif filename.lower().endswith('.mb'):
                cmds.file(save=True, type='mayaBinary')
            else:
                # Default to Maya ASCII if extension is unknown
                cmds.file(save=True, type='mayaAscii')
                
            message = f"{os.path.basename(filename)} saved successfully"
            self.status_bar.showMessage(message, 5000)
            print(message)
            
            # Update version history
            self.version_history.add_version(filename, version_notes)
            self.populate_recent_files()
                      
            # Reset the backup timer
            self.last_backup_time = time.time()
            
            # If this was a first-time save and warnings are enabled, show first-time warning
            if is_first_save and self.enable_timed_warning.isChecked():
                self.show_first_time_warning()
        except Exception as e:
            message = f"Error saving file: {e}"
            self.status_bar.showMessage(message, 5000)
            print(message)
    
    def create_backup(self):
        """Create a backup copy of the current file"""
        print("Creating backup...")
        
        # Check if file is saved
        current_file = cmds.file(query=True, sceneName=True)
        if not current_file:
            message = "Error: File must be saved at least once before creating a backup"
            self.status_bar.showMessage(message, 5000)
            print(message)
            return
        
        # Create backup
        success, message, backup_path = savePlus_core.create_backup(current_file)
        self.status_bar.showMessage(message, 5000)
        
        if success:
            # Add to history
            self.version_history.add_version(backup_path, "Automatic backup")
            self.populate_recent_files()
        
        return success
    
    def populate_recent_files(self):
        """Populate the recent files list"""
        try:
            self.recent_files_list.clear()
            
            recent_versions = self.version_history.get_recent_versions(20)
            
            for version in recent_versions:
                # Create list item with filename and date
                filename = version.get('filename', 'Unknown')
                date = version.get('date', '')
                
                item = QListWidgetItem(f"{filename} - {date}")
                item.setData(Qt.UserRole, version.get('path', ''))
                
                # Set tooltip to show path and notes
                tooltip = f"Path: {version.get('path', '')}"
                notes = version.get('notes', '').strip()
                if notes:
                    tooltip += f"\nNotes: {notes}"
                item.setToolTip(tooltip)
                
                self.recent_files_list.addItem(item)
        except Exception as e:
            savePlus_core.debug_print(f"Error populating recent files: {e}")
    
    def open_recent_file(self, item):
        """Open a file from the recent files list"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.open_maya_file(file_path)
    
    def open_selected_file(self):
        """Open the selected file from the recent files list"""
        selected_items = self.recent_files_list.selectedItems()
        if selected_items:
            file_path = selected_items[0].data(Qt.UserRole)
            if file_path and os.path.exists(file_path):
                self.open_maya_file(file_path)
            else:
                message = f"File not found: {file_path}"
                self.status_bar.showMessage(message, 5000)
                print(message)
    
    def open_maya_file(self, file_path):
        """Open a Maya file"""
        # Check for unsaved changes
        if cmds.file(query=True, modified=True):
            result = cmds.confirmDialog(
                title='Unsaved Changes',
                message='Save changes to the current file?',
                button=['Save', 'Don\'t Save', 'Cancel'],
                defaultButton='Save',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            
            if result == 'Cancel':
                return
            elif result == 'Save':
                cmds.file(save=True)
        
        # Find this section in the open_maya_file method, around line 880
        try:
            cmds.file(file_path, open=True, force=True)
            message = f"Opened: {os.path.basename(file_path)}"
            self.status_bar.showMessage(message, 5000)
            print(message)
            
            # Update the filename input
            self.filename_input.setText(os.path.basename(file_path))
            self.update_filename_preview()
            
            # Add these new lines to update the save location display
            self.selected_directory = os.path.dirname(file_path)
            self.update_save_location_display()
            
        except Exception as e:
            message = f"Error opening file: {e}"
            self.status_bar.showMessage(message, 5000)
            print(message)
    
    def populate_history(self):
        """Populate the history table with version history"""
        try:
            self.history_table.setRowCount(0)  # Clear table
            
            # Get current file path
            current_file = cmds.file(query=True, sceneName=True)
            
            if current_file:
                versions = self.version_history.get_versions_for_file(current_file)
                
                for idx, version in enumerate(versions):
                    self.history_table.insertRow(idx)
                    
                    # Filename
                    filename_item = QTableWidgetItem(version.get('filename', 'Unknown'))
                    self.history_table.setItem(idx, 0, filename_item)
                    
                    # Date
                    date_item = QTableWidgetItem(version.get('date', ''))
                    self.history_table.setItem(idx, 1, date_item)
                    
                    # Path
                    path_item = QTableWidgetItem(version.get('path', ''))
                    self.history_table.setItem(idx, 2, path_item)
                    
                    # Notes
                    notes = version.get('notes', '').strip()
                    notes_item = QTableWidgetItem(notes)
                    self.history_table.setItem(idx, 3, notes_item)
            else:
                print("No current file to show history for")
                
        except Exception as e:
            savePlus_core.debug_print(f"Error populating history: {e}")
    
    def open_selected_history_file(self):
        """Open the selected file from the history table"""
        selected_rows = self.history_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            file_path = self.history_table.item(row, 2).text()
            
            if file_path and os.path.exists(file_path):
                self.open_maya_file(file_path)
            else:
                message = f"File not found: {file_path}"
                self.status_bar.showMessage(message, 5000)
                print(message)
    
    def export_history(self):
        """Export version history to a text file"""
        # Get save location
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Version History", "", "Text Files (*.txt)"
        )
        
        if file_path:
            # Add extension if not provided
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            if self.version_history.export_history(file_path):
                message = f"History exported to: {file_path}"
                self.status_bar.showMessage(message, 5000)
                print(message)
            else:
                message = "Error exporting history"
                self.status_bar.showMessage(message, 5000)
                print(message)
    
    def on_tab_changed(self, index):
        """Handle tab changed event"""
        if index == 1:  # History tab
            self.populate_history()
            self.populate_recent_files()
    
    def show_preferences(self):
        """Show the preferences tab"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentWidget(self.preferences_tab)
    
    def show_about(self):
        """Show the about dialog"""
        about_dialog = savePlus_ui_components.AboutDialog(self)
        about_dialog.exec()
    
    def show_first_time_warning(self):
        """Show the first-time save warning dialog"""
        # Get the current interval setting
        reminder_interval = self.reminder_interval_spinbox.value()
        
        warning_dialog = savePlus_ui_components.TimedWarningDialog(
            self, 
            first_time=True,
            interval=reminder_interval
        )
        result = warning_dialog.exec()
        
        # If user chose to disable warnings
        if warning_dialog.get_disable_warnings():
            self.enable_timed_warning.setChecked(False)
    
    def generate_filename(self):
        """Generate a filename based on the name generator inputs"""
        assignment_letter = self.assignment_letter_combo.currentText()
        assignment_num = str(self.assignment_spinbox.value()).zfill(2)
        last_name = self.lastname_input.text()
        first_name = self.firstname_input.text()
        version_type = self.version_type_combo.currentText()
        version_num = str(self.version_number_spinbox.value()).zfill(2)
        
        if not last_name or not first_name:
            QMessageBox.warning(self, "Missing Information", 
                               "Please enter both Last Name and First Name")
            return
        
        # Format: X##_LastName_FirstName_wip_## (where X is the assignment letter)
        new_filename = f"{assignment_letter}{assignment_num}_{last_name}_{first_name}_{version_type}_{version_num}"
        
        # Update the filename input
        self.filename_input.setText(new_filename)
        
        # Update preview
        self.update_filename_preview()
        
        # Save settings
        self.save_name_generator_settings()
        
        print(f"Generated filename: {new_filename}")
    
    def reset_name_generator(self):
        """Reset name generator fields to defaults"""
        self.assignment_letter_combo.setCurrentIndex(0)  # Reset to 'A'
        self.assignment_spinbox.setValue(1)
        self.lastname_input.setText("")
        self.firstname_input.setText("")
        self.version_type_combo.setCurrentIndex(0)
        self.version_number_spinbox.setValue(1)
        
        # Update preview
        self.update_filename_preview()
        
        # Save settings
        self.save_name_generator_settings()
        
        print("Name generator reset to defaults")
    
    def update_filename_preview(self):
        """Update the filename preview label"""
        if hasattr(self, 'filename_input') and hasattr(self, 'filename_preview'):
            base_name = self.filename_input.text()
            if base_name:
                # Extension based on dropdown (.ma is first)
                ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
                self.filename_preview.setText(f"{base_name}{ext}")
            else:
                self.filename_preview.setText("No filename")
    
    def toggle_timed_warning(self, state):
        """Toggle the timed warning feature on or off"""
        if hasattr(self, 'save_timer'):
            if state == Qt.Checked:
                self.save_timer.start(60000)  # Check every minute
                reminder_interval = self.reminder_interval_spinbox.value()
                print(f"[SavePlus Debug] Save reminder ENABLED with {reminder_interval}-minute interval")
                print(f"[SavePlus Debug] Timer check frequency: every 60 seconds")
            else:
                self.save_timer.stop()
                print("[SavePlus Debug] Save reminder DISABLED")
            
            # Save setting
            cmds.optionVar(iv=(self.OPT_VAR_ENABLE_TIMED_WARNING, state == Qt.Checked))
    
    def check_save_time(self):
        """Check if enough time has passed to show a save reminder"""
        current_time = time.time()
        elapsed_minutes = (current_time - self.last_save_time) / 60
        
        # Get interval from preferences or spinbox
        reminder_interval = self.reminder_interval_spinbox.value()
        
        # Add debug prints to track what's happening
        print(f"[SavePlus Debug] Timer check - Current time: {time.ctime(current_time)}")
        print(f"[SavePlus Debug] Last save time: {time.ctime(self.last_save_time)}")
        print(f"[SavePlus Debug] Elapsed: {elapsed_minutes:.2f} min, Threshold: {reminder_interval} min")
              
        # Show warning if enough time has passed
        if elapsed_minutes >= reminder_interval:
            print(f"[SavePlus Debug] Showing reminder dialog (interval: {reminder_interval} min)")
            # Create dialog with the current reminder interval
            warning_dialog = savePlus_ui_components.TimedWarningDialog(self, interval=reminder_interval)
            
            # Show the dialog and get the user's response
            result = warning_dialog.exec()
            
            # Handle the user's choice
            if result == QDialog.Accepted:
                # User clicked "Save Now" - Ask which save method to use
                msgBox = QMessageBox(self)
                msgBox.setWindowTitle("Save Method")
                msgBox.setText("How would you like to save your file?")

                savePlusButton = msgBox.addButton("Save Plus (Increment)", QMessageBox.ActionRole)
                saveAsNewButton = msgBox.addButton("Save As New", QMessageBox.ActionRole)
                cancelButton = msgBox.addButton("Cancel", QMessageBox.RejectRole)

                msgBox.setDefaultButton(savePlusButton)  # Default to Save Plus
                msgBox.exec()

                clickedButton = msgBox.clickedButton()

                if clickedButton == savePlusButton:
                    save_choice = 0
                elif clickedButton == saveAsNewButton:
                    save_choice = 1
                else:
                    save_choice = 2
                
                if save_choice == 0:  # Save Plus
                    print("[SavePlus Debug] User chose Save Plus")
                    self.save_plus()
                elif save_choice == 1:  # Save As New
                    print("[SavePlus Debug] User chose Save As New")
                    self.save_as_new()
                # If user chooses Cancel (option 2), do nothing
            else:
                # User clicked "Remind Me Later"
                # Reset timer to remind them again in 5 minutes (or some shorter interval)
                shorter_reminder = min(5, reminder_interval/2)  # Either 5 minutes or half the interval, whichever is smaller
                self.last_save_time = current_time - ((reminder_interval - shorter_reminder) * 60)
                print(f"[SavePlus Debug] Reminder postponed. Will remind again in {shorter_reminder} minutes")
        else:
            print(f"[SavePlus Debug] Not time for reminder yet. Next reminder in {reminder_interval - elapsed_minutes:.2f} minutes")
        
    def check_backup_time(self):
        """Check if enough time has passed to create an auto-backup"""
        if not self.pref_enable_auto_backup.isChecked():
            return
            
        current_time = time.time()
        backup_interval = self.pref_backup_interval.value()
        elapsed_minutes = (current_time - self.last_backup_time) / 60
        
        # Create backup if it's been at least as long as the backup interval
        if elapsed_minutes >= backup_interval:
            # Only backup if file is saved and modified
            current_file = cmds.file(query=True, sceneName=True)
            if current_file and cmds.file(query=True, modified=True):
                print(f"Auto-backup triggered after {elapsed_minutes:.1f} minutes")
                if self.create_backup():
                    self.last_backup_time = current_time
    
    def load_option_var(self, name, default_value):
        """Load an option variable with a default value"""
        return savePlus_core.load_option_var(name, default_value)
        
    def adjust_window_size(self):
        """Adjust window size based on content"""
        if not self.auto_resize_enabled:
            return
            
        try:
            # Process events to ensure container widget is properly laid out
            QtCore.QCoreApplication.processEvents()
            
            # Get actual heights of sections instead of fixed estimates
            total_height = 0
            
            # Use actual heights of widgets
            if hasattr(self, 'file_options_section'):
                if not self.file_options_section.is_collapsed():
                    total_height += self.file_options_section.sizeHint().height()
                else:
                    total_height += self.file_options_section.header.height()
                    
            if hasattr(self, 'name_gen_section'):
                if not self.name_gen_section.is_collapsed():
                    total_height += self.name_gen_section.sizeHint().height()
                else:
                    total_height += self.name_gen_section.header.height()
            
            # Add height for save buttons
            total_height += 60  # Buttons with padding
            
            if hasattr(self, 'log_section'):
                if not self.log_section.is_collapsed():
                    total_height += self.log_section.sizeHint().height()
                else:
                    total_height += self.log_section.header.height()
            
            # Add spacing between sections
            total_height += self.container_layout.spacing() * 4  # Account for section spacing
            
            # Add bottom padding
            total_height += 20
            
            # Force the container widget to update its layout
            self.container_widget.updateGeometry()
            
            # Process events to apply resize immediately
            QtCore.QCoreApplication.processEvents()
        except Exception as e:
            savePlus_core.debug_print(f"Error during window resize: {e}")
            # Disable auto-resize if we encounter problems
            self.auto_resize_enabled = False
    
    def save_name_generator_settings(self):
        """Save name generator settings to option variables"""
        try:
            cmds.optionVar(sv=(self.OPT_VAR_ASSIGNMENT_LETTER, self.assignment_letter_combo.currentText()))
            cmds.optionVar(iv=(self.OPT_VAR_ASSIGNMENT_NUMBER, self.assignment_spinbox.value()))
            cmds.optionVar(sv=(self.OPT_VAR_LAST_NAME, self.lastname_input.text()))
            cmds.optionVar(sv=(self.OPT_VAR_FIRST_NAME, self.firstname_input.text()))
            cmds.optionVar(sv=(self.OPT_VAR_VERSION_TYPE, self.version_type_combo.currentText()))
            cmds.optionVar(iv=(self.OPT_VAR_VERSION_NUMBER, self.version_number_spinbox.value()))
        except Exception as e:
            savePlus_core.debug_print(f"Error saving name generator settings: {e}")
    
    def save_preferences(self):
        """Save all preference settings"""
        try:
            # Save file type preference
            file_type_index = self.pref_default_filetype.currentIndex()
            cmds.optionVar(iv=(self.OPT_VAR_DEFAULT_FILETYPE, file_type_index))
            
            # Save auto-save interval
            auto_save_interval = self.pref_auto_save_interval.value()
            cmds.optionVar(iv=(self.OPT_VAR_AUTO_SAVE_INTERVAL, auto_save_interval))
            
            # Sync the reminder interval with the main tab spinner
            if hasattr(self, 'reminder_interval_spinbox'):
                self.reminder_interval_spinbox.setValue(auto_save_interval)
            
            # Save path preferences
            default_path = self.pref_default_path.text()
            cmds.optionVar(sv=(self.OPT_VAR_DEFAULT_SAVE_PATH, default_path))
            
            project_path = self.pref_project_path.text()
            cmds.optionVar(sv=(self.OPT_VAR_PROJECT_PATH, project_path))
            
            # Save UI preferences
            cmds.optionVar(iv=(self.OPT_VAR_FILE_EXPANDED, int(self.pref_file_expanded.isChecked())))
            cmds.optionVar(iv=(self.OPT_VAR_NAME_EXPANDED, int(self.pref_name_expanded.isChecked())))
            cmds.optionVar(iv=(self.OPT_VAR_LOG_EXPANDED, int(self.pref_log_expanded.isChecked())))
            
            # Save new preferences
            cmds.optionVar(iv=(self.OPT_VAR_ENABLE_AUTO_BACKUP, int(self.pref_enable_auto_backup.isChecked())))
            cmds.optionVar(iv=(self.OPT_VAR_BACKUP_INTERVAL, self.pref_backup_interval.value()))
            cmds.optionVar(iv=(self.OPT_VAR_ADD_VERSION_NOTES, int(self.add_version_notes.isChecked())))
            
            # Update backup timer
            if self.pref_enable_auto_backup.isChecked():
                if not self.backup_timer.isActive():
                    self.backup_timer.start(60000)
            else:
                if self.backup_timer.isActive():
                    self.backup_timer.stop()
            
            # Apply UI settings immediately
            self.apply_ui_settings()
            
            print("Preferences saved successfully")
            self.status_bar.showMessage("Preferences saved successfully", 5000)
        except Exception as e:
            error_message = f"Error saving preferences: {e}"
            print(error_message)
            self.status_bar.showMessage(error_message, 5000)

            # Update save location display to reflect new preferences
            self.update_save_location_display()
    
    def load_preferences(self):
        """Load preference settings"""
        try:
            # Load file type preference
            if cmds.optionVar(exists=self.OPT_VAR_DEFAULT_FILETYPE):
                file_type_index = cmds.optionVar(q=self.OPT_VAR_DEFAULT_FILETYPE)
                self.pref_default_filetype.setCurrentIndex(file_type_index)
            
            # Load auto-save interval
            if cmds.optionVar(exists=self.OPT_VAR_AUTO_SAVE_INTERVAL):
                auto_save_interval = cmds.optionVar(q=self.OPT_VAR_AUTO_SAVE_INTERVAL)
                self.pref_auto_save_interval.setValue(auto_save_interval)
            
            # Load path preferences
            if cmds.optionVar(exists=self.OPT_VAR_DEFAULT_SAVE_PATH):
                default_path = cmds.optionVar(q=self.OPT_VAR_DEFAULT_SAVE_PATH)
                self.pref_default_path.setText(default_path)
            
            if cmds.optionVar(exists=self.OPT_VAR_PROJECT_PATH):
                project_path = cmds.optionVar(q=self.OPT_VAR_PROJECT_PATH)
                self.pref_project_path.setText(project_path)
            
            # Load UI preferences
            if cmds.optionVar(exists=self.OPT_VAR_FILE_EXPANDED):
                file_expanded = bool(cmds.optionVar(q=self.OPT_VAR_FILE_EXPANDED))
                self.pref_file_expanded.setChecked(file_expanded)
            
            if cmds.optionVar(exists=self.OPT_VAR_NAME_EXPANDED):
                name_expanded = bool(cmds.optionVar(q=self.OPT_VAR_NAME_EXPANDED))
                self.pref_name_expanded.setChecked(name_expanded)
            
            if cmds.optionVar(exists=self.OPT_VAR_LOG_EXPANDED):
                log_expanded = bool(cmds.optionVar(q=self.OPT_VAR_LOG_EXPANDED))
                self.pref_log_expanded.setChecked(log_expanded)
                
            # Load new preferences
            if cmds.optionVar(exists=self.OPT_VAR_ENABLE_AUTO_BACKUP):
                enable_auto_backup = bool(cmds.optionVar(q=self.OPT_VAR_ENABLE_AUTO_BACKUP))
                self.pref_enable_auto_backup.setChecked(enable_auto_backup)
                
            if cmds.optionVar(exists=self.OPT_VAR_BACKUP_INTERVAL):
                backup_interval = cmds.optionVar(q=self.OPT_VAR_BACKUP_INTERVAL)
                self.pref_backup_interval.setValue(backup_interval)
                
            if cmds.optionVar(exists=self.OPT_VAR_ADD_VERSION_NOTES):
                add_version_notes = bool(cmds.optionVar(q=self.OPT_VAR_ADD_VERSION_NOTES))
                self.add_version_notes.setChecked(add_version_notes)
            
            # Apply UI settings
            self.apply_ui_settings()
        except Exception as e:
            savePlus_core.debug_print(f"Error loading preferences: {e}")

        # Initialize save location based on default path
        if cmds.optionVar(exists=self.OPT_VAR_DEFAULT_SAVE_PATH):
            default_path = cmds.optionVar(q=self.OPT_VAR_DEFAULT_SAVE_PATH)
            
            # If the filename input is empty and no current file is open,
            # use the default path
            current_file = cmds.file(query=True, sceneName=True)
            if not current_file and not self.filename_input.text():
                self.selected_directory = default_path
                # Add a placeholder text to show the path
                self.filename_input.setPlaceholderText("untitled.ma")
                
        # Update save location display
        self.update_save_location_display()

    def apply_ui_settings(self):
        """Apply UI settings from preferences"""
        try:
            # Set collapsed state of sections based on preferences
            file_expanded = self.pref_file_expanded.isChecked()
            name_expanded = self.pref_name_expanded.isChecked()
            log_expanded = self.pref_log_expanded.isChecked()
            
            # Only change state if different from current state to avoid unnecessary toggling
            if self.file_options_section.is_collapsed() == file_expanded:
                self.file_options_section.toggle_content()
                
            if self.name_gen_section.is_collapsed() == name_expanded:
                self.name_gen_section.toggle_content()
                
            if self.log_section.is_collapsed() == log_expanded:
                self.log_section.toggle_content()
            
            # Adjust window size to reflect changes
            self.adjust_window_size()
        except Exception as e:
            savePlus_core.debug_print(f"Error applying UI settings: {e}")
