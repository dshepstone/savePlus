"""
SavePlus - File versioning tool for Maya 2025 (Python 3 with PySide6)
Maya 2025 - Python 3 and PySide6 Compatible Version
"""

import re
import os
import time
import traceback
from maya import cmds, mel

from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, 
                              QLabel, QDialog, QLineEdit, QHBoxLayout,
                              QCheckBox, QFileDialog, QMainWindow, QMenuBar,
                              QMenu, QStatusBar, QGridLayout, QFrame,
                              QGroupBox, QComboBox, QStyle, QSizePolicy,
                              QTextEdit, QSplitter, QToolButton, QSpinBox,
                              QMessageBox, QFormLayout, QScrollArea,
                              QApplication, QTabWidget)
from PySide6 import QtCore
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QAction
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# Constants
VERSION = "1.1.0"
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
        # Write to the text widget
        if self.text_widget:
            self.text_widget.append(message.rstrip())
            # Make sure to scroll to the bottom
            self.text_widget.verticalScrollBar().setValue(
                self.text_widget.verticalScrollBar().maximum()
            )
    
    def flush(self):
        pass
    
    def start_redirect(self):
        """Start redirecting stdout and stderr"""
        import sys
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def stop_redirect(self):
        """Stop redirecting stdout and stderr"""
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
        
        # Title
        title = QLabel("SavePlus")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        
        # Version
        version = QLabel(f"Version {VERSION}")
        version.setAlignment(Qt.AlignCenter)
        
        # Description
        desc = QLabel(
            "SavePlus provides a simple way to increment your save files.\n"
            "Based on the original MEL script by Neal Singleton."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        
        # Examples
        examples = QLabel(
            "Examples:\n"
            "filename.mb → filename02.mb\n"
            "filename5.mb → filename6.mb\n"
            "filename00002.mb → filename00003.mb\n"
            "scene45_99.mb → scene45_100.mb"
        )
        examples.setWordWrap(True)
        examples.setAlignment(Qt.AlignCenter)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        # Add widgets to layout
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
        
        # Warning icon and message
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
        
        # Checkbox for disabling warnings (only shown for first-time saves)
        self.disable_checkbox = None
        if first_time:
            self.disable_checkbox = QCheckBox("Disable these reminders")
            self.disable_checkbox.setChecked(False)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save Now" if not first_time else "Got it")
        save_button.clicked.connect(self.accept)
        
        remind_later_button = None
        if not first_time:
            remind_later_button = QPushButton("Remind Me Later")
            remind_later_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        if remind_later_button:
            button_layout.addWidget(remind_later_button)
        
        # Add to main layout
        layout.addLayout(message_layout)
        if self.disable_checkbox:
            layout.addWidget(self.disable_checkbox)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_disable_warnings(self):
        """Return whether warnings should be disabled"""
        if self.disable_checkbox:
            return self.disable_checkbox.isChecked()
        return False


class ZurbriggStyleCollapsibleHeader(QWidget):
    """Header widget for the collapsible frame in Zurbrigg style"""
    
    def __init__(self, title, parent=None):
        super(ZurbriggStyleCollapsibleHeader, self).__init__(parent)
        
        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)
        
        # Icon indicator (+ for collapsed, - for expanded)
        self.icon_label = QLabel("-")
        self.icon_label.setFixedWidth(15)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Title with indicator color
        self.title_label = QLabel(title)
        bold_font = QFont()
        bold_font.setBold(True)
        self.title_label.setFont(bold_font)
        
        # Add widgets to layout
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
        
        # Set frame style and fixed height
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), palette.mid().color())
        self.setPalette(palette)
        
        self.setFixedHeight(26)
        
        # Default state is expanded
        self.is_expanded = True
    
    def update_state(self, is_expanded):
        """Update the icon based on the expanded state"""
        self.is_expanded = is_expanded
        self.icon_label.setText("-" if is_expanded else "+")
    
    def mousePressEvent(self, event):
        """Handle mouse press event to toggle collapse state"""
        if self.parent():
            self.parent().toggle_content()
        super(ZurbriggStyleCollapsibleHeader, self).mousePressEvent(event)


class ZurbriggStyleCollapsibleFrame(QWidget):
    """
    A collapsible frame widget that maintains fixed position in layouts,
    similar to how the Zurbrigg Advanced Playblast UI works.
    """
    
    # Define a signal that will be emitted when content is toggled
    toggled = QtCore.Signal()
    
    def __init__(self, title, parent=None, collapsed=True):
        super(ZurbriggStyleCollapsibleFrame, self).__init__(parent)
        
        # Store the current state
        self.collapsed = collapsed
        
        # Main layout for the frame
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        
        # Create header
        self.header = ZurbriggStyleCollapsibleHeader(title, self)
        
        # Create content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Set initial visibility based on collapsed state
        self.content_widget.setVisible(not collapsed)
        self.header.update_state(not collapsed)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content_widget)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Store the expanded height for restoring later
        self.expanded_height = None
    
    def toggle_content(self):
        """Toggle the visibility of the content"""
        self.collapsed = not self.collapsed
        
        # Update the header state
        self.header.update_state(not self.collapsed)
        
        # Toggle visibility
        self.content_widget.setVisible(not self.collapsed)
        
        # Set size hint to force layout update
        if not self.collapsed:
            # When expanding, allow natural size
            self.content_widget.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        else:
            # When collapsing, set minimum height to zero
            self.content_widget.setMaximumHeight(0)
        
        # Emit toggled signal to notify parent of state change
        self.toggled.emit()
    
    def add_widget(self, widget):
        """Add a widget to the content layout"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the content layout"""
        self.content_layout.addLayout(layout)

    def sizeHint(self):
        """Return a size hint that reflects the collapsed state"""
        size = super(ZurbriggStyleCollapsibleFrame, self).sizeHint()
        if self.collapsed:
            size.setHeight(self.header.height())
        return size
        
    def is_collapsed(self):
        """Return the current collapsed state"""
        return self.collapsed


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
    
    def __init__(self, parent=None):
        try:
            super(SavePlusUI, self).__init__(parent)
            debug_print("Initializing SavePlus UI")
            
            # Set window properties
            self.setWindowTitle("SavePlus")
            self.setMinimumWidth(550)
            self.setMinimumHeight(450)
            
            # Flag to control auto-resize behavior
            self.auto_resize_enabled = True
            
            # Directory selected with browse button
            self.selected_directory = None
            
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
            
            # Create tab widget (basic UI component)
            self.tab_widget = QTabWidget()
            
            # Create SavePlus Tab (basic UI component)
            self.saveplus_tab = QWidget()
            self.saveplus_layout = QVBoxLayout(self.saveplus_tab)
            self.saveplus_layout.setContentsMargins(8, 8, 8, 8)
            self.saveplus_layout.setSpacing(8)
            
            # Create Preferences Tab (basic UI component)
            self.preferences_tab = QWidget()
            self.preferences_layout = QVBoxLayout(self.preferences_tab)
            self.preferences_layout.setContentsMargins(8, 8, 8, 8)
            self.preferences_layout.setSpacing(10)
            
            # Add tabs to tab widget (basic UI component)
            self.tab_widget.addTab(self.saveplus_tab, "SavePlus")
            self.tab_widget.addTab(self.preferences_tab, "Preferences")
            
            # Add tab widget to main layout (basic UI component)
            main_layout.addWidget(self.tab_widget)
            
            # --- SAVEPLUS TAB CONTENT ---
            
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
            
            # Add header to saveplus layout
            header_container = QFrame()
            header_container.setFrameShape(QFrame.StyledPanel)
            header_container.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 4px; }")
            header_container.setLayout(header_layout)
            
            self.saveplus_layout.addWidget(header_container)
            
            # Create a subtle separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
            self.saveplus_layout.addWidget(separator)
            
            # Create container widget for scrollable content
            self.container_widget = QWidget()
            self.container_layout = QVBoxLayout(self.container_widget)
            self.container_layout.setContentsMargins(0, 0, 0, 0)
            self.container_layout.setSpacing(5)
            
            # Create File Options section (expanded by default)
            self.file_options_section = ZurbriggStyleCollapsibleFrame("File Options", collapsed=False)
            
            # Create file options content
            file_options = QWidget()
            file_layout = QFormLayout(file_options)
            file_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # Add filename input field
            filename_layout = QHBoxLayout()
            self.filename_input = QLineEdit()
            self.filename_input.setMinimumWidth(250)
            filename_layout.addWidget(self.filename_input)
            
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
            
            # Add timed save warning checkbox
            self.enable_timed_warning = QCheckBox("Enable 15-minute save reminder")
            self.enable_timed_warning.setChecked(self.load_option_var(self.OPT_VAR_ENABLE_TIMED_WARNING, False))
            self.enable_timed_warning.stateChanged.connect(self.toggle_timed_warning)
            
            # Add to form layout
            file_layout.addRow("Filename:", filename_layout)
            file_layout.addRow("File Type:", self.filetype_combo)
            file_layout.addRow("", self.use_current_dir)
            file_layout.addRow("", self.enable_timed_warning)
            
            self.file_options_section.add_widget(file_options)
            self.container_layout.addWidget(self.file_options_section)
            
            # Add file_options_section toggled signal connection
            self.file_options_section.toggled.connect(self.adjust_window_size)
            
            # Create Name Generator section (collapsed by default)
            self.name_gen_section = ZurbriggStyleCollapsibleFrame("Name Generator", collapsed=True)
            
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
            
            save_button = QPushButton("Save Plus")
            save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
            save_button.setMinimumHeight(40)
            save_button.clicked.connect(self.save_plus)
            
            save_new_button = QPushButton("Save As New")
            save_new_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            save_new_button.setMinimumHeight(40)
            save_new_button.clicked.connect(self.save_as_new)
            
            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(save_new_button)
            
            self.container_layout.addLayout(buttons_layout)
            
            # Create Log section (collapsed by default)
            self.log_section = ZurbriggStyleCollapsibleFrame("Log Output", collapsed=True)
            
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
            
            # Create scroll area
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(self.container_widget)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Add scroll area to saveplus layout
            self.saveplus_layout.addWidget(self.scroll_area)
            
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
            
            # Add to preferences layout
            self.preferences_layout.addWidget(general_group)
            
            # Path Preferences
            paths_group = QGroupBox("Path Settings")
            paths_layout = QFormLayout(paths_group)
            
            # Default save location
            default_location = QHBoxLayout()
            self.pref_default_path = QLineEdit()
            self.pref_default_path.setPlaceholderText("Default directory for saving files")
            browse_button = QPushButton("Browse...")
            browse_button.setFixedWidth(80)
            default_location.addWidget(self.pref_default_path)
            default_location.addWidget(browse_button)
            
            paths_layout.addRow("Default Save Location:", default_location)
            
            # Project directory
            project_location = QHBoxLayout()
            self.pref_project_path = QLineEdit()
            self.pref_project_path.setPlaceholderText("Maya project directory")
            project_browse = QPushButton("Browse...")
            project_browse.setFixedWidth(80)
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
            apply_button_layout = QHBoxLayout()
            apply_button_layout.addStretch()
            apply_button_layout.addWidget(apply_button)
            
            self.preferences_layout.addLayout(apply_button_layout)
            
            # Update filename preview initially
            self.update_filename_preview()
            
            # Setup log redirector
            self.log_redirector = LogRedirector(self.log_text)
            self.log_redirector.start_redirect()
            
            # Log initialization message
            print("SavePlus UI initialized successfully")
            
            # Setup timer for save reminders
            self.last_save_time = time.time()
            self.save_timer = QTimer(self)
            self.save_timer.timeout.connect(self.check_save_time)
            
            # Flag to track first-time save
            self.is_first_save = not current_file
            
            # Start timer if option is enabled
            if self.enable_timed_warning.isChecked():
                self.save_timer.start(60000)  # Check every minute
            
            # Schedule initial window sizing after UI is fully constructed
            QtCore.QTimer.singleShot(200, self.adjust_window_size)
                
        except Exception as e:
            error_message = f"Error initializing SavePlus UI: {str(e)}"
            print(error_message)
            traceback.print_exc()
            cmds.confirmDialog(title="SavePlus Error", 
                              message=f"Error loading SavePlus: {str(e)}\n\nCheck script editor for details.", 
                              button=["OK"], defaultButton="OK")
    
    def closeEvent(self, event):
        """Handle clean up when window is closed"""
        debug_print("Closing SavePlus UI")
        try:
            # Stop redirecting output
            if hasattr(self, 'log_redirector') and self.log_redirector:
                self.log_redirector.stop_redirect()
            
            # Stop timer
            if hasattr(self, 'save_timer') and self.save_timer:
                self.save_timer.stop()
            
            # Disable auto resize to prevent errors during shutdown
            self.auto_resize_enabled = False
        except Exception as e:
            debug_print(f"Error during close: {e}")
        
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
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Location Directory", ""
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
    
    def save_plus(self):
        """Execute the save plus operation with the specified filename"""
        print("Starting Save Plus operation...")
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
            # Extension based on dropdown (now .ma is first)
            ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
            filename = base_name + ext
            print(f"Applied file extension: {ext}")
        
        print(f"Attempting to save as: {filename}")
        
        # Perform the save operation
        result, message = save_plus_proc(filename)
        self.status_bar.showMessage(message, 5000)
        print(message)
        
        # Update the filename field with the new filename if successful
        if result:
            new_filename = cmds.file(query=True, sceneName=True)
            if new_filename:
                self.filename_input.setText(os.path.basename(new_filename))
                print(f"Updated filename to: {os.path.basename(new_filename)}")
                self.update_filename_preview()
                
                # Reset the save timer
                self.last_save_time = time.time()
                
                # If this was a first-time save and warnings are enabled, show first-time warning
                if is_first_save and self.enable_timed_warning.isChecked():
                    self.show_first_time_warning()
    
    def save_as_new(self):
        """Save the file with the specified name without incrementing"""
        print("Starting Save As New operation...")
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
            # Extension based on dropdown (now .ma is first)
            ext = '.ma' if self.filetype_combo.currentIndex() == 0 else '.mb'
            filename = base_name + ext
            print(f"Applied file extension: {ext}")
        
        print(f"Attempting to save as: {filename}")
        
        # Check if file exists
        if os.path.exists(filename):
            message = f"Warning: {os.path.basename(filename)} already exists, file not saved"
            self.status_bar.showMessage(message, 5000)
            print(message)
            return
        
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
            cmds.file(save=True)
            message = f"{os.path.basename(filename)} saved successfully"
            self.status_bar.showMessage(message, 5000)
            print(message)
            
            # Reset the save timer
            self.last_save_time = time.time()
            
            # If this was a first-time save and warnings are enabled, show first-time warning
            if is_first_save and self.enable_timed_warning.isChecked():
                self.show_first_time_warning()
        except Exception as e:
            message = f"Error saving file: {e}"
            self.status_bar.showMessage(message, 5000)
            print(message)
    
    def show_preferences(self):
        """Show the preferences tab"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentWidget(self.preferences_tab)
    
    def show_about(self):
        """Show the about dialog"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def show_first_time_warning(self):
        """Show the first-time save warning dialog"""
        warning_dialog = TimedWarningDialog(self, first_time=True)
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
                print("Save reminder enabled (15-minute interval)")
            else:
                self.save_timer.stop()
                print("Save reminder disabled")
            
            # Save setting
            cmds.optionVar(iv=(self.OPT_VAR_ENABLE_TIMED_WARNING, state == Qt.Checked))
    
    def check_save_time(self):
        """Check if enough time has passed to show a save reminder"""
        current_time = time.time()
        elapsed_minutes = (current_time - self.last_save_time) / 60
        
        # Show warning if it's been at least 15 minutes
        if elapsed_minutes >= 15:
            warning_dialog = TimedWarningDialog(self)
            result = warning_dialog.exec()
            
            if result == QDialog.Accepted:
                # User clicked "Save Now"
                self.save_plus()
            else:
                # User clicked "Remind Me Later" - reset timer for 5 minutes
                self.last_save_time = current_time - (10 * 60)  # Will trigger again in 5 minutes
    
    def load_option_var(self, name, default_value):
        """Load an option variable with a default value"""
        try:
            if cmds.optionVar(exists=name):
                if isinstance(default_value, bool):
                    return bool(cmds.optionVar(q=name))
                elif isinstance(default_value, int):
                    return cmds.optionVar(q=name)
                elif isinstance(default_value, str):
                    return cmds.optionVar(q=name)
            return default_value
        except Exception as e:
            debug_print(f"Error loading option var {name}: {e}")
            return default_value
        
    def adjust_window_size(self):
        """Adjust window size based on content"""
        if not self.auto_resize_enabled:
            return
            
        try:
            # Process events to ensure container widget is properly laid out
            QtCore.QCoreApplication.processEvents()
            
            # Calculate optimal height based on visible content
            total_height = 0
            
            # Add header height
            if hasattr(self, 'saveplus_tab'):
                total_height += 80  # Approximate height for header
            
            # Add heights for visible sections
            if hasattr(self, 'file_options_section') and not self.file_options_section.is_collapsed():
                total_height += 150  # Approximate height when expanded
            else:
                total_height += 30   # Header height when collapsed
                
            if hasattr(self, 'name_gen_section') and not self.name_gen_section.is_collapsed():
                total_height += 280  # Approximate height when expanded
            else:
                total_height += 30   # Header height when collapsed
                
            if hasattr(self, 'log_section') and not self.log_section.is_collapsed():
                total_height += 200  # Approximate height when expanded
            else:
                total_height += 30   # Header height when collapsed
                
            # Add height for save buttons
            total_height += 50
            
            # Add margins for the main window components (menu bar, status bar, etc)
            extra_height = 100
            
            # Set window size
            self.resize(self.width(), total_height + extra_height)
            
            # Process events to apply resize immediately
            QtCore.QCoreApplication.processEvents()
        except Exception as e:
            debug_print(f"Error during window resize: {e}")
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
            debug_print(f"Error saving name generator settings: {e}")


def save_plus_proc(file_path=None):
    """Core function that implements the SavePlus functionality"""
    print("=== SavePlus Process Started ===")
    
    # Log current Maya scene information
    current_scene = cmds.file(query=True, sceneName=True)
    print(f"Current scene: {current_scene or 'Unsaved scene'}")
    
    if not file_path:
        file_path = cmds.file(query=True, sceneName=True)
        
        if not file_path:
            print("ERROR: No filename specified and scene not saved")
            return False, "File must be saved before using SavePlus"
    
    if file_path:
        print(f"Target file path: {file_path}")
    
    # Handle the case where file_path is just a filename
    if os.path.dirname(file_path) == "":
        # Get current workspace
        workspace = cmds.workspace(query=True, directory=True)
        scenes_dir = os.path.join(workspace, "scenes")
        
        # Check if scenes directory exists, create if it doesn't
        if not os.path.exists(scenes_dir):
            try:
                print(f"Creating scenes directory: {scenes_dir}")
                os.makedirs(scenes_dir)
            except Exception as e:
                print(f"ERROR: Could not create scenes directory: {e}")
                return False, f"Error: Could not create scenes directory: {e}"
        
        file_path = os.path.join(scenes_dir, file_path)
        print(f"Using workspace scenes directory: {file_path}")
    
    # Split path and filename
    directory = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    print(f"Directory: {directory}")
    print(f"Filename: {file_name}")
    
    # Make sure the directory exists
    if not os.path.exists(directory):
        try:
            print(f"Creating directory: {directory}")
            os.makedirs(directory)
        except OSError as e:
            print(f"ERROR: Could not create directory: {e}")
            return False, f"Error: Could not create directory {directory}"
    
    # Check if this is a first-time save
    current_scene = cmds.file(query=True, sceneName=True)
    if not current_scene:
        print("First-time save detected")
        # If not a Maya file extension, add .ma
        if not file_name.endswith('.ma') and not file_name.endswith('.mb'):
            file_path += '.ma'  # Changed default to .ma
            print(f"Added .ma extension: {file_path}")
        
        # If the file doesn't exist, just save it
        if not os.path.exists(file_path):
            try:
                print(f"Saving new file as: {file_path}")
                cmds.file(rename=file_path)
                cmds.file(save=True)
                print("=== SavePlus Process Completed Successfully ===")
                return True, f"{os.path.basename(file_path)} saved successfully"
            except Exception as e:
                print(f"ERROR during save: {e}")
                return False, f"Error saving file: {e}"
        else:
            print(f"ERROR: File already exists: {file_path}")
            return False, f"Error: File {os.path.basename(file_path)} already exists"
    
    # Make sure we have a valid file extension
    base_name, ext = os.path.splitext(file_name)
    if ext.lower() not in ['.ma', '.mb']:
        ext = '.ma'  # Changed default to .ma
        file_name = base_name + ext
        file_path = os.path.join(directory, file_name)
        print(f"Using default .ma extension: {file_path}")
    
    # First, check for a structured assignment-based filename pattern
    # Format: X##_LastName_FirstName_type_##
    # For example: A01_Smith_John_wip_01.mb
    assignment_match = re.match(r'([A-Z])(\d+)_([^_]+)_([^_]+)_([^_]+)_(\d+)$', base_name)
    
    if assignment_match:
        # We have a name generator formatted filename
        assignment_letter = assignment_match.group(1)
        assignment_number = assignment_match.group(2)
        last_name = assignment_match.group(3)
        first_name = assignment_match.group(4)
        version_type = assignment_match.group(5)
        version_number = assignment_match.group(6)
        
        # Increment the version number
        new_version_number = str(int(version_number) + 1).zfill(len(version_number))
        
        # Create the new name
        new_base_name = f"{assignment_letter}{assignment_number}_{last_name}_{first_name}_{version_type}_{new_version_number}"
        print(f"Incrementing version number from {version_number} to {new_version_number}")
    else:
        # Regular expression to find the trailing number
        match = re.search(r'(\D*)(\d+)(\D*)$', base_name)
        
        if match:
            # If a number is found
            prefix = match.group(1)
            number = match.group(2)
            suffix = match.group(3)
            
            # Increment the number, preserving leading zeros
            new_number = str(int(number) + 1).zfill(len(number))
            new_base_name = prefix + new_number + suffix
            print(f"Incrementing number from {number} to {new_number}")
        else:
            # If no number is found, add "02" to the end
            new_base_name = base_name + "02"
            print(f"No number found, adding '02' suffix: {new_base_name}")
    
    # Create the new filename
    new_file_name = new_base_name + ext
    new_file_path = os.path.join(directory, new_file_name)
    print(f"New file path: {new_file_path}")
    
    # Check if the file already exists
    if os.path.exists(new_file_path):
        print(f"ERROR: New file already exists: {new_file_path}")
        return False, f"Warning: {new_file_name} already exists, file not saved"
    
    # Rename and save
    try:
        print(f"Renaming file to: {new_file_path}")
        cmds.file(rename=new_file_path)
        print("Saving file...")
        cmds.file(save=True)
        print("=== SavePlus Process Completed Successfully ===")
        return True, f"{new_file_name} saved successfully"
    except Exception as e:
        print(f"ERROR during save: {e}")
        print("=== SavePlus Process Failed ===")
        return False, f"Error saving file: {e}"


# Show the UI when script is executed
print("="*50)
print(f"SavePlus v{VERSION} starting...")

try:
    # Show the UI
    ui = SavePlusUI()
    ui.show()
    
    print(f"SavePlus v{VERSION} loaded successfully!")
except Exception as e:
    print(f"Error loading SavePlus: {str(e)}")
    traceback.print_exc()
    cmds.confirmDialog(title="SavePlus Error", 
                      message=f"Error loading SavePlus: {str(e)}\n\nCheck script editor for details.", 
                      button=["OK"], defaultButton="OK")

print("="*50)
