"""
Helios Laser Driver
Complete RS-232 driver for Helios laser systems

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import serial
import serial.tools.list_ports
import time
import threading
from typing import Dict, List, Optional, Tuple

from hardware.helios_protocol import (
    HeliosProtocol, HeliosCommand, HeliosStatus, PulseMode
)


class HeliosDriver:
    """
    Complete driver for Helios laser system

    Features:
    - RS-232 communication at 9600 baud
    - All protocol commands supported
    - Thread-safe operation
    - Temperature monitoring
    - Status monitoring
    - Power monitoring
    """

    # RS-232 Settings (from protocol document)
    BAUDRATE = 9600
    DATABITS = 8
    PARITY = 'N'
    STOPBITS = 1

    def __init__(self, timeout: float = 2.0):
        """
        Initialize Helios driver

        Args:
            timeout: Serial communication timeout in seconds
        """
        self.protocol = HeliosProtocol()
        self.timeout = timeout

        # Serial connection
        self._serial: Optional[serial.Serial] = None
        self._port_name = ""
        self._connected = False

        # Communication lock for thread safety
        self._comm_lock = threading.Lock()

        # Cached state
        self._laser_enabled = False
        self._pulse_mode = PulseMode.CONTINUOUS_PULSING
        self._frequency_hz = 10000.0
        self._current_ma = 500.0
        self._controller_serial = ""
        self._head_serial = ""

        # Temperature monitoring (in °C)
        self._pump_temp_c = 0.0
        self._resonator_temp_c = 0.0
        self._qswitch_temp_c = 0.0
        self._power_stage_temp_c = 0.0

        # Status
        self._status = HeliosStatus(0)
        self._operation_hours = 0.0
        self._power_mw = 0.0

        print("INFO: Helios Laser driver initialized")

    # ==================== Connection Management ====================

    @staticmethod
    def list_available_ports() -> List[str]:
        """
        List available serial ports

        Returns:
            list: Available port names
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str) -> bool:
        """
        Connect to Helios laser

        Args:
            port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')

        Returns:
            bool: True if connection successful
        """
        try:
            print(f"INFO: Connecting to Helios laser on {port}")

            self._serial = serial.Serial(
                port=port,
                baudrate=self.BAUDRATE,
                bytesize=self.DATABITS,
                parity=self.PARITY,
                stopbits=self.STOPBITS,
                timeout=self.timeout
            )

            self._port_name = port
            self._connected = True

            # Read serial numbers
            time.sleep(0.5)
            self._controller_serial = self.query_controller_serial()
            time.sleep(0.5)
            self._head_serial = self.query_head_serial()
            time.sleep(0.5)

            # Read initial state
            self._update_cached_state()

            print(f"INFO: Connected to Helios laser on {port}")
            print(f"  Controller S/N: {self._controller_serial}")
            print(f"  Head S/N: {self._head_serial}")
            return True

        except serial.SerialException as e:
            print(f"ERROR: Failed to connect to {port}: {e}")
            self._connected = False
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from Helios laser

        Returns:
            bool: True if disconnection successful
        """
        if not self._connected:
            return True

        try:
            print("INFO: Disconnecting from Helios laser")

            # Turn off laser before disconnecting
            self.set_laser_enable(False)
            time.sleep(0.5)

            # Close serial port
            if self._serial and self._serial.is_open:
                self._serial.close()

            self._connected = False
            print("INFO: Disconnected from Helios laser")
            return True

        except Exception as e:
            print(f"ERROR: Error during disconnect: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if laser is connected"""
        return self._connected and self._serial and self._serial.is_open

    # ==================== Communication Methods ====================

    def _send_command(self, command: bytes) -> bool:
        """
        Send command to laser (no response expected)

        Args:
            command: Command bytes to send

        Returns:
            bool: True if send successful
        """
        if not self.is_connected():
            print("ERROR: Cannot send command - not connected")
            return False

        try:
            with self._comm_lock:
                self._serial.write(command)
                self._serial.flush()
            return True
        except serial.SerialException as e:
            print(f"ERROR: Failed to send command: {e}")
            return False

    def _query(self, command: bytes) -> Optional[str]:
        """
        Send query and read response

        Args:
            command: Query command bytes

        Returns:
            str: Response string, or None if error
        """
        if not self.is_connected():
            print("ERROR: Cannot query - not connected")
            return None

        try:
            with self._comm_lock:
                # Clear input buffer
                self._serial.reset_input_buffer()

                # Send query
                self._serial.write(command)
                self._serial.flush()

                # Read response (terminated by CR)
                response = self._serial.read_until(b'\r')

                if not response:
                    print("ERROR: No response from laser")
                    return None

                return HeliosCommand.parse_response(response)

        except serial.SerialException as e:
            print(f"ERROR: Query failed: {e}")
            return None

    def _set_and_verify(self, set_cmd: bytes, query_cmd: bytes,
                       expected_value: str, retries: int = 3) -> bool:
        """
        Set a value and verify it was set correctly

        Args:
            set_cmd: Command to set value
            query_cmd: Command to query value
            expected_value: Expected response
            retries: Number of retry attempts

        Returns:
            bool: True if value was set and verified
        """
        for attempt in range(retries):
            # Send set command
            if not self._send_command(set_cmd):
                continue

            time.sleep(0.5)  # Wait 500ms for laser to process (per documentation)

            # Query to verify
            response = self._query(query_cmd)
            if response and response == expected_value:
                return True

            if attempt < retries - 1:
                print(f"DEBUG: Verification failed, retrying ({attempt + 1}/{retries})")
                time.sleep(0.5)

        print(f"ERROR: Failed to set and verify value after {retries} attempts")
        return False

    # ==================== Laser Control ====================

    def set_laser_enable(self, enabled: bool) -> bool:
        """
        Enable or disable laser

        Args:
            enabled: True to enable, False to disable

        Returns:
            bool: True if command successful
        """
        print(f"DEBUG: {'Enabling' if enabled else 'Disabling'} laser")

        cmd = self.protocol.cmd_set_laser_enable(enabled)
        query_cmd = self.protocol.cmd_query_laser_enable()
        expected = "1" if enabled else "0"

        if self._set_and_verify(cmd, query_cmd, expected):
            self._laser_enabled = enabled
            return True
        return False

    def is_laser_enabled(self) -> bool:
        """Check if laser is currently enabled"""
        return self._laser_enabled

    def query_laser_enable(self) -> bool:
        """Query laser enable state from hardware"""
        cmd = self.protocol.cmd_query_laser_enable()
        response = self._query(cmd)
        if response:
            self._laser_enabled = (response == "1")
            return self._laser_enabled
        return False

    # ==================== Pulse Mode Control ====================

    def set_pulse_mode(self, mode: PulseMode) -> bool:
        """
        Set pulse mode

        Args:
            mode: PulseMode enum value

        Returns:
            bool: True if command successful
        """
        print(f"DEBUG: Setting pulse mode to {mode.name}")

        cmd = self.protocol.cmd_set_pulse_mode(mode)
        query_cmd = self.protocol.cmd_query_pulse_mode()
        expected = str(mode.value)

        if self._set_and_verify(cmd, query_cmd, expected):
            self._pulse_mode = mode
            return True
        return False

    def get_pulse_mode(self) -> PulseMode:
        """Get current pulse mode"""
        return self._pulse_mode

    # ==================== Frequency Control ====================

    def set_frequency_hz(self, freq_hz: float) -> bool:
        """
        Set laser frequency in Hz

        Args:
            freq_hz: Frequency in Hz (16.7 kHz to 125 kHz)

        Returns:
            bool: True if command successful
        """
        print(f"DEBUG: Setting laser frequency to {freq_hz} Hz")

        try:
            cmd = self.protocol.cmd_set_frequency_hz(freq_hz)
            period_ns = self.protocol.frequency_to_period_ns(freq_hz)
            query_cmd = self.protocol.cmd_query_frequency()
            expected = str(period_ns)

            if self._set_and_verify(cmd, query_cmd, expected):
                self._frequency_hz = freq_hz
                return True
        except ValueError as e:
            print(f"ERROR: {e}")
        return False

    def get_frequency_hz(self) -> float:
        """Get current frequency in Hz"""
        return self._frequency_hz

    def query_frequency_hz(self) -> Optional[float]:
        """Query frequency from hardware (returns Hz)"""
        cmd = self.protocol.cmd_query_frequency()
        response = self._query(cmd)
        if response:
            try:
                period_ns = int(response)
                freq_hz = self.protocol.period_ns_to_frequency(period_ns)
                self._frequency_hz = freq_hz
                return freq_hz
            except (ValueError, ZeroDivisionError) as e:
                print(f"ERROR: Failed to parse frequency: {e}")
        return None

    # ==================== Current Control ====================

    def set_current_ma(self, current_ma: float) -> bool:
        """
        Set laser diode current in mA

        Args:
            current_ma: Current in mA (0-7000)

        Returns:
            bool: True if command successful
        """
        print(f"DEBUG: Setting laser current to {current_ma} mA")

        try:
            cmd = self.protocol.cmd_set_current_ma(current_ma)
            query_cmd = self.protocol.cmd_query_current()
            expected = str(int(current_ma))

            if self._set_and_verify(cmd, query_cmd, expected):
                self._current_ma = current_ma
                return True
        except ValueError as e:
            print(f"ERROR: {e}")
        return False

    def get_current_ma(self) -> float:
        """Get current setting in mA"""
        return self._current_ma

    # ==================== Temperature Monitoring ====================

    def query_pump_temperature_c(self) -> Optional[float]:
        """Query pump diode temperature in °C"""
        cmd = self.protocol.cmd_query_pump_temp()
        response = self._query(cmd)
        if response:
            try:
                temp_mc = int(response)
                temp_c = self.protocol.millicelsius_to_celsius(temp_mc)
                self._pump_temp_c = temp_c
                return temp_c
            except ValueError as e:
                print(f"ERROR: Failed to parse temperature: {e}")
        return None

    def query_resonator_temperature_c(self) -> Optional[float]:
        """Query resonator/SHG temperature in °C"""
        cmd = self.protocol.cmd_query_resonator_temp()
        response = self._query(cmd)
        if response:
            try:
                temp_mc = int(response)
                temp_c = self.protocol.millicelsius_to_celsius(temp_mc)
                self._resonator_temp_c = temp_c
                return temp_c
            except ValueError as e:
                print(f"ERROR: Failed to parse temperature: {e}")
        return None

    def query_qswitch_temperature_c(self) -> Optional[float]:
        """Query q-switch temperature in °C"""
        cmd = self.protocol.cmd_query_qswitch_temp()
        response = self._query(cmd)
        if response:
            try:
                temp_mc = int(response)
                temp_c = self.protocol.millicelsius_to_celsius(temp_mc)
                self._qswitch_temp_c = temp_c
                return temp_c
            except ValueError as e:
                print(f"ERROR: Failed to parse temperature: {e}")
        return None

    def query_power_stage_temperature_c(self) -> Optional[float]:
        """Query controller power stage temperature in °C"""
        cmd = self.protocol.cmd_query_power_stage_temp()
        response = self._query(cmd)
        if response:
            try:
                temp_mc = int(response)
                temp_c = self.protocol.millicelsius_to_celsius(temp_mc)
                self._power_stage_temp_c = temp_c
                return temp_c
            except ValueError as e:
                print(f"ERROR: Failed to parse temperature: {e}")
        return None

    def query_all_temperatures(self) -> Dict[str, float]:
        """
        Query all temperatures

        Returns:
            dict: Temperature readings in °C
        """
        temps = {}
        temps['pump'] = self.query_pump_temperature_c()
        time.sleep(0.5)
        temps['resonator'] = self.query_resonator_temperature_c()
        time.sleep(0.5)
        temps['qswitch'] = self.query_qswitch_temperature_c()
        time.sleep(0.5)
        temps['power_stage'] = self.query_power_stage_temperature_c()
        return temps

    # ==================== Status and Monitoring ====================

    def query_status(self) -> HeliosStatus:
        """Query status register"""
        cmd = self.protocol.cmd_query_status()
        response = self._query(cmd)
        if response:
            try:
                status_value = int(response)
                self._status = HeliosStatus(status_value)
                return self._status
            except ValueError as e:
                print(f"ERROR: Failed to parse status: {e}")
        return self._status

    def clear_status(self) -> bool:
        """Clear status register"""
        cmd = self.protocol.cmd_clear_status()
        return self._send_command(cmd)

    def clear_errors(self) -> bool:
        """Clear controller errors"""
        cmd = self.protocol.cmd_clear_errors()
        return self._send_command(cmd)

    def query_power_monitor_mw(self) -> Optional[float]:
        """Query laser power monitor in mW"""
        cmd = self.protocol.cmd_query_power_monitor()
        response = self._query(cmd)
        if response:
            try:
                power_mw = float(response)
                self._power_mw = power_mw
                return power_mw
            except ValueError as e:
                print(f"ERROR: Failed to parse power: {e}")
        return None

    def query_operation_hours(self) -> Optional[float]:
        """Query laser diode operation time in hours"""
        cmd = self.protocol.cmd_query_operation_time()
        response = self._query(cmd)
        if response:
            try:
                hours = float(response)
                self._operation_hours = hours
                return hours
            except ValueError as e:
                print(f"ERROR: Failed to parse operation time: {e}")
        return None

    # ==================== Serial Numbers ====================

    def query_controller_serial(self) -> str:
        """Query controller serial number"""
        cmd = self.protocol.cmd_query_controller_serial()
        response = self._query(cmd)
        if response:
            self._controller_serial = response
            return response
        return ""

    def query_head_serial(self) -> str:
        """Query laser head serial number"""
        cmd = self.protocol.cmd_query_head_serial()
        response = self._query(cmd)
        if response:
            self._head_serial = response
            return response
        return ""

    def get_controller_serial(self) -> str:
        """Get cached controller serial number"""
        return self._controller_serial

    def get_head_serial(self) -> str:
        """Get cached head serial number"""
        return self._head_serial

    # ==================== Factory Reset ====================

    def restore_factory_settings(self) -> bool:
        """
        Restore factory settings

        WARNING: This will reset all parameters to factory defaults.
        Laser must be disabled before calling this method.
        After calling, wait 2 seconds before power cycling.

        Returns:
            bool: True if command sent successfully
        """
        if self._laser_enabled:
            print("ERROR: Laser must be disabled before factory reset")
            return False

        print("WARNING: Restoring factory settings")
        cmd = self.protocol.cmd_restore_factory()
        if self._send_command(cmd):
            print("INFO: Factory settings restored. Wait 2s before power cycle.")
            time.sleep(2)
            return True
        return False

    # ==================== State Management ====================

    def _update_cached_state(self):
        """Update all cached state from hardware"""
        self.query_laser_enable()
        time.sleep(0.5)
        self.query_frequency_hz()
        time.sleep(0.5)
        # Current is write-only in some modes, skip query
        self.query_status()

    def get_status(self) -> Dict:
        """
        Get complete laser status

        Returns:
            dict: Comprehensive status dictionary
        """
        return {
            'connected': self.is_connected(),
            'laser_enabled': self._laser_enabled,
            'pulse_mode': self._pulse_mode.name,
            'frequency_hz': self._frequency_hz,
            'current_ma': self._current_ma,
            'power_mw': self._power_mw,
            'operation_hours': self._operation_hours,
            'temperatures': {
                'pump_c': self._pump_temp_c,
                'resonator_c': self._resonator_temp_c,
                'qswitch_c': self._qswitch_temp_c,
                'power_stage_c': self._power_stage_temp_c
            },
            'status_value': self._status.value,
            'has_errors': self._status.has_errors(),
            'controller_serial': self._controller_serial,
            'head_serial': self._head_serial
        }

    def update_status(self):
        """Update status information from hardware"""
        if not self.is_connected():
            return

        self.query_status()
        time.sleep(0.5)
        self.query_power_monitor_mw()
        time.sleep(0.5)
        self.query_all_temperatures()
