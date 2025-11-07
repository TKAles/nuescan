"""
Microscope Controller
Handles communication with Genesis and Helios microscope/laser systems

Genesis: Laser scanning microscope system (stub)
Helios: Laser control system with frequency and current control (full implementation)
Both systems communicate via USB/Serial interfaces

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import time
from typing import Dict, Optional
from hardware.helios_driver import HeliosDriver, PulseMode


class MicroscopeController:
    """
    Controller for Genesis and Helios microscope systems

    Provides methods for:
    - System connection and initialization
    - Interlock status monitoring
    - Parameter configuration
    - Safety checks
    """

    def __init__(self):
        """Initialize microscope controller"""
        # Genesis state (stub)
        self._genesis_connected = False
        self._genesis_ready = False
        self._genesis_interlocked = False
        self._genesis_power_mw = 0.0

        # Helios driver (full implementation)
        self._helios_driver = HeliosDriver()
        self._helios_port = None

        # System interlock (master safety)
        self._system_interlocked = False

        print("INFO: Microscope controller initialized")
        print("  - Genesis: Stub implementation")
        print("  - Helios: Full RS-232 driver")

    # ==================== Genesis Methods ====================

    def connect_genesis(self) -> bool:
        """
        Connect to Genesis laser scanning microscope

        Returns:
            bool: True if connection successful
        """
        print("DEBUG: Connecting to Genesis microscope")

        # Stub implementation
        time.sleep(0.1)

        self._genesis_connected = True
        self._genesis_ready = True
        self._genesis_interlocked = True  # Assume interlocks OK

        print("INFO: Genesis microscope connected")
        return True

    def disconnect_genesis(self) -> bool:
        """
        Disconnect from Genesis microscope

        Returns:
            bool: True if disconnection successful
        """
        print("DEBUG: Disconnecting from Genesis microscope")

        self._genesis_connected = False
        self._genesis_ready = False

        print("INFO: Genesis microscope disconnected")
        return True

    def apply_genesis_settings(self, settings: Dict) -> bool:
        """
        Apply Genesis configuration settings

        Args:
            settings: Dictionary containing Genesis parameters

        Returns:
            bool: True if settings applied successfully
        """
        print("DEBUG: Applying Genesis settings")
        print(f"  Power: {settings.get('power_mw', 0)} mW")

        if not self._genesis_connected:
            print("ERROR: Genesis not connected")
            return False

        self._genesis_power_mw = settings.get('power_mw', 0.0)

        # Stub - would send commands to actual hardware
        time.sleep(0.05)

        print("INFO: Genesis settings applied")
        return True

    def get_genesis_status(self) -> Dict[str, any]:
        """
        Get Genesis microscope status

        Returns:
            dict: Genesis status information
        """
        return {
            'connected': self._genesis_connected,
            'ready': self._genesis_ready,
            'interlocked': self._genesis_interlocked,
            'power_mw': self._genesis_power_mw
        }

    # ==================== Helios Methods ====================

    def connect_helios(self, port: str) -> bool:
        """
        Connect to Helios laser system

        Args:
            port: COM port for Helios device

        Returns:
            bool: True if connection successful
        """
        print(f"DEBUG: Connecting to Helios on {port}")

        if not self._helios_driver.connect(port):
            return False

        self._helios_port = port
        print(f"INFO: Helios connected on {port}")
        print(f"  Controller S/N: {self._helios_driver.get_controller_serial()}")
        print(f"  Head S/N: {self._helios_driver.get_head_serial()}")
        return True

    def disconnect_helios(self) -> bool:
        """
        Disconnect from Helios laser system

        Returns:
            bool: True if disconnection successful
        """
        print("DEBUG: Disconnecting from Helios")
        return self._helios_driver.disconnect()

    def is_helios_connected(self) -> bool:
        """Check if Helios is connected"""
        return self._helios_driver.is_connected()

    def apply_helios_settings(self, settings: Dict) -> bool:
        """
        Apply Helios configuration settings

        This method connects and configures the Helios laser with the
        specified parameters from the settings dialog.

        Args:
            settings: Dictionary containing:
                - com_port: COM port name
                - frequency_hz: Laser frequency in Hz
                - current_ma: Laser diode current in mA

        Returns:
            bool: True if settings applied successfully
        """
        if settings is None:
            print("ERROR: No settings provided")
            return False

        print("DEBUG: Applying Helios settings")
        print(f"  Port: {settings.get('com_port', 'N/A')}")
        print(f"  Frequency: {settings.get('frequency_hz', 0)} Hz")
        print(f"  Current: {settings.get('current_ma', 0)} mA")

        # Connect if not already connected or port changed
        port = settings.get('com_port')
        if not port:
            print("ERROR: No COM port specified")
            return False

        if not self.is_helios_connected() or port != self._helios_port:
            if self.is_helios_connected():
                self.disconnect_helios()
            if not self.connect_helios(port):
                return False

        # Set frequency
        freq_hz = settings.get('frequency_hz', 0.0)
        if freq_hz > 0:
            if not self._helios_driver.set_frequency_hz(freq_hz):
                print("ERROR: Failed to set frequency")
                return False
            time.sleep(0.05)

        # Set current
        current_ma = settings.get('current_ma', 0.0)
        if current_ma > 0:
            if not self._helios_driver.set_current_ma(current_ma):
                print("ERROR: Failed to set current")
                return False
            time.sleep(0.05)

        # Set to continuous pulsing mode by default
        if not self._helios_driver.set_pulse_mode(PulseMode.CONTINUOUS_PULSING):
            print("WARNING: Failed to set pulse mode")

        print("INFO: Helios settings applied successfully")
        return True

    def helios_enable_laser(self, enabled: bool) -> bool:
        """
        Enable or disable Helios laser

        Args:
            enabled: True to enable, False to disable

        Returns:
            bool: True if command successful
        """
        if not self.is_helios_connected():
            print("ERROR: Helios not connected")
            return False

        return self._helios_driver.set_laser_enable(enabled)

    def is_helios_laser_enabled(self) -> bool:
        """Check if Helios laser is currently enabled"""
        if not self.is_helios_connected():
            return False
        return self._helios_driver.is_laser_enabled()

    def get_helios_status(self) -> Dict[str, any]:
        """
        Get Helios laser system status

        Returns:
            dict: Helios status information
        """
        if not self.is_helios_connected():
            return {
                'connected': False,
                'ready': False,
                'interlocked': False,
                'port': None,
                'frequency_hz': 0.0,
                'current_ma': 0.0,
                'laser_enabled': False,
                'power_mw': 0.0
            }

        # Get comprehensive status from driver
        status = self._helios_driver.get_status()

        return {
            'connected': status['connected'],
            'ready': not status['has_errors'],
            'interlocked': not status['has_errors'],  # Use error state as interlock
            'port': self._helios_port,
            'frequency_hz': status['frequency_hz'],
            'current_ma': status['current_ma'],
            'laser_enabled': status['laser_enabled'],
            'power_mw': status['power_mw'],
            'operation_hours': status['operation_hours'],
            'controller_serial': status['controller_serial'],
            'head_serial': status['head_serial']
        }

    def helios_update_status(self):
        """Update Helios status from hardware"""
        if self.is_helios_connected():
            self._helios_driver.update_status()

    # ==================== Combined Status Methods ====================

    def get_status(self) -> Dict[str, any]:
        """
        Get complete microscope system status

        Returns:
            dict: Combined status for Genesis, Helios, and interlocks
        """
        # Get Helios status from driver
        helios_status = self.get_helios_status()
        helios_ready = helios_status.get('ready', False)
        helios_interlocked = helios_status.get('interlocked', False)

        return {
            # System-wide
            'interlocked': self._system_interlocked or (
                self._genesis_interlocked and helios_interlocked
            ),

            # Genesis
            'genesis_ready': self._genesis_ready,
            'genesis_interlocked': self._genesis_interlocked,

            # Helios
            'helios_ready': helios_ready,
            'helios_interlocked': helios_interlocked
        }

    def check_interlocks(self) -> bool:
        """
        Check all safety interlocks

        Returns:
            bool: True if all interlocks are satisfied
        """
        # Check Genesis interlocks
        if self._genesis_connected and not self._genesis_interlocked:
            print("WARNING: Genesis interlock not satisfied")
            return False

        # Check Helios interlocks
        if self.is_helios_connected():
            helios_status = self.get_helios_status()
            if not helios_status.get('interlocked', False):
                print("WARNING: Helios interlock not satisfied")
                return False

        return True

    # ==================== Scan Preparation ====================

    def prepare_for_scan(self, params: Dict) -> bool:
        """
        Prepare microscope systems for scanning

        Args:
            params: Scan parameters dictionary

        Returns:
            bool: True if preparation successful
        """
        print("DEBUG: Preparing microscope systems for scan")

        # Check interlocks
        if not self.check_interlocks():
            print("ERROR: Interlock check failed")
            return False

        # Verify systems are ready
        if self._genesis_connected and not self._genesis_ready:
            print("ERROR: Genesis not ready")
            return False

        if self.is_helios_connected():
            helios_status = self.get_helios_status()
            if not helios_status.get('ready', False):
                print("ERROR: Helios not ready")
                return False

        # Configure for scan
        # Stub implementation
        time.sleep(0.1)

        print("INFO: Microscope systems ready for scan")
        return True

    def emergency_stop(self) -> bool:
        """
        Emergency stop all microscope operations

        Returns:
            bool: True if stop successful
        """
        print("WARNING: Emergency stop triggered")

        # Disable all systems
        if self._genesis_connected:
            self._genesis_ready = False

        if self.is_helios_connected():
            # Disable Helios laser immediately
            self._helios_driver.set_laser_enable(False)

        return True
