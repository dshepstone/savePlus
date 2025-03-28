"""
SavePlus Main - Main UI class and functionality for the SavePlus tool
Part of the SavePlus toolset for Maya 2025
"""
import os
import time
import re
import traceback
import os
import time
import traceback

from maya import cmds, mel
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
TIMER_COUNT = 0  # Add this line to track timer firing count

def truncate_path(path, max_length=40):
    """
    Truncate a path for display by preserving the beginning and end
    while replacing the middle with ellipsis if too long.
    """
    if not path or len(path) <= max_length:
        return path
        
    # Keep the drive or network location part
    drive, remainder = os.path.splitdrive(path)
    
    # Separate the filename from the directory path
    directory, filename = os.path.split(remainder)
    
    # Calculate how much of the directory we can show
    # We want to show the beginning and end of the directory path
    available_length = max_length - len(drive) - len(filename) - 5  # 5 for "/.../"
    
    if available_length <= 0:
        # Path is too long, just show drive and filename
        return f"{drive}/.../{filename}"
    
    half_length = available_length // 2
    
    # Get the beginning and end of the directory path
    dir_start = directory[:half_length]
    dir_end = directory[-half_length:] if half_length > 0 else ""
    
    return f"{drive}{dir_start}/.../{dir_end}/{filename}"

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
    OPT_VAR_PIPELINE_STAGE = "SavePlusPipelineStage"  # New option var for pipeline stage
    
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

            # Create save buttons at the TOP of interface
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 10, 0, 10)  # Add some vertical padding

            # Style buttons with consistent, modern appearance
            button_style = """
            QPushButton {
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #3a3a3a, stop: 1 #2a2a2a);
                border: 1px solid #444444;
                padding: 6px 12px;
                min-height: 30px;
                color: #ffffff;  /* White text for maximum contrast */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #4a4a4a, stop: 1 #3a3a3a);
                color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #2a2a2a, stop: 1 #3a3a3a);
                color: #ffffff;
            }
            """

            # Create buttons with keyboard shortcut indicators
            save_button = QPushButton("Save Plus (Ctrl+S)")
            save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
            save_button.setMinimumHeight(40)
            save_button.setStyleSheet(button_style)
            save_button.clicked.connect(self.save_plus)

            save_new_button = QPushButton("Save As New (Ctrl+Shift+S)")
            save_new_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            save_new_button.setMinimumHeight(40)
            save_new_button.setStyleSheet(button_style)
            save_new_button.clicked.connect(self.save_as_new)

            # New backup button
            backup_button = QPushButton("Create Backup (Ctrl+B)")
            backup_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
            backup_button.setMinimumHeight(40)
            backup_button.setStyleSheet(button_style)
            backup_button.clicked.connect(self.create_backup)
            backup_button.setToolTip("Create a backup copy of the current file")

            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(save_new_button)
            buttons_layout.addWidget(backup_button)

            # Add top save buttons to container layout
            self.container_layout.addLayout(buttons_layout)

            # Last save indicator and status
            last_save_layout = QHBoxLayout()
            last_save_layout.setContentsMargins(4, 2, 4, 2)

            last_save_container = QFrame()
            last_save_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.2); border-radius: 3px;")
            last_save_container.setLayout(last_save_layout)

            self.last_save_indicator = QLabel("●")
            self.last_save_indicator.setStyleSheet("color: #4CAF50; font-size: 18px;")
            self.last_save_indicator.setFixedWidth(20)

            self.last_save_status = QLabel("Last saved: N/A")
            self.last_save_status.setStyleSheet("color: #ffffff; font-size: 10px;")

            last_save_layout.addWidget(self.last_save_indicator)
            last_save_layout.addWidget(self.last_save_status)
            last_save_layout.addStretch()

            self.container_layout.addWidget(last_save_container)

            # Add a subtle separator between buttons and sections
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
            self.container_layout.addWidget(separator)
            self.container_layout.addSpacing(10)  # Add space after separator

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
            self.filename_input.textChanged.connect(self.update_version_preview)
            self.filename_input.setMaximumWidth(350)  # Limit maximum width
            self.filename_input.setTextMargins(2, 0, 2, 0)  # Add text margins
            self.filename_input.home(False)  # Ensure text starts from beginning
            # Store full path separately from display name
            self.current_full_path = ""
            filename_layout.addWidget(self.filename_input)

            # Get current file name if available
            current_file = cmds.file(query=True, sceneName=True)
            if current_file:
                self.filename_input.setText(os.path.basename(current_file))

            # Create a button group for path options
            path_buttons_layout = QHBoxLayout()
            path_buttons_layout.setSpacing(4)  # Tighter spacing between buttons

            browse_button = QPushButton("Browse")  # Even shorter text
            browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
            browse_button.clicked.connect(self.browse_file)
            browse_button.setFixedWidth(80)  # Even smaller width if needed
            browse_button.setToolTip("Browse for a directory to save to")

            reference_path_button = QPushButton("Reference")
            reference_path_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogToParent))
            reference_path_button.clicked.connect(self.use_reference_path)
            reference_path_button.setFixedWidth(80)  # Matching width
            reference_path_button.setToolTip("Use path from selected reference")

            path_buttons_layout.addWidget(browse_button)
            path_buttons_layout.addWidget(reference_path_button)
            filename_layout.addLayout(path_buttons_layout)

            # Add to form layout
            file_layout.addRow("Filename:", filename_layout)

            # Add save location display label with path visualization
            self.save_location_label = QLabel()
            self.save_location_label.setStyleSheet("color: #0066CC; font-size: 10px; background-color: #f5f5f5; padding: 3px; border-radius: 2px;")
            file_layout.addRow("Save Location:", self.save_location_label)

            # Add version preview
            version_preview_layout = QHBoxLayout()
            version_preview_label = QLabel("Next version:")
            version_preview_label.setStyleSheet("color: #666666; font-size: 11px;")

            self.version_preview_icon = QLabel("→")
            self.version_preview_icon.setStyleSheet("color: #0066CC; font-weight: bold;")

            self.version_preview_text = QLabel("N/A")
            self.version_preview_text.setStyleSheet("color: #0066CC; font-weight: bold;")

            version_preview_layout.addWidget(version_preview_label)
            version_preview_layout.addWidget(self.version_preview_icon)
            version_preview_layout.addWidget(self.version_preview_text)
            version_preview_layout.addStretch()

            file_layout.addRow("", version_preview_layout)

            # Add file type selection
            self.filetype_combo = QComboBox()
            self.filetype_combo.addItems(["Maya ASCII (.ma)", "Maya Binary (.mb)"])
            self.filetype_combo.setFixedWidth(180)
            self.filetype_combo.currentIndexChanged.connect(self.update_filename_preview)
            self.filetype_combo.currentIndexChanged.connect(self.update_version_preview)
            
            # Add option to use the current directory
            self.use_current_dir = QCheckBox("Use current directory")
            self.use_current_dir.setChecked(True)
            
            # Create layout for save reminder controls
            save_reminder_layout = QHBoxLayout()
            save_reminder_layout.setContentsMargins(0, 0, 0, 0)

            # Add timed save reminder checkbox with updated label
            self.enable_timed_warning = QCheckBox("Enable save reminder every")
            self.enable_timed_warning.setChecked(False)  # Explicitly set to False by default
            self.enable_timed_warning.stateChanged.connect(self.toggle_timed_warning)
            save_reminder_layout.addWidget(self.enable_timed_warning)

            # Add spinner for reminder interval
            self.reminder_interval_spinbox = QSpinBox()
            self.reminder_interval_spinbox.setRange(1, 60)
            self.reminder_interval_spinbox.setValue(15)  # Default to 15 minutes
            self.reminder_interval_spinbox.setSuffix(" minutes")
            self.reminder_interval_spinbox.setFixedWidth(100)
            self.reminder_interval_spinbox.valueChanged.connect(self.update_reminder_interval)
            save_reminder_layout.addWidget(self.reminder_interval_spinbox)
            
            # Add version notes option
            self.add_version_notes = QCheckBox("Add version notes when saving")
            self.add_version_notes.setChecked(self.load_option_var(self.OPT_VAR_ADD_VERSION_NOTES, False))
            self.add_version_notes.setToolTip("Add notes for each version to track changes")
            
            # Add to form layout
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
            
            # Pipeline stage dropdown (replaces the simple version_type_combo)
            pipeline_stage_layout = QHBoxLayout()
            self.pipeline_stage_label = QLabel("Pipeline Stage:")

            # Create the pipeline stage dropdown
            self.pipeline_stage_combo = QComboBox()
            self.pipeline_stage_combo.addItems([
                "Layout", 
                "Planning", 
                "Blocking", 
                "Blocking Plus", 
                "Spline", 
                "Polish", 
                "Lighting", 
                "Final"
            ])
            saved_stage = self.load_option_var(self.OPT_VAR_PIPELINE_STAGE, "Blocking")
            index = self.pipeline_stage_combo.findText(saved_stage)
            if index >= 0:
                self.pipeline_stage_combo.setCurrentIndex(index)
            self.pipeline_stage_combo.setFixedWidth(120)

            # Status dropdown (WIP or Final)
            self.version_status_combo = QComboBox()
            self.version_status_combo.addItems(["wip", "final"])
            saved_type = self.load_option_var(self.OPT_VAR_VERSION_TYPE, "wip")
            index = self.version_status_combo.findText(saved_type)
            if index >= 0:
                self.version_status_combo.setCurrentIndex(index)
            self.version_status_combo.setFixedWidth(80)

            self.pipeline_stage_combo.setItemData(0, "Camera angles, character and prop placement, and shot timing established", Qt.ToolTipRole)  # Layout
            self.pipeline_stage_combo.setItemData(1, "Performance planning using reference footage and thumbnail sketches", Qt.ToolTipRole)  # Planning / Reference
            self.pipeline_stage_combo.setItemData(2, "Key storytelling poses blocked in stepped mode with rough timing", Qt.ToolTipRole)  # Blocking
            self.pipeline_stage_combo.setItemData(3, "Primary and secondary breakdowns added; refined timing, spacing, and arcs", Qt.ToolTipRole)  # Blocking Plus
            self.pipeline_stage_combo.setItemData(4, "Converted to spline; cleaned interpolation, arcs, and spacing", Qt.ToolTipRole)  # Spline
            self.pipeline_stage_combo.setItemData(5, "Final polish: facial animation, overlap, follow-through, and subtle details", Qt.ToolTipRole)  # Polish
            self.pipeline_stage_combo.setItemData(6, "Lighting pass: establishing mood, depth, and render look", Qt.ToolTipRole)  # Lighting
            self.pipeline_stage_combo.setItemData(7, "Shot approved: animation and visuals are final and ready for comp or submission", Qt.ToolTipRole)  # Final Output

            # Add both dropdowns to the layout
            pipeline_stage_layout.addWidget(self.pipeline_stage_combo)
            pipeline_stage_layout.addWidget(self.version_status_combo)
            pipeline_stage_layout.addStretch()
            
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
            name_gen_layout.addRow("Stage:", pipeline_stage_layout)
            name_gen_layout.addRow("Version:", version_number_layout)
            name_gen_layout.addRow("Preview:", self.filename_preview)
            name_gen_layout.addRow("", buttons_layout)
            
            self.name_gen_section.add_widget(name_gen)
            self.container_layout.addWidget(self.name_gen_section)
            
            # Add name_gen_section toggled signal connection
            self.name_gen_section.toggled.connect(self.adjust_window_size)
            
            # Add Quick Notes section
            quick_notes_layout = QHBoxLayout()
            quick_notes_layout.setContentsMargins(0, 5, 0, 5)

            self.quick_note_input = QLineEdit()
            self.quick_note_input.setPlaceholderText("Add a quick note for next save...")

            quick_notes_layout.addWidget(QLabel("Quick Note:"))
            quick_notes_layout.addWidget(self.quick_note_input)

            self.container_layout.addLayout(quick_notes_layout)
            
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
            self.pref_name_expanded.setChecked(False)  # Default to collapsed
            ui_layout.addRow("", self.pref_name_expanded)
            
            self.pref_log_expanded = QCheckBox("Log Output section expanded by default")
            self.pref_log_expanded.setChecked(False)  # Default to collapsed
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
            self.update_version_preview()
            
            # Setup log redirector
            self.log_redirector = savePlus_ui_components.LogRedirector(self.log_text)
            self.log_redirector.start_redirect()
            
            # Log initialization message
            print("SavePlus UI initialized successfully")
            
           # Setup timer for save reminders - MAKE SURE THIS IS IN __init__
            self.timer_job_id = None  # Initialize scriptJob ID
            self.last_save_time = time.time()
            self.last_timer_check = time.time()
            self.save_timer = QTimer()  # Create without parent for Maya compatibility
            self.save_timer.setTimerType(QtCore.Qt.CoarseTimer)  # More reliable timer type
            self.save_timer.timeout.connect(self.check_save_time)
            print("[SavePlus Debug] Qt timer created (not started)")

            # Enable this timer in Maya's event loop - KEEP THIS IMPORTANT CODE
            if hasattr(self, 'save_timer'):
                # Connect to Maya's main loop if needed
                try:
                    from maya import OpenMayaUI as omui
                    print("[SavePlus Debug] Connected timer to Maya's event loop")
                except Exception as e:
                    print(f"[SavePlus Debug] Using standard Qt timer: {e}")

            # Load timer preference without triggering stateChanged
            timer_enabled = self.load_option_var(self.OPT_VAR_ENABLE_TIMED_WARNING, False)
            print(f"[SavePlus Debug] Loaded timer preference: enabled={timer_enabled}")

            # Set checkbox state without triggering signals
            self.enable_timed_warning.blockSignals(True)
            self.enable_timed_warning.setChecked(timer_enabled)
            self.enable_timed_warning.blockSignals(False)

            # Schedule timer setup if enabled in preferences (delay to ensure UI is ready)
            if timer_enabled:
                print("[SavePlus Debug] Timer enabled in preferences, scheduling activation")
                QtCore.QTimer.singleShot(1000, self.setup_timer)
            else:
                print("[SavePlus Debug] Timer disabled in preferences")

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

            # Initialize the timer system after UI is loaded
            QtCore.QTimer.singleShot(2000, self.bootstrap_timer)

            # Force multiple initial timer checks to verify operation
            if self.enable_timed_warning.isChecked():
                print("\n" + "#"*70)
                print("## STARTING TIMER VERIFICATION SEQUENCE")
                print("#"*70 + "\n")
                
                # Reset the counter
                if not hasattr(SavePlusUI, 'TIMER_COUNT'):
                    SavePlusUI.TIMER_COUNT = 0
                SavePlusUI.TIMER_COUNT = 0
                
                # Simulate last save being 4 minutes ago for immediate testing
                print("[SavePlus Debug] Setting up timer for immediate testing")
                self.last_save_time = time.time() - (4 * 60)
                
                # Schedule multiple checks at different intervals
                QtCore.QTimer.singleShot(1000, lambda: print("\n[VERIFY] Scheduling initial timer check #1"))
                QtCore.QTimer.singleShot(1500, self.check_save_time)
                
                QtCore.QTimer.singleShot(6000, lambda: print("\n[VERIFY] Scheduling initial timer check #2"))
                QtCore.QTimer.singleShot(6500, self.check_save_time)
                
                QtCore.QTimer.singleShot(11000, lambda: print("\n[VERIFY] Scheduling initial timer check #3"))
                QtCore.QTimer.singleShot(11500, self.check_save_time)
                
                # Force UI update
                QtCore.QTimer.singleShot(16000, lambda: print("[SavePlus Debug] Timer verification sequence complete"))
                
                # Setup a more robust timer initialization
                self.save_timer = QTimer()
                self.save_timer.setTimerType(QtCore.Qt.CoarseTimer)
                self.save_timer.timeout.connect(self.check_save_time)
                print("[DEBUG] Qt timer created with proper signal connection")

                # Load the timer state from preferences without triggering toggle
                timer_enabled = self.load_option_var(self.OPT_VAR_ENABLE_TIMED_WARNING, False)
                if timer_enabled:
                    print("[DEBUG] Timer should be enabled from preferences")
                    # Block signals to prevent immediate toggle
                    self.enable_timed_warning.blockSignals(True)
                    self.enable_timed_warning.setChecked(True)
                    self.enable_timed_warning.blockSignals(False)
                    # Start timer after a delay
                    QtCore.QTimer.singleShot(1000, lambda: self.toggle_timed_warning(2))

        except Exception as e:
            error_message = f"Error initializing SavePlus UI: {str(e)}"
            print(error_message)
            traceback.print_exc()
            cmds.confirmDialog(title="SavePlus Error", 
                            message=f"Error loading SavePlus: {str(e)}\n\nCheck script editor for details.", 
                            button=["OK"], defaultButton="OK")

    def update_filename_display(self, full_path):
        """Update the filename input to show only the basename while storing the full path"""
        self.current_full_path = full_path
        basename = os.path.basename(full_path) if full_path else ""
        self.filename_input.setText(basename)
        self.filename_input.setToolTip(full_path)  # Show full path on hover
        self.update_filename_preview()
        self.update_version_preview()

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
                self.update_filename_display(new_path)
                self.filename_input.setText(os.path.basename(new_path))
                self.filename_input.setToolTip(new_path)  # Show full path on hover
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
            full_path = ""
            if self.selected_directory:
                full_path = self.selected_directory
            elif hasattr(self, 'pref_default_path') and self.pref_default_path.text() and self.use_current_dir.isChecked():
                full_path = self.pref_default_path.text()
            else:
                current_file = cmds.file(query=True, sceneName=True)
                if current_file:
                    full_path = os.path.dirname(current_file)
                else:
                    full_path = "Default Maya project"
            
            # Display truncated path but set full path as tooltip
            truncated_path = truncate_path(full_path, 40)  # Adjust max_length as needed
            self.save_location_label.setText(truncated_path)
            self.save_location_label.setToolTip(full_path)  # Show full path on hover

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
        filename = self.current_full_path if self.current_full_path else self.filename_input.text()
       
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
            # Check for quick note first
            if hasattr(self, 'quick_note_input') and self.quick_note_input.text().strip():
                version_notes = self.quick_note_input.text().strip()
                self.quick_note_input.clear()  # Clear after using
                print("Quick note added")
            else:
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

                # Update last save status
                self.last_save_indicator.setStyleSheet("color: #4CAF50; font-size: 18px;")  # Green
                self.last_save_indicator.setToolTip("Recent save - you're up to date")
                save_time = time.strftime("%H:%M:%S", time.localtime())
                self.last_save_status.setText(f"Last saved: {save_time}")
                self.update_version_preview()

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
        # Get version notes if enabled
        version_notes = ""
        if self.add_version_notes.isChecked():
            # Check for quick note first
            if hasattr(self, 'quick_note_input') and self.quick_note_input.text().strip():
                version_notes = self.quick_note_input.text().strip()
                self.quick_note_input.clear()  # Clear after using
                print("Quick note added")
            else:
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
                      
            # Update last save status
            self.last_save_indicator.setStyleSheet("color: #4CAF50; font-size: 18px;")  # Green
            self.last_save_indicator.setToolTip("Recent save - you're up to date")
            save_time = time.strftime("%H:%M:%S", time.localtime())
            self.last_save_status.setText(f"Last saved: {save_time}")
            self.update_version_preview()

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
            self.filename_input.setToolTip(file_path)  # Show full path on hover
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
        
        # Get pipeline stage and status - this is the most important change
        pipeline_stage = self.pipeline_stage_combo.currentText().lower()
        version_status = self.version_status_combo.currentText()
        
        # Combine stage and status for the version type
        version_type = f"{pipeline_stage}_{version_status}"
        
        version_num = str(self.version_number_spinbox.value()).zfill(2)
        
        if not last_name or not first_name:
            QMessageBox.warning(self, "Missing Information", 
                            "Please enter both Last Name and First Name")
            return
        
        # Format: X##_LastName_FirstName_stage_status_## (where X is the assignment letter)
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
        
        # Reset pipeline stage and status
        self.pipeline_stage_combo.setCurrentIndex(2)  # Default to Blocking
        self.version_status_combo.setCurrentIndex(0)  # Default to WIP
        
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
        """Toggle the timed warning feature using Maya's scriptJob system"""
        print(f"\n[DEBUG] toggle_timed_warning called with state: {state}")
        print(f"[DEBUG] State type: {type(state)}, Qt.Checked value: {Qt.Checked}")
        
        try:
            # Use direct integer comparison - 2 is checked, 0 is unchecked
            if state == 2 or state is True or state == Qt.Checked:
                print("\n" + "="*70)
                print("               TIMER ENABLED - USING MAYA SCRIPTJOB")
                print("="*70 + "\n")
                
                # Set last save time to current time
                self.last_save_time = time.time()
                
                # Remove any existing scriptJob
                if hasattr(self, 'timer_job_id') and self.timer_job_id is not None:
                    try:
                        cmds.scriptJob(kill=self.timer_job_id)
                        print(f"[DEBUG] Removed existing timer scriptJob: {self.timer_job_id}")
                    except Exception as e:
                        print(f"[DEBUG] Error removing timer scriptJob: {e}")
                
                # Use directly scheduled Qt timer instead of scriptJob
                # This is simpler and more reliable across Maya versions
                if hasattr(self, 'save_timer'):
                    self.save_timer.stop()  # Stop if already running
                    self.save_timer.setInterval(5000)  # 5 seconds
                    self.save_timer.start()
                    print("[DEBUG] Started Qt timer with 5-second interval")
                    print(f"[DEBUG] Timer active status: {self.save_timer.isActive()}")
                
                # Save the setting
                cmds.optionVar(iv=(self.OPT_VAR_ENABLE_TIMED_WARNING, 1))
                
            else:
                print("\n" + "="*70)
                print("               TIMER DISABLED - STOPPING TIMER")
                print("="*70 + "\n")
                
                # Stop Qt timer
                if hasattr(self, 'save_timer') and self.save_timer.isActive():
                    self.save_timer.stop()
                    print("[DEBUG] Stopped Qt timer")
                
                # Kill the scriptJob if it exists (just to be thorough)
                if hasattr(self, 'timer_job_id') and self.timer_job_id is not None:
                    try:
                        cmds.scriptJob(kill=self.timer_job_id)
                        print(f"[DEBUG] Killed timer scriptJob: {self.timer_job_id}")
                        self.timer_job_id = None
                    except Exception as e:
                        print(f"[DEBUG] Error killing scriptJob: {e}")
                        self.timer_job_id = None
                
                # Save the setting
                cmds.optionVar(iv=(self.OPT_VAR_ENABLE_TIMED_WARNING, 0))
                
        except Exception as e:
            print(f"[ERROR] Timer toggle failed: {str(e)}")
            traceback.print_exc()
    
    def check_save_time(self):
        """Check if enough time has passed to show a save reminder"""
        try:
            # Increment and display counter - VERY VISIBLE logging
            if not hasattr(SavePlusUI, 'TIMER_COUNT'):
                SavePlusUI.TIMER_COUNT = 0
            
            SavePlusUI.TIMER_COUNT += 1
            print("\n" + "*"*70)
            print(f"*** TIMER CHECK #{SavePlusUI.TIMER_COUNT} at {time.strftime('%H:%M:%S')} ***")
            print("*"*70 + "\n")
            
            # Get current time and calculate elapsed time
            current_time = time.time()
            elapsed_minutes = (current_time - self.last_save_time) / 60
            
            # CRITICAL FIX: Get interval BEFORE using it
            reminder_interval = self.reminder_interval_spinbox.value()
            
            # Detailed debug information
            print(f"[Timer Status] Last save: {time.strftime('%H:%M:%S', time.localtime(self.last_save_time))}")
            print(f"[Timer Status] Elapsed time: {elapsed_minutes:.2f} minutes")
            print(f"[Timer Status] Reminder threshold: {reminder_interval} minutes")
            print(f"[Timer Status] Timer interval: {self.save_timer.interval()/1000} seconds")
            print(f"[Timer Status] Timer active: {self.save_timer.isActive()}")
            
            # Update indicator color based on time since last save
            if elapsed_minutes >= reminder_interval:
                # Red - Time to save
                self.last_save_indicator.setStyleSheet("color: #F44336; font-size: 18px;")
                self.last_save_indicator.setToolTip("Save recommended - it's been a while")
                print("[Timer Status] Indicator: RED (save needed)")
            elif elapsed_minutes >= reminder_interval * 0.7:
                # Yellow - Getting close to reminder time
                self.last_save_indicator.setStyleSheet("color: #FFC107; font-size: 18px;")
                self.last_save_indicator.setToolTip("Consider saving soon")
                print("[Timer Status] Indicator: YELLOW (getting close)")
            else:
                # Green - Recent save
                self.last_save_indicator.setStyleSheet("color: #4CAF50; font-size: 18px;")
                self.last_save_indicator.setToolTip("Recent save - you're up to date")
                print("[Timer Status] Indicator: GREEN (recently saved)")
            
            # Show warning if enough time has passed
            if elapsed_minutes >= reminder_interval:
                print("\n" + "!"*70)
                print(f"!!! TIME TO SHOW REMINDER DIALOG !!! (Elapsed: {elapsed_minutes:.2f} min > Threshold: {reminder_interval} min)")
                print("!"*70 + "\n")
                
                # Create and show the dialog
                warning_dialog = savePlus_ui_components.TimedWarningDialog(self, first_time=False, interval=int(elapsed_minutes))
                
                # Force dialog to stay on top
                warning_dialog.setWindowFlags(warning_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
                
                # Show the dialog and get response
                print("[Dialog] Showing save reminder dialog...")
                result = warning_dialog.exec()
                
                if result == QDialog.Accepted:
                    # User clicked "Save Now" - Ask which save method to use
                    print("[Dialog] User chose to save now")
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
                        print("[Dialog] User chose Save Plus (increment)")
                        self.save_plus()
                    elif clickedButton == saveAsNewButton:
                        print("[Dialog] User chose Save As New")
                        self.save_as_new()
                    else:
                        print("[Dialog] User cancelled save operation")
                else:
                    # User clicked "Remind Me Later"
                    print("[Dialog] User chose to be reminded later")
                    # Reset timer to remind again in 2 minutes
                    self.last_save_time = current_time - ((reminder_interval - 2) * 60)
                    print(f"[Timer Status] Last save time adjusted to remind again in 2 minutes")
            else:
                print(f"[Timer Status] Not time for reminder yet. Will remind in {reminder_interval - elapsed_minutes:.2f} minutes")
            
            # End of timer check
            print("\n" + "-"*70)
            print(f"--- TIMER CHECK #{SavePlusUI.TIMER_COUNT} COMPLETED ---")
            print("-"*70 + "\n")
            
        except Exception as e:
            # Comprehensive error reporting
            print("\n" + "X"*70)
            print("XXX ERROR IN TIMER CHECK XXX")
            print("X"*70)
            print(f"Error message: {str(e)}")
            print("Stack trace:")
            traceback.print_exc()
            print("X"*70 + "\n")

    def setup_timer(self):
        """Set up the save reminder timer based on current preferences"""
        try:
            if self.enable_timed_warning.isChecked():
                print("[DEBUG] Setting up timer via scriptJob")
                self.toggle_timed_warning(Qt.Checked)
            else:
                print("[DEBUG] Timer setup skipped (not enabled)")
        except Exception as e:
            print(f"[ERROR] Timer setup failed: {str(e)}")
            traceback.print_exc()

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
            
            # Save pipeline stage
            cmds.optionVar(sv=(self.OPT_VAR_PIPELINE_STAGE, self.pipeline_stage_combo.currentText()))
            
            # Save version status
            cmds.optionVar(sv=(self.OPT_VAR_VERSION_TYPE, self.version_status_combo.currentText()))
            
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
            
            # Load timed warning preference
            if cmds.optionVar(exists=self.OPT_VAR_ENABLE_TIMED_WARNING):
                enable_timed_warning = bool(cmds.optionVar(q=self.OPT_VAR_ENABLE_TIMED_WARNING))
                print(f"[DEBUG] Loading timed warning preference: {enable_timed_warning}")
                
                # Only update if different to avoid triggering the stateChanged signal
                if self.enable_timed_warning.isChecked() != enable_timed_warning:
                    self.enable_timed_warning.blockSignals(True)
                    self.enable_timed_warning.setChecked(enable_timed_warning)
                    self.enable_timed_warning.blockSignals(False)

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

    def use_reference_path(self):
        """Extract path from selected referenced node and use it for saving"""
        print("Attempting to use reference path from selection...")
        
        # Get the current selection
        selection = cmds.ls(selection=True)
        
        if not selection:
            self.status_bar.showMessage("No objects selected. Please select a referenced object.", 5000)
            print("No selection found")
            return
        
        # Check if selection is referenced
        reference_nodes = []
        for obj in selection:
            if cmds.referenceQuery(obj, isNodeReferenced=True):
                reference_nodes.append(obj)
        
        if not reference_nodes:
            self.status_bar.showMessage("Selected objects are not references. Please select a referenced object.", 5000)
            print("No referenced objects in selection")
            return
        
        # Get the reference file path
        try:
            # Get the reference node for the first referenced object
            reference_node = cmds.referenceQuery(reference_nodes[0], referenceNode=True)
            
            # Get the file path for this reference
            reference_file = cmds.referenceQuery(reference_node, filename=True)
            print(f"Reference file: {reference_file}")
            
            # Correct way to handle nested references
            # In Maya, when you get a filename from referenceQuery, it already gives
            # the resolved path, so we don't need additional parent handling
            
            # Extract the directory path
            reference_dir = os.path.dirname(reference_file)
            print(f"Using reference directory: {reference_dir}")
            
            # Set this as our new directory
            self.selected_directory = reference_dir
            
            # Update UI
            self.use_current_dir.setChecked(False)
            self.update_save_location_display()
            
            # Extract character/asset name from reference for filename suggestion
            ref_basename = os.path.basename(reference_file)
            asset_name = os.path.splitext(ref_basename)[0]
            
            # Remove common prefixes or namespaces from the asset name if needed
            if '_' in asset_name:
                # Usually character names are after prefixes like "chr_" or "prop_"
                parts = asset_name.split('_')
                if len(parts) > 1 and parts[0].lower() in ['chr', 'prop', 'env', 'rig']:
                    asset_name = '_'.join(parts[1:])  # Remove the prefix
            
            # Ask if user wants to use this name for the file
            if cmds.confirmDialog(
                title='Use Asset Name',
                message=f'Do you want to use "{asset_name}" in your filename?',
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No'
            ) == 'Yes':
                # Get current scene file base name or create a new one
                current_file = cmds.file(query=True, sceneName=True)
                if current_file:
                    current_basename = os.path.basename(current_file)
                    # Insert asset name into filename if not already there
                    if asset_name not in current_basename:
                        name_parts = os.path.splitext(current_basename)
                        new_basename = f"{name_parts[0]}_{asset_name}{name_parts[1]}"
                        self.filename_input.setText(new_basename)
                        print(f"Updated filename to include asset name: {new_basename}")
                else:
                    # Suggest a new filename with asset name
                    suggested_name = f"shot_{asset_name}_v001.ma"
                    self.filename_input.setText(suggested_name)
                    self.filename_input.setToolTip(new_path)  # Show full path on hover
                    print(f"Created new suggested filename: {suggested_name}")
                
                self.update_filename_preview()
            
            # Update the filename input if needed (only if we didn't set it from asset name)
            if not self.filename_input.text():
                current_filename = os.path.basename(cmds.file(query=True, sceneName=True) or "untitled.ma")
                new_path = os.path.join(reference_dir, current_filename)
                self.filename_input.setText(os.path.basename(new_path))
                self.filename_input.setToolTip(new_path)  # Show full path on hover
                self.update_filename_preview()
            
            message = f"Save location set to referenced character path: {reference_dir}"
            self.status_bar.showMessage(message, 5000)
            print(message)
            
        except Exception as e:
            message = f"Error getting reference path: {e}"
            self.status_bar.showMessage(message, 5000)
            print(message)
            traceback.print_exc()

    def update_version_preview(self):
        """Update the version preview to show what the next save will be"""
        try:
            filename = self.filename_input.text()
            if not filename:
                self.version_preview_text.setText("N/A")
                return
                
            # Get the base name and extension
            base_name, ext = os.path.splitext(filename)
            if not ext or (ext.lower() not in ['.ma', '.mb']):
                # Use extension from dropdown
                ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
            
            # Find the trailing number pattern
            match = re.search(r'(\D*)(\d+)(\D*)$', base_name)
            
            if match:
                # If a number is found
                prefix = match.group(1)
                number = match.group(2)
                suffix = match.group(3)
                
                # Increment the number, preserving leading zeros
                new_number = str(int(number) + 1).zfill(len(number))
                new_base_name = prefix + new_number + suffix
                new_filename = new_base_name + ext
                
                # Show original → new
                self.version_preview_text.setText(f"{os.path.basename(filename)} → {new_filename}")
            else:
                # If no number is found, add "02" to the end
                new_base_name = base_name + "02"
                new_filename = new_base_name + ext
                self.version_preview_text.setText(f"{os.path.basename(filename)} → {new_filename}")
        except Exception as e:
            savePlus_core.debug_print(f"Error updating version preview: {e}")
            self.version_preview_text.setText("Error")

    def force_timer_test(self):
        """Force the timer to run for testing purposes"""
        print("\n" + "#"*70)
        print("#     FORCED TIMER TEST - BYPASSING NORMAL ACTIVATION     #")
        print("#"*70 + "\n")
        
        try:
            # Create a brand new timer to avoid any issues with existing one
            test_timer = QTimer()
            test_timer.setTimerType(QtCore.Qt.CoarseTimer)
            
            # Set up a test function to run
            def test_check():
                print(f"[TEST] Direct timer check at {time.strftime('%H:%M:%S')}")
                self.check_save_time()  # Call the regular check method
            
            # Connect and start
            test_timer.timeout.connect(test_check)
            test_timer.start(5000)  # 5 second interval
            
            print(f"[TEST] Direct test timer created and started")
            print(f"[TEST] Timer active: {test_timer.isActive()}")
            
            # Force immediate checks
            test_check()  # Run immediately
            
            # Return the timer so it doesn't get garbage collected
            return test_timer
        
        except Exception as e:
            print(f"[ERROR] Force timer test failed: {str(e)}")
            traceback.print_exc()
            return None

    def check_save_time_maya(self):
        """Maya scriptJob handler for timeChange events"""
        try:
            current_time = time.time()
            
            # Initialize if needed
            if not hasattr(self, 'last_timer_check'):
                self.last_timer_check = 0
                print("[DEBUG] Initialized last_timer_check")
                
            # Only check every 5 seconds to avoid too frequent checks
            time_since_check = current_time - self.last_timer_check
            if time_since_check < 5:
                return
                
            # Update last check time
            self.last_timer_check = current_time
            print(f"[DEBUG] Maya timeChange timer check at {time.strftime('%H:%M:%S')}")
            
            # Call the regular check method
            self.check_save_time()
        except Exception as e:
            print(f"[ERROR] Timer check failed in scriptJob: {str(e)}")
            traceback.print_exc()

    def closeEvent(self, event):
        """Handle clean up when window is closed"""
        savePlus_core.debug_print("Closing SavePlus UI")
        try:
            # Stop redirecting output
            if hasattr(self, 'log_redirector') and self.log_redirector:
                self.log_redirector.stop_redirect()
            
            # Stop Qt timer
            if hasattr(self, 'save_timer') and self.save_timer.isActive():
                self.save_timer.stop()
                print("[DEBUG] Stopped Qt timer during close")
                
            # Kill any active scriptJobs
            if hasattr(self, 'timer_job_id') and self.timer_job_id is not None:
                try:
                    cmds.scriptJob(kill=self.timer_job_id)
                    print(f"[DEBUG] Killed timer scriptJob during close: {self.timer_job_id}")
                    self.timer_job_id = None
                except Exception as e:
                    print(f"[DEBUG] Error killing scriptJob during close: {e}")
            
            # Stop backup timer
            if hasattr(self, 'backup_timer') and self.backup_timer:
                self.backup_timer.stop()
            
            # Disable auto resize to prevent errors during shutdown
            self.auto_resize_enabled = False
        except Exception as e:
            savePlus_core.debug_print(f"Error during close: {e}")
        
        super(SavePlusUI, self).closeEvent(event)

    def bootstrap_timer(self):
        """Safely establish the timer after all UI components are ready"""
        print("\n[DEBUG] ========= BOOTSTRAP TIMER STARTING =========")
        
        # Initialize timer attributes
        if not hasattr(self, 'timer_job_id'):
            self.timer_job_id = None
        
        # Get current preference state
        timer_enabled = self.enable_timed_warning.isChecked()
        print(f"[DEBUG] Current timer checkbox state: {timer_enabled}")
        
        # Only enable the timer if checked
        if timer_enabled:
            print("[DEBUG] Timer is enabled, setting up...")
            self.toggle_timed_warning(Qt.Checked)
        else:
            print("[DEBUG] Timer is disabled, no action needed")
        
        print("[DEBUG] ========= BOOTSTRAP COMPLETE =========\n")

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
