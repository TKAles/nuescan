"""
Genesis Laser Settings Dialog
Configures Genesis scanning laser parameters
"""

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog


class GenesisDialog(QDialog):
    """Dialog for configuring Genesis laser settings"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load UI file
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'nuescan_genesis_dialog.ui'
        )
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Genesis Laser Settings")

        # Initialize with default values
        self._load_default_settings()

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect dialog signals"""
        # LineEdit text changed
        self.le_genesis_power_mw.textChanged.connect(self.on_power_changed)

        # Dialog buttons are auto-connected by Qt Designer

    def _load_default_settings(self):
        """Load default Genesis settings"""
        self.le_genesis_power_mw.setText("100.0")  # Default 100mW

    def on_power_changed(self, text):
        """Handle scanning power change"""
        print(f"DEBUG: Genesis power changed to: {text}")

    def get_settings(self):
        """
        Get current Genesis settings as a dictionary

        Returns:
            dict: Genesis laser settings
        """
        try:
            power_mw = float(self.le_genesis_power_mw.text())
        except ValueError:
            power_mw = 0.0

        return {
            'power_mw': power_mw
        }

    def set_settings(self, settings):
        """
        Set Genesis settings from a dictionary

        Args:
            settings (dict): Genesis laser settings
        """
        if 'power_mw' in settings:
            self.le_genesis_power_mw.setText(str(settings['power_mw']))
