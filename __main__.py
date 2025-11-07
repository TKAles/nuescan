#!/usr/bin/env python3
"""
nueScan - SRAS Scan Planning and Control Software
Entry point for the application

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import NueScanMainWindow


def main():
    """Main entry point for nueScan application"""
    app = QApplication(sys.argv)
    app.setApplicationName("nueScan")
    app.setOrganizationName("SRAS")
    app.setApplicationVersion("0.1.0")

    # Create and show main window
    main_window = NueScanMainWindow()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
