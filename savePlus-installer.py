"""
SavePlus Installer for Maya 2025 with PySide6
-----------------
This small script installs SavePlus buttons on your current Maya shelf.
Just copy and paste this into the Maya Script Editor and run it.
"""

import os
from maya import cmds, mel

# Define the path to save the script
scripts_dir = os.path.join(cmds.internalVar(userAppDir=True), "scripts")
savePlus_path = os.path.join(scripts_dir, "savePlus.py")

# Create the scripts directory if it doesn't exist
if not os.path.exists(scripts_dir):
    os.makedirs(scripts_dir)

# Display installation info
print("="*50)
print("SavePlus Installer for Maya 2025")
print("="*50)
print(f"Scripts directory: {scripts_dir}")
print(f"SavePlus script path: {savePlus_path}")

# Define the UI button command
ui_button_command = """
# Load SavePlus UI
import sys
import os
from maya import cmds

# Import the SavePlus module
script_path = os.path.join(cmds.internalVar(userAppDir=True), "scripts", "savePlus.py")

try:
    # Execute the script
    exec(open(script_path).read())
except Exception as e:
    cmds.warning(f"Error loading SavePlus: {e}")
"""

# Define the Quick Save command
quick_save_command = """
# Quick SavePlus - Standalone version
import re
import os
from maya import cmds

def quick_save_plus():
    # Get current file path
    current_file = cmds.file(query=True, sceneName=True)
    if not current_file:
        cmds.warning("File must be saved at least once before using Quick SavePlus")
        return
    
    # Split path and filename
    directory = os.path.dirname(current_file)
    file_name = os.path.basename(current_file)
    
    # Make sure we have a valid file extension
    base_name, ext = os.path.splitext(file_name)
    if ext.lower() not in ['.ma', '.mb']:
        ext = '.mb'  # Default to .mb if no valid extension
        file_name = base_name + ext
        current_file = os.path.join(directory, file_name)
    
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
        else:
            # If no number is found, add "02" to the end
            new_base_name = base_name + "02"
    
    # Create the new filename
    new_file_name = new_base_name + ext
    new_file_path = os.path.join(directory, new_file_name)
    
    # Check if the file already exists
    if os.path.exists(new_file_path):
        cmds.warning(f"Warning: {new_file_name} already exists, file not saved")
        return
    
    # Rename and save
    try:
        cmds.file(rename=new_file_path)
        cmds.file(save=True)
        print(f"File saved successfully as: {new_file_name}")
    except Exception as e:
        cmds.warning(f"Error saving file: {e}")

# Run the quick save plus function
quick_save_plus()
"""

# Function to create the shelf buttons
def create_shelf_buttons():
    UNIQUE_IDENTIFIER = "SavePlus_v1_ToolButton"
    
    # Get the active shelf
    top_shelf = mel.eval('$gShelfTopLevel=$gShelfTopLevel')
    current_shelf = cmds.tabLayout(top_shelf, query=True, selectTab=True)
    
    # Check for existing buttons
    existing_ui_button = None
    existing_quick_button = None
    
    if cmds.shelfLayout(current_shelf, exists=True):
        shelf_buttons = cmds.shelfLayout(current_shelf, query=True, childArray=True) or []
        for btn in shelf_buttons:
            if cmds.shelfButton(btn, exists=True):
                try:
                    annotation = cmds.shelfButton(btn, query=True, annotation=True)
                    if f"{UNIQUE_IDENTIFIER} - UI" in annotation:
                        existing_ui_button = btn
                    elif f"{UNIQUE_IDENTIFIER} - Quick" in annotation:
                        existing_quick_button = btn
                except:
                    pass
    
    # Create or update UI button
    if existing_ui_button:
        cmds.shelfButton(existing_ui_button, edit=True, command=ui_button_command)
        print(f"Updated existing UI button")
    else:
        button = cmds.shelfButton(
                label='SavePlus',
                annotation=f'Show SavePlus interface - {UNIQUE_IDENTIFIER} - UI',
                image='incrementalSave.png',
                command=ui_button_command,
                sourceType='python',
                parent=current_shelf)
        print(f"UI button created")
    
    # Create or update Quick button
    if existing_quick_button:
        cmds.shelfButton(existing_quick_button, edit=True, command=quick_save_command)
        print(f"Updated existing Quick button")
    else:
        button = cmds.shelfButton(
                label='Quick SavePlus',
                annotation=f'Version up current file without UI - {UNIQUE_IDENTIFIER} - Quick',
                image='save.png',
                command=quick_save_command,
                sourceType='python',
                parent=current_shelf)
        print(f"Quick button created")

# Create the shelf buttons
create_shelf_buttons()

print("SavePlus buttons installed successfully!")
print("="*50)
