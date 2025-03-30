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

def normalize_path(path):
    """Normalize file paths to use consistent forward slashes."""
    if path:
        return path.replace('\\', '/')
    return path

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
    print("=== MODIFIED SavePlus Process Started (Version 2.0) ===")
    
    # Normalize the input path
    if file_path:
        file_path = normalize_path(file_path)
    
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
        file_path = normalize_path(file_path)
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
    
    print(f"DEBUG: Processing base_name: '{base_name}'")
    
    # Special pattern for known problematic filenames
    # Check for _Lucus_Scene pattern specifically
    lucus_match = re.search(r'^_?Lucus_Scene_(\w+)_(\w+)_(\d+)$', base_name)
    if lucus_match:
        print(f"DEBUG: Found Lucus_Scene pattern")
        stage = lucus_match.group(1)
        status = lucus_match.group(2)
        version_number = lucus_match.group(3)
        
        # Extract project identifier if it exists before the _Lucus_Scene
        project_prefix = ""
        project_match = re.match(r'^([A-Z]\d+)_?Lucus_Scene', base_name)
        if project_match:
            project_prefix = project_match.group(1) + "_"
            print(f"DEBUG: Found project prefix: {project_prefix}")
        
        # Increment the version number
        new_version_number = str(int(version_number) + 1).zfill(len(version_number))
        new_base_name = f"{project_prefix}Lucus_Scene_{stage}_{status}_{new_version_number}"
        print(f"DEBUG: Special case - Incrementing from {version_number} to {new_version_number}")
    else:
        # IMPROVED FILENAME HANDLING SECTION
        # First, check for project identifier pattern (e.g., J02_)
        project_prefix_match = re.match(r'^([A-Z]\d+)_(.+)$', base_name)
        
        if project_prefix_match:
            # Extract project identifier components
            project_prefix = project_prefix_match.group(1)
            remainder = project_prefix_match.group(2)
            
            print(f"DEBUG: Found project identifier: {project_prefix}_")
            print(f"DEBUG: Name remainder: {remainder}")
            
            # Try the strict assignment-based pattern first
            # Format: LastName_FirstName_type_##
            assignment_match = re.match(r'([^_]+)_([^_]+)_([^_]+)_(\d+)$', remainder)
            
            if assignment_match:
                # We have a standard name generator formatted filename
                last_name = assignment_match.group(1)
                first_name = assignment_match.group(2)
                version_type = assignment_match.group(3)
                version_number = assignment_match.group(4)
                
                # Increment the version number
                new_version_number = str(int(version_number) + 1).zfill(len(version_number))
                
                # Create the new name with project prefix preserved
                new_base_name = f"{project_prefix}_{last_name}_{first_name}_{version_type}_{new_version_number}"
                print(f"DEBUG: Incrementing version number from {version_number} to {new_version_number}")
            else:
                # Try more flexible pattern for any number at the end of the string
                number_match = re.search(r'(.*)(\d+)$', remainder)
                
                if number_match:
                    prefix = number_match.group(1)
                    number = number_match.group(2)
                    
                    # Increment the number, preserving leading zeros
                    new_number = str(int(number) + 1).zfill(len(number))
                    
                    # Create the new name with project prefix preserved
                    new_base_name = f"{project_prefix}_{prefix}{new_number}"
                    print(f"DEBUG: Incrementing number from {number} to {new_number} with project prefix preserved")
                else:
                    # Try to find any numbers in the string that we can increment
                    number_anywhere = re.search(r'(.*)(\d+)(.*)', remainder)
                    
                    if number_anywhere:
                        before = number_anywhere.group(1)
                        num = number_anywhere.group(2)
                        after = number_anywhere.group(3)
                        
                        # Increment the number, preserving leading zeros
                        new_num = str(int(num) + 1).zfill(len(num))
                        
                        # Create the new name with project prefix preserved
                        new_base_name = f"{project_prefix}_{before}{new_num}{after}"
                        print(f"DEBUG: Found and incremented number anywhere in string: {num} -> {new_num}")
                    else:
                        # No trailing number found, add "02" to the end of the remainder
                        new_base_name = f"{project_prefix}_{remainder}02"
                        print(f"DEBUG: No number found in remainder, adding '02' suffix with project prefix preserved")
        else:
            # Special handling for filenames that might have a backslash issue
            if base_name.startswith('\\'):
                print(f"DEBUG: Found backslash at start of filename: {repr(base_name)}")
                # Remove the backslash for processing
                clean_base_name = base_name.replace('\\', '')
                
                # Look for the pattern after removing the backslash
                clean_match = re.search(r'(.*)(\d+)$', clean_base_name)
                if clean_match:
                    prefix = clean_match.group(1)
                    number = clean_match.group(2)
                    
                    # Increment the number, preserving leading zeros
                    new_number = str(int(number) + 1).zfill(len(number))
                    new_base_name = prefix + new_number
                    print(f"DEBUG: After removing backslash, incrementing number from {number} to {new_number}")
                else:
                    # If no number found, add "02" to the end
                    new_base_name = clean_base_name + "02"
                    print(f"DEBUG: After removing backslash, adding '02' suffix: {new_base_name}")
            else:
                # Standard processing without project identifier
                # First, check for a structured assignment-based filename pattern without project prefix
                # Format: LastName_FirstName_type_##
                assignment_match = re.match(r'([^_]+)_([^_]+)_([^_]+)_(\d+)$', base_name)
                
                if assignment_match:
                    # We have a name generator formatted filename without project prefix
                    last_name = assignment_match.group(1)
                    first_name = assignment_match.group(2)
                    version_type = assignment_match.group(3)
                    version_number = assignment_match.group(4)
                    
                    # Increment the version number
                    new_version_number = str(int(version_number) + 1).zfill(len(version_number))
                    
                    # Create the new name
                    new_base_name = f"{last_name}_{first_name}_{version_type}_{new_version_number}"
                    print(f"DEBUG: Incrementing version number from {version_number} to {new_version_number}")
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
                        print(f"DEBUG: Incrementing number from {number} to {new_number}")
                    else:
                        # If no number is found, add "02" to the end
                        new_base_name = base_name + "02"
                        print(f"DEBUG: No number found, adding '02' suffix: {new_base_name}")
    
    # Create the new filename
    new_file_name = new_base_name + ext
    new_file_path = os.path.join(directory, new_file_name)
    new_file_path = normalize_path(new_file_path)
    print(f"DEBUG: Raw new_file_path: {repr(new_file_path)}")
    print(f"New file path: {new_file_path}")
    
    # IMPROVED FILE CONFLICT HANDLING
    # Check if the file already exists and find the next available version if needed
    if os.path.exists(new_file_path):
        print(f"DEBUG: File conflict detected for {new_file_path}")
        print(f"DEBUG: Entering auto-increment section")
        
        print(f"WARNING: File already exists: {new_file_path}")
        print("Finding next available version...")
        
        # Set up counters for finding next available filename
        attempt = 1
        max_attempts = 100  # Prevent infinite loops
        available_found = False
        
        # Try to find an available filename by incrementing numbers
        while not available_found and attempt < max_attempts:
            attempt_version = new_base_name
            
            # Try to find and increment the last number in the filename
            number_match = re.search(r'(\D*)(\d+)(\D*)$', attempt_version)
            if number_match:
                prefix = number_match.group(1)
                number = number_match.group(2)
                suffix = number_match.group(3)
                
                # Increment number by current attempt count
                attempt_number = str(int(number) + attempt).zfill(len(number))
                attempt_version = prefix + attempt_number + suffix
            else:
                # Fallback if no number pattern found
                attempt_version = f"{new_base_name}_{attempt}"
            
            # Create the complete filename with extension
            attempt_filename = attempt_version + ext
            attempt_filepath = os.path.join(directory, attempt_filename)
            attempt_filepath = normalize_path(attempt_filepath)
                        
            print(f"DEBUG: Attempt {attempt} - Trying {attempt_filepath}")
            
            # Check if this version is available
            if not os.path.exists(attempt_filepath):
                new_base_name = attempt_version
                new_file_name = attempt_filename
                new_file_path = attempt_filepath
                available_found = True
                print(f"Found available filename: {new_file_name}")
            
            attempt += 1
        
        # If we couldn't find an available name after all attempts
        if not available_found:
            print(f"ERROR: Could not find an available filename after {max_attempts} attempts")
            return False, f"Error: Could not find an available filename after {max_attempts} attempts", ""
    
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