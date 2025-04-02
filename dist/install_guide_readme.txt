# SavePlus v1.2.2 - Maya File Versioning Tool
## Installation and Quick Start Guide

### System Requirements
- Maya 2025
- Operating Systems: Windows 10/11, macOS 12+, Linux (CentOS/Rocky Linux 8.6)
- Recommended: 8 GB RAM, Multi-core processor

### Installation Methods

#### Automatic Installation (Recommended)
1. Extract the downloaded SavePlus ZIP file
2. Launch Maya 2025
3. Drag and drop the `install_saveplus.mel` file into Maya's viewport
4. Click "Install" when prompted
5. A SavePlus button will be added to your Maya shelf

#### Manual Installation
1. Extract the SavePlus ZIP file
2. Copy these files to your Maya scripts directory:
   - __init__.py
   - savePlus_core.py
   - savePlus_ui_components.py
   - savePlus_main.py
   - savePlus_launcher.py

3. Copy the icon file (saveplus.png) to your Maya icons directory
   - Windows: C:/Users/[username]/Documents/maya/prefs/icons
   - macOS: /Users/[username]/Library/Preferences/Autodesk/maya/prefs/icons
   - Linux: /home/[username]/maya/prefs/icons

4. In Maya's Script Editor, run:
   ```python
   import savePlus_launcher
   savePlus_launcher.install_shelf_button()
   ```

### Launching SavePlus
- Click the SavePlus button on your Maya shelf
- OR run in Script Editor: 
  ```python
  import savePlus_launcher
  savePlus_launcher.launch_save_plus()
  ```

### Keyboard Shortcuts
- Ctrl+S: Save Plus (increment save)
- Ctrl+Shift+S: Save As New
- Ctrl+B: Create Backup

### Learn More
- Product Website: https://mayasaveplus.com/index.html
- Features: https://mayasaveplus.com/features.html
- Documentation: https://mayasaveplus.com/documentation.html
- Downloads: https://mayasaveplus.com/download.html
- Changelog: https://mayasaveplus.com/changelog.html

### Troubleshooting
- Ensure all files are in the correct Maya scripts directory
- Verify Maya 2025 is installed
- Check Script Editor for any import or installation errors

### Support
- Email Support: support@mayasaveplus.com
- Online Documentation: https://mayasaveplus.com/documentation.html

### License
SavePlus is open-source software. See LICENSE file for details.

### Credits
Original MEL script by Neal Singleton
Python port by SavePlus Team
Version 1.2.2 - Released April 2, 2025

### Copyright
© 2025 SavePlus Team. All rights reserved.