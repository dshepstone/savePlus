SavePlus Installation Guide (v2.0.4)
=====================================

Overview
- SavePlus is a Maya file versioning and project management tool.
- It provides automatic version incrementing, backup creation, version notes, project scene browsing, and project-aware save paths.

System Requirements
- Autodesk Maya 2025 (primary support; Maya 2023/2024 may work with limited features)
- PySide6 (included with Maya 2025)
- Windows 10/11 / macOS 12+ / Linux (CentOS/Rocky 8.6+)
- Python support enabled in Maya (default)

Quick Install (Drag & Drop)
1) Download and extract SavePlus_v2.0.4.zip.
2) Open Maya 2025.
3) Drag install_saveplus.mel into the Maya viewport.
4) Accept the install prompt.
5) A SavePlus shelf button is created on your current shelf (duplicates are
   detected and updated in place rather than added again).
6) (Optional) Launch immediately when prompted.

Manual Install
1) Copy the following files into your Maya scripts directory:
   - __init__.py
   - savePlus_core.py
   - savePlus_maya.py
   - savePlus_main.py
   - savePlus_ui_components.py
   - savePlus_launcher.py
2) Copy icons/saveplus.png into your Maya prefs/icons directory (optional).
3) In Maya's Script Editor (Python tab), run:
   import savePlus_launcher
   savePlus_launcher.install_shelf_button()
4) Click the new shelf button to launch, or run:
   savePlus_launcher.launch_save_plus()

Where Maya Stores Scripts
- Windows:   C:/Users/<username>/Documents/maya/scripts
- macOS:     /Users/<username>/Library/Preferences/Autodesk/maya/scripts
- Linux:     /home/<username>/maya/scripts

Key Features
- Versioned Save: increments filenames automatically (e.g., _v01 -> _v02).
- Backups: optional timed backups with configurable retention.
- Version Notes: attach notes per save and review them later.
- Project Support: set Maya projects, browse project scenes, and open them directly.
- History: browse recent files and version history with notes.
- Compact Name Mode: Name Generator option to shorten filenames for cloud storage
  and Windows path-length limits (target: under 64 characters).
- In-Panel Button Help: brief descriptions shown below the three main save buttons.
- Docked Panel Scroll: Project and History tabs are fully scrollable when docked
  at reduced height.
- Hot Reload: shelf button reloads all SavePlus modules on every click so file
  changes take effect without restarting Maya.

Updating SavePlus
- Re-run the drag-and-drop installer or overwrite the scripts in your Maya scripts
  folder. The installer will update an existing shelf button rather than create a
  duplicate.

Notes
- The Project Scenes browser shows scenes from the current Maya project (project/scenes).
- Check the Maya Script Editor for error output if the UI does not open.

Download
- ZIP: https://github.com/dshepstone/savePlus/releases/download/latest_release/SavePlus_v2.0.4.zip

Support
- Check the Maya Script Editor for error output if the UI does not open.
