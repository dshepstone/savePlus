"""
SavePlus Core - File versioning and history tracking for Maya
Part of the SavePlus toolset for Maya 2025
"""

import re
import os
import time
import json
from datetime import datetime
from maya import cmds

# Constants
VERSION = "1.2.0"
DEBUG_MODE = True

def debug_print(message):
    """Print debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        print(f"[SavePlus Debug] {message}")

class VersionHistoryModel:
    """Class to manage version history data"""
    
    def __init__(self):
        self.history_file = os.path.join(
            cmds.internalVar(userAppDir=True),
            "saveplus_history.json"
        )
        self.versions = self.load_history()
    
    def load_history(self):
        """Load version history from disk"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            debug_print(f"Error loading version history: {e}")
            return {}
    
    def save_history(self):
        """Save version history to disk"""
        try:
            # Create directory if it doesn't exist
            dirname = os.path.dirname(self.history_file)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
                
            with open(self.history_file, 'w') as f:
                json.dump(self.versions, f, indent=2)
        except Exception as e:
            debug_print(f"Error saving version history: {e}")
    
    def add_version(self, file_path, notes=""):
        """Add a new version to history"""
        base_path = os.path.normpath(file_path)  # Normalize path for consistency
        
        # Get base file without version number to group related files
        base_name = os.path.basename(base_path)
        directory = os.path.dirname(base_path)
        
        # Extract the base name without version number for grouping
        match = re.search(r'(\D*?)(\d+)([^/\\]*?)$', base_name)
        if match:
            group_key = os.path.join(directory, match.group(1))
        else:
            # If no number in filename, use directory as group
            group_key = directory
        
        # Initialize group if it doesn't exist
        if group_key not in self.versions:
            self.versions[group_key] = []
        
        # Add new version
        version_info = {
            "path": base_path,
            "filename": base_name,
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes
        }
        
        # Add to front of the list (most recent first)
        self.versions[group_key].insert(0, version_info)
        
        # Limit to 50 entries per group
        if len(self.versions[group_key]) > 50:
            self.versions[group_key] = self.versions[group_key][:50]
        
        # Save changes
        self.save_history()
        
        return version_info
    
    def get_recent_versions(self, count=10):
        """Get the most recent versions across all groups"""
        all_versions = []
        
        for group, versions in self.versions.items():
            all_versions.extend(versions)
        
        # Sort by timestamp, newest first
        sorted_versions = sorted(
            all_versions, 
            key=lambda x: x.get('timestamp', 0), 
            reverse=True
        )
        
        return sorted_versions[:count]
    
    def get_versions_for_file(self, file_path):
        """Get all versions related to the given file"""
        base_path = os.path.normpath(file_path)
        directory = os.path.dirname(base_path)
        base_name = os.path.basename(base_path)
        
        # Try to find the group that contains this file
        match = re.search(r'(\D*?)(\d+)([^/\\]*?)$', base_name)
        if match:
            group_key = os.path.join(directory, match.group(1))
            
            if group_key in self.versions:
                return self.versions[group_key]
        
        # If we couldn't find a direct match, check if the file exists in any group
        for group, versions in self.versions.items():
            for version in versions:
                if version.get('path') == base_path:
                    return versions
        
        return []
    
    def export_history(self, file_path):
        """Export version history to a text file"""
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
            return False, "File must be saved before using SavePlus", ""
    
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
                return False, f"Error: Could not create scenes directory: {e}", ""
        
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
            return False, f"Error: Could not create directory {directory}", ""
    
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
                # Use saveAs for the first save to ensure proper file format
                if file_path.lower().endswith('.ma'):
                    cmds.file(save=True, type='mayaAscii')
                elif file_path.lower().endswith('.mb'):
                    cmds.file(save=True, type='mayaBinary')
                else:
                    # Default to Maya ASCII
                    cmds.file(save=True, type='mayaAscii')
                    
                print("=== SavePlus Process Completed Successfully ===")
                return True, f"{os.path.basename(file_path)} saved successfully", file_path
            except Exception as e:
                print(f"ERROR during save: {e}")
                return False, f"Error saving file: {e}", ""
        else:
            print(f"ERROR: File already exists: {file_path}")
            return False, f"Error: File {os.path.basename(file_path)} already exists", ""
    
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
        return False, f"Warning: {new_file_name} already exists, file not saved", ""
    
    # Rename and save
    try:
        print(f"Renaming file to: {new_file_path}")
        cmds.file(rename=new_file_path)
        print("Saving file...")
        
        # Explicitly specify the file type based on extension
        if new_file_path.lower().endswith('.ma'):
            cmds.file(save=True, type='mayaAscii')
        elif new_file_path.lower().endswith('.mb'):
            cmds.file(save=True, type='mayaBinary')
        else:
            # Default to Maya ASCII if extension is unknown
            cmds.file(save=True, type='mayaAscii')
            
        print("=== SavePlus Process Completed Successfully ===")
        return True, f"{new_file_name} saved successfully", new_file_path
    except Exception as e:
        print(f"ERROR during save: {e}")
        print("=== SavePlus Process Failed ===")
        return False, f"Error saving file: {e}", ""

def load_option_var(name, default_value):
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

def create_backup(current_file=None):
    """Create a backup copy of the current file"""
    print("Creating backup...")
    
    # Check if file is saved
    if not current_file:
        current_file = cmds.file(query=True, sceneName=True)
        
    if not current_file:
        print("ERROR: File must be saved at least once before creating a backup")
        return False, "Error: File must be saved at least once before creating a backup", ""
    
    # Create backup filename - add "_backup" and timestamp
    directory = os.path.dirname(current_file)
    base_name, ext = os.path.splitext(os.path.basename(current_file))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{base_name}_backup_{timestamp}{ext}"
    backup_path = os.path.join(directory, backup_filename)
    
    # Save a copy
    try:
        # Save current file first
        cmds.file(save=True)
        
        # Use Maya's file command to make a copy
        cmds.file(current_file, copyAs=backup_path)
        
        message = f"Backup saved as: {backup_filename}"
        print(message)
        
        return True, message, backup_path
    except Exception as e:
        message = f"Error creating backup: {e}"
        print(message)
        return False, message, ""
