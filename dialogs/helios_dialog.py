"""
Helios Device Settings Dialog
Configures Helios laser parameters and COM port

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from hardware.helios_driver import HeliosDriver


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
        # Get available ports from system
        ports = HeliosDriver.list_available_ports()

        if ports:
            self.cb_helios_port.addItems(ports)
            print(f"DEBUG: Found {len(ports)} available COM ports")
        else:
            # No ports found
            self.cb_helios_port.addItem("No ports found")
            print("WARNING: No COM ports found")

    def refresh_com_ports(self):
        """Refresh the COM port list"""
        current_port = self.cb_helios_port.currentText()
        self.cb_helios_port.clear()
        self._populate_com_ports()

        # Try to restore previous selection
        index = self.cb_helios_port.findText(current_port)
        if index >= 0:
            self.cb_helios_port.setCurrentIndex(index)

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

        Validates input ranges before returning.

        Returns:
            dict: Helios device settings, or None if validation fails
        """
        # Validate frequency
        try:
            frequency_hz = float(self.le_helios_frequency.text())
            # Convert to period to check valid range (8000-60000 ns)
            # Valid frequencies: ~16.7 kHz to 125 kHz
            if frequency_hz < 16666 or frequency_hz > 125000:
                QMessageBox.warning(
                    self, "Invalid Frequency",
                    f"Frequency must be between 16.7 kHz and 125 kHz\n"
                    f"(Period: 8000-60000 ns)\n\n"
                    f"Entered: {frequency_hz/1000:.1f} kHz"
                )
                return None
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Frequency",
                "Please enter a valid frequency value in Hz"
            )
            return None

        # Validate current
        try:
            current_ma = float(self.le_helios_current.text())
            if current_ma < 0 or current_ma > 7000:
                QMessageBox.warning(
                    self, "Invalid Current",
                    f"Current must be between 0 and 7000 mA\n\n"
                    f"Entered: {current_ma} mA"
                )
                return None
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Current",
                "Please enter a valid current value in mA"
            )
            return None

        # Validate COM port selection
        com_port = self.cb_helios_port.currentText()
        if not com_port or com_port == "No ports found":
            QMessageBox.warning(
                self, "No Port Selected",
                "Please select a valid COM port"
            )
            return None

        return {
            'com_port': com_port,
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
