SavePlus Installation Guide (v1.3.1)
===================================

Overview
- SavePlus is a Maya file versioning and project management tool.
- It provides automatic version incrementing, backup creation, version notes, project scene browsing, and project-aware save paths.

System Requirements
- Autodesk Maya 2016+ (tested with Maya 2025)
- Python support enabled in Maya (default)

Quick Install (Drag & Drop)
1) Locate the SavePlus package folder that contains:
   - install_saveplus.mel
   - install_saveplus.py
   - savePlus_core.py
   - savePlus_main.py
   - savePlus_ui_components.py
   - savePlus_launcher.py
   - icons/saveplus.png (optional but recommended)
2) Drag and drop install_saveplus.mel into the Maya viewport.
3) Accept the install prompt.
4) A SavePlus shelf button is created on your current shelf.
5) (Optional) Launch immediately when prompted.

Manual Install
1) Copy the following files into your Maya scripts directory:
   - savePlus_core.py
   - savePlus_main.py
   - savePlus_ui_components.py
   - savePlus_launcher.py
   - __init__.py (optional, for package metadata)
2) Copy icons/saveplus.png into your Maya prefs/icons directory (optional).
3) In Maya's Script Editor (Python tab), run:
   import savePlus_launcher
   savePlus_launcher.launch_save_plus()
4) Create a shelf button using the same command if desired.

Where Maya Stores Scripts
- Windows:   %USERPROFILE%/Documents/maya/<version>/scripts
- macOS:     ~/Library/Preferences/Autodesk/maya/<version>/scripts
- Linux:     ~/maya/<version>/scripts

Key Features
- Versioned Save: increments filenames automatically (e.g., _v01 -> _v02).
- Backups: optional timed backups with configurable retention.
- Version Notes: attach notes per save and review them later.
- Project Support: set Maya projects, browse project scenes, and open them directly.
- History: browse recent files and version history with notes.

Notes
- If you update SavePlus, re-run the installer or overwrite the scripts in your Maya scripts folder.
- The Project Scenes browser shows scenes from the current Maya project (project/scenes).

Support
- Check the Maya Script Editor for error output if the UI does not open.
