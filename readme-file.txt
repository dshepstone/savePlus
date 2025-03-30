# SavePlus - Intelligent File Versioning for Maya

![SavePlus Logo](docs/assets/images/saveplus_logo.png)

SavePlus is a comprehensive file versioning and management tool for Autodesk Maya 2025 that helps artists maintain organized version histories, track changes, and prevent work loss.

## Key Features

- **Intelligent Versioning**: Automatically increment file versions with smart detection of naming patterns
- **Version History Tracking**: Keep a complete record of your file versions with optional notes
- **Save Reminders**: Customizable alerts to remind you when it's time to save your work
- **Automatic Backups**: Create timestamped backup copies to prevent data loss
- **Name Generator**: Generate standardized filenames based on project requirements and pipeline stage
- **Customizable Settings**: Configure defaults to match your specific workflow needs

## Quick Installation

1. **Download**: Get the latest version from the [Releases page](https://github.com/yourusername/saveplus/releases)
2. **Extract**: Unzip the package to a temporary location
3. **Install**: Drag and drop `install_saveplus.py` into Maya's viewport
4. **Launch**: Click the SavePlus button on your Maya shelf

For detailed installation instructions, see the [Documentation](https://yourusername.github.io/saveplus/documentation.html#installation).

## Usage

SavePlus provides three primary ways to save your work:

```python
# Save Plus (increment version)
import savePlus_launcher
savePlus_launcher.launch_save_plus()  # Then click "Save Plus"

# Save As New (create new file)
import savePlus_launcher
savePlus_launcher.launch_save_plus()  # Then click "Save As New"

# Create Backup (with timestamp)
import savePlus_launcher
savePlus_launcher.launch_save_plus()  # Then click "Create Backup"
```

The tool provides a user-friendly interface for all these operations with detailed version previews, history tracking, and customizable settings.

## Documentation

Visit our [GitHub Pages documentation](https://yourusername.github.io/saveplus/) for comprehensive guides:

- [Features Overview](https://yourusername.github.io/saveplus/features.html)
- [Complete Documentation](https://yourusername.github.io/saveplus/documentation.html)
- [Download & Installation](https://yourusername.github.io/saveplus/download.html)
- [Version History](https://yourusername.github.io/saveplus/changelog.html)

## Requirements

- Maya 2025 (limited compatibility with 2023-2024)
- Windows 10/11, macOS 12+, or Linux (CentOS/Rocky Linux 8.6+)
- PySide6 (included with Maya 2025)

## Attribution and Acknowledgments

SavePlus builds upon the foundation of the original MEL script developed by Neal Singleton. The Python port and enhanced functionality draw significant inspiration from Chris Zurbrigg's Python tools and courses for Maya development.

Special thanks to:
- Neal Singleton for the original MEL script concept and versioning logic
- Chris Zurbrigg for his invaluable Maya Python tutorials and UI component designs
- The Maya community for feedback and testing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions to improve SavePlus! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information on how to participate in the project.