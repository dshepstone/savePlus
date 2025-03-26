"""
SavePlus UI Components - Custom UI classes for the SavePlus tool
Part of the SavePlus toolset for Maya 2025
"""

import sys
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, 
                              QLabel, QDialog, QLineEdit, QHBoxLayout,
                              QCheckBox, QStyle, QSizePolicy, QPlainTextEdit)
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import savePlus_core

VERSION = savePlus_core.VERSION

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
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def stop_redirect(self):
        """Stop redirecting stdout and stderr"""
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
    
    def update_message(self, minutes):
        """Update message to show current interval"""
        if not hasattr(self, 'first_time') or not self.first_time:
            message_text = f"It's been {minutes} minute{'s' if minutes != 1 else ''} since your last save.\nWould you like to save your work now?"
            self.message.setText(message_text)  # Assuming 'message' is the QLabel

    def get_disable_warnings(self):
        """Return whether warnings should be disabled"""
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
        
        # Explanation label
        help_label = QLabel("Enter notes for this version (optional):")
        
        # Text input
        self.text_edit = QPlainTextEdit()
        self.text_edit.setMinimumHeight(100)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Save with Notes")
        save_button.clicked.connect(self.accept)
        
        skip_button = QPushButton("Skip Notes")
        skip_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(skip_button)
        
        # Add to main layout
        layout.addWidget(help_label)
        layout.addWidget(self.text_edit)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_notes(self):
        """Return the entered notes"""
        return self.text_edit.toPlainText()


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
        
        # Ensure fixed position even when collapsed
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
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
        
    def set_collapsed(self, collapsed):
        """Set the collapsed state directly"""
        if self.collapsed != collapsed:
            self.toggle_content()
