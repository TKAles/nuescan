"""
Helios Device Settings Dialog
Configures Helios laser parameters and COM port
"""

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog


class HeliosDialog(QDialog):
    """Dialog for configuring Helios device settings"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load UI file
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'nuescan_helios_dialog.ui'
        )
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Helios Device Settings")

        # Initialize with default values
        self._load_default_settings()

        # Connect signals
        self._connect_signals()

        # Populate COM ports
        self._populate_com_ports()

    def _connect_signals(self):
        """Connect dialog signals"""
        # ComboBox value changed
        self.cb_helios_port.currentIndexChanged.connect(self.on_port_changed)

        # LineEdit text changed
        self.le_helios_frequency.textChanged.connect(self.on_frequency_changed)
        self.le_helios_current.textChanged.connect(self.on_current_changed)

        # Dialog buttons are auto-connected by Qt Designer

    def _load_default_settings(self):
        """Load default Helios settings"""
        self.le_helios_frequency.setText("10000")  # Default 10kHz
        self.le_helios_current.setText("500")      # Default 500mA

    def _populate_com_ports(self):
        """Populate available COM ports"""
        # Stub implementation - would scan for actual ports
        self.cb_helios_port.addItems([
            "COM1", "COM2", "COM3", "COM4", "COM5",
            "/dev/ttyUSB0", "/dev/ttyUSB1"
        ])

    def on_port_changed(self, index):
        """Handle COM port selection change"""
        port = self.cb_helios_port.currentText()
        print(f"DEBUG: Helios port changed to: {port}")

    def on_frequency_changed(self, text):
        """Handle frequency change"""
        print(f"DEBUG: Helios frequency changed to: {text}")

    def on_current_changed(self, text):
        """Handle current change"""
        print(f"DEBUG: Helios current changed to: {text}")

    def get_settings(self):
        """
        Get current Helios settings as a dictionary

        Returns:
            dict: Helios device settings
        """
        try:
            frequency_hz = float(self.le_helios_frequency.text())
        except ValueError:
            frequency_hz = 0.0

        try:
            current_ma = float(self.le_helios_current.text())
        except ValueError:
            current_ma = 0.0

        return {
            'com_port': self.cb_helios_port.currentText(),
            'frequency_hz': frequency_hz,
            'current_ma': current_ma
        }

    def set_settings(self, settings):
        """
        Set Helios settings from a dictionary

        Args:
            settings (dict): Helios device settings
        """
        if 'com_port' in settings:
            index = self.cb_helios_port.findText(settings['com_port'])
            if index >= 0:
                self.cb_helios_port.setCurrentIndex(index)

        if 'frequency_hz' in settings:
            self.le_helios_frequency.setText(str(settings['frequency_hz']))

        if 'current_ma' in settings:
            self.le_helios_current.setText(str(settings['current_ma']))
