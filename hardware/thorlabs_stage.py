"""
ThorLabs MLS Stage Controller
Handles communication with ThorLabs MLS 3-axis positioning stage via BBD203 motor controller

The ThorLabs MLS stage provides precision X/Y/Z positioning for scanning operations.
This implementation uses the BBD203 3-channel motor controller with the APT protocol.

Channel Mapping:
- Channel 1: X-axis
- Channel 2: Y-axis
- Channel 3: Z-axis (optional)

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import time
from typing import Dict, Optional

from hardware.bbd203_driver import BBD203Driver
from hardware.bbd203_protocol import TriggerMode
from hardware.stage_settings import StageSettings


class ThorLabsStage:
    """
    Controller for ThorLabs MLS positioning stage using BBD203 motor controller

    Provides methods for:
    - Connecting/disconnecting from stage
    - Homing axes
    - Position control and readout
    - Status monitoring
    """

    # Channel mapping
    X_AXIS = 1
    Y_AXIS = 2
    Z_AXIS = 3

    def __init__(self, encoder_counts_per_mm: int = 20000, settings_file: Optional[str] = None):
        """
        Initialize ThorLabs stage controller

        Args:
            encoder_counts_per_mm: Encoder resolution (default: 20000 for MLS203)
            settings_file: Path to settings file (default: ~/.nuescan/stage_settings.json)
        """
        self._driver = BBD203Driver(encoder_counts_per_mm)
        self._port = None

        # Settings manager
        self.settings = StageSettings(settings_file)

        # Scanning state
        self._scanning = False

        # Default velocity and acceleration (can be overridden by settings)
        self._default_velocity = 1.0  # mm/s
        self._default_accel = 5.0     # mm/s²

        print("INFO: ThorLabs Stage controller initialized (BBD203 driver)")

    def connect(self, serial_number: str, baudrate: int = 115200) -> bool:
        """
        Connect to ThorLabs stage via BBD203 controller using serial number

        The serial number is printed on the BBD203 controller (e.g., '83123456').
        The driver will automatically find the USB device and connect.

        Args:
            serial_number: BBD203 device serial number
            baudrate: Baud rate (default: 115200)

        Returns:
            bool: True if connection successful
        """
        print(f"DEBUG: Connecting to BBD203/MLS Stage with serial number {serial_number}")

        # Connect by serial number - driver will auto-find the port
        if not self._driver.connect_by_serial(serial_number, baudrate):
            return False

        self._port = serial_number  # Store serial for reference

        # Enable all channels
        time.sleep(0.2)
        self._driver.enable_channel(self.X_AXIS, True)
        time.sleep(0.1)
        self._driver.enable_channel(self.Y_AXIS, True)
        time.sleep(0.1)
        self._driver.enable_channel(self.Z_AXIS, True)
        time.sleep(0.1)

        # Apply startup settings from configuration
        self.apply_startup_settings()

        print("INFO: Stage connected and channels enabled")
        return True

    def disconnect(self) -> bool:
        """
        Disconnect from ThorLabs stage

        Returns:
            bool: True if disconnection successful
        """
        self._scanning = False
        return self._driver.disconnect()

    def is_connected(self) -> bool:
        """Check if stage is connected"""
        return self._driver.is_connected()

    # ==================== Homing ====================

    def home_all_axes(self, wait: bool = True, timeout: float = 60.0) -> bool:
        """
        Home all axes (X, Y, Z)

        Args:
            wait: If True, block until homing complete
            timeout: Timeout in seconds

        Returns:
            bool: True if homing successful
        """
        print("DEBUG: Homing all axes")

        if not self.is_connected():
            print("ERROR: Cannot home - stage not connected")
            return False

        return self._driver.home_all_channels(wait=wait, timeout=timeout)

    def home_axis(self, axis: str, wait: bool = True, timeout: float = 30.0) -> bool:
        """
        Home a specific axis

        Args:
            axis: Axis to home ('X', 'Y', or 'Z')
            wait: If True, block until homing complete
            timeout: Timeout in seconds

        Returns:
            bool: True if homing successful
        """
        axis = axis.upper()
        if axis not in ['X', 'Y', 'Z']:
            print(f"ERROR: Invalid axis: {axis}")
            return False

        channel = {'X': self.X_AXIS, 'Y': self.Y_AXIS, 'Z': self.Z_AXIS}[axis]

        print(f"DEBUG: Homing {axis} axis (channel {channel})")

        return self._driver.home_channel(channel, wait=wait, timeout=timeout)

    # ==================== Motion Control ====================

    def move_absolute(self, x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None,
                     wait: bool = False) -> bool:
        """
        Move to absolute position

        Args:
            x: X position in mm (None to leave unchanged)
            y: Y position in mm (None to leave unchanged)
            z: Z position in mm (None to leave unchanged)
            wait: If True, block until move complete

        Returns:
            bool: True if move successful
        """
        if not self.is_connected():
            print("ERROR: Stage not connected")
            return False

        success = True

        # Move each axis that was specified
        if x is not None:
            if not self._driver.move_absolute(self.X_AXIS, x, wait=wait):
                success = False

        if y is not None:
            if not self._driver.move_absolute(self.Y_AXIS, y, wait=wait):
                success = False

        if z is not None:
            if not self._driver.move_absolute(self.Z_AXIS, z, wait=wait):
                success = False

        return success

    def move_relative(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
                     wait: bool = False) -> bool:
        """
        Move relative to current position

        Args:
            dx: X displacement in mm
            dy: Y displacement in mm
            dz: Z displacement in mm
            wait: If True, block until move complete

        Returns:
            bool: True if move successful
        """
        if not self.is_connected():
            print("ERROR: Stage not connected")
            return False

        success = True

        if dx != 0.0:
            if not self._driver.move_relative(self.X_AXIS, dx, wait=wait):
                success = False

        if dy != 0.0:
            if not self._driver.move_relative(self.Y_AXIS, dy, wait=wait):
                success = False

        if dz != 0.0:
            if not self._driver.move_relative(self.Z_AXIS, dz, wait=wait):
                success = False

        return success

    def stop_all(self, immediate: bool = True) -> bool:
        """
        Stop all motion

        Args:
            immediate: If True, stop immediately; if False, decelerate

        Returns:
            bool: True if stop successful
        """
        return self._driver.stop(0, immediate)  # Channel 0 = all channels

    # ==================== Position and Status ====================

    def get_position(self) -> Dict[str, float]:
        """
        Get current position

        Returns:
            dict: Current X, Y, Z positions in mm
        """
        return {
            'x': self._driver.get_position(self.X_AXIS) or 0.0,
            'y': self._driver.get_position(self.Y_AXIS) or 0.0,
            'z': self._driver.get_position(self.Z_AXIS) or 0.0
        }

    def get_status(self) -> Dict[str, bool]:
        """
        Get current stage status

        Returns:
            dict: Status information compatible with main_window expectations
        """
        x_status = self._driver.get_channel_status(self.X_AXIS) or {}
        y_status = self._driver.get_channel_status(self.Y_AXIS) or {}
        z_status = self._driver.get_channel_status(self.Z_AXIS) or {}

        # Determine if any axis is moving
        moving = (x_status.get('moving', False) or
                 y_status.get('moving', False) or
                 z_status.get('moving', False))

        # Determine if stage is ready (all enabled axes are homed)
        x_ready = x_status.get('enabled', False) and x_status.get('homed', False)
        y_ready = y_status.get('enabled', False) and y_status.get('homed', False)
        ready = x_ready and y_ready  # Z is optional

        return {
            'connected': self.is_connected(),
            'x_homed': x_status.get('homed', False),
            'y_homed': y_status.get('homed', False),
            'z_homed': z_status.get('homed', False),
            'ready': ready,
            'scanning': self._scanning,
            'moving': moving
        }

    # ==================== Velocity Control ====================

    def set_velocity(self, velocity_mm_s: float, accel_mm_s2: float,
                    axis: Optional[str] = None) -> bool:
        """
        Set velocity and acceleration parameters

        Args:
            velocity_mm_s: Maximum velocity in mm/s
            accel_mm_s2: Acceleration in mm/s²
            axis: Specific axis ('X', 'Y', 'Z'), or None for all axes

        Returns:
            bool: True if parameters set successfully
        """
        if axis:
            axis = axis.upper()
            if axis not in ['X', 'Y', 'Z']:
                print(f"ERROR: Invalid axis: {axis}")
                return False

            channel = {'X': self.X_AXIS, 'Y': self.Y_AXIS, 'Z': self.Z_AXIS}[axis]
            return self._driver.set_velocity_params(channel, velocity_mm_s, accel_mm_s2)
        else:
            # Set for all axes
            success = True
            for channel in [self.X_AXIS, self.Y_AXIS, self.Z_AXIS]:
                if not self._driver.set_velocity_params(channel, velocity_mm_s, accel_mm_s2):
                    success = False
                time.sleep(0.05)
            return success

    # ==================== Scan Support ====================

    def prepare_for_scan(self, params: Dict) -> bool:
        """
        Prepare stage for scanning operation

        Args:
            params: Scan parameters dictionary

        Returns:
            bool: True if preparation successful
        """
        print("DEBUG: Preparing stage for scan")

        status = self.get_status()
        if not status['ready']:
            print("ERROR: Stage not ready for scanning")
            return False

        # Move to start position
        x_start = params.get('x_start', 0)
        y_start = params.get('y_start', 0)

        print(f"  Moving to scan start: X={x_start} mm, Y={y_start} mm")

        if not self.move_absolute(x=x_start, y=y_start, wait=True):
            print("ERROR: Failed to move to start position")
            return False

        self._scanning = True
        print("INFO: Stage ready for scanning")
        return True

    def stop_scan(self) -> bool:
        """
        Stop current scan operation

        Returns:
            bool: True if stop successful
        """
        print("DEBUG: Stopping scan")
        self._scanning = False
        return self.stop_all(immediate=True)

    # ==================== Utility Methods ====================

    def identify(self, channel: Optional[int] = None) -> bool:
        """
        Flash front panel LEDs to identify controller

        Args:
            channel: Specific channel (1, 2, 3), or None for all

        Returns:
            bool: True if command sent successfully
        """
        if channel is None:
            # Identify all channels
            for ch in [1, 2, 3]:
                self._driver.identify(ch)
                time.sleep(0.1)
            return True
        else:
            return self._driver.identify(channel)

    @staticmethod
    def list_available_ports():
        """
        List available serial ports (deprecated - use list_devices instead)

        Returns:
            list: Available port names
        """
        return BBD203Driver.list_available_ports()

    @staticmethod
    def list_devices():
        """
        List all connected ThorLabs BBD203 devices

        Returns:
            list: List of dicts with device info including 'serial' and 'port'
        """
        return BBD203Driver.list_thorlabs_devices()

    # ==================== Settings Management ====================

    def apply_startup_settings(self) -> bool:
        """
        Apply saved settings to the stage on startup

        This includes:
        - Velocity parameters for all axes
        - Acceleration parameters for all axes
        - Trigger configuration for all axes

        Returns:
            bool: True if all settings applied successfully
        """
        print("INFO: Applying startup settings to stage")

        success = True

        # Apply velocity and acceleration settings
        velocities = self.settings.get_all_velocities()
        accelerations = self.settings.get_all_accelerations()

        print(f"  Velocity settings: X={velocities['x_axis']} mm/s, "
              f"Y={velocities['y_axis']} mm/s, Z={velocities['z_axis']} mm/s")
        print(f"  Acceleration settings: X={accelerations['x_axis']} mm/s², "
              f"Y={accelerations['y_axis']} mm/s², Z={accelerations['z_axis']} mm/s²")

        # Set velocity/acceleration for each axis
        if not self._driver.set_velocity_params(
            self.X_AXIS, velocities['x_axis'], accelerations['x_axis']
        ):
            success = False
        time.sleep(0.05)

        if not self._driver.set_velocity_params(
            self.Y_AXIS, velocities['y_axis'], accelerations['y_axis']
        ):
            success = False
        time.sleep(0.05)

        if not self._driver.set_velocity_params(
            self.Z_AXIS, velocities['z_axis'], accelerations['z_axis']
        ):
            success = False
        time.sleep(0.05)

        # Apply trigger configuration for each axis
        for axis_name, channel in [('x_axis', self.X_AXIS),
                                   ('y_axis', self.Y_AXIS),
                                   ('z_axis', self.Z_AXIS)]:
            trigger_config = self.settings.get_trigger_config(axis_name)

            if not self._driver.set_trigger_mode(
                channel,
                trigger_config['mode'],
                trigger_config['polarity'],
                trigger_config['start_pos_fwd'],
                trigger_config['start_pos_rev'],
                trigger_config['interval_fwd'],
                trigger_config['interval_rev']
            ):
                success = False
            time.sleep(0.05)

        if success:
            print("INFO: All startup settings applied successfully")
        else:
            print("WARNING: Some startup settings failed to apply")

        return success

    def save_current_settings(self) -> bool:
        """
        Save current settings to file

        Returns:
            bool: True if saved successfully
        """
        return self.settings.save()

    def reload_settings(self) -> bool:
        """
        Reload settings from file

        Returns:
            bool: True if reloaded successfully
        """
        return self.settings.load()

    def configure_velocity(self, x: Optional[float] = None,
                          y: Optional[float] = None,
                          z: Optional[float] = None,
                          save: bool = True) -> bool:
        """
        Configure velocity for one or more axes

        Args:
            x: X-axis velocity in mm/s (None to keep current)
            y: Y-axis velocity in mm/s (None to keep current)
            z: Z-axis velocity in mm/s (None to keep current)
            save: Save settings to file after updating

        Returns:
            bool: True if configuration successful
        """
        success = True

        if x is not None:
            self.settings.set_velocity('x_axis', x)
            accel = self.settings.get_acceleration('x_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.X_AXIS, x, accel)
                time.sleep(0.05)

        if y is not None:
            self.settings.set_velocity('y_axis', y)
            accel = self.settings.get_acceleration('y_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.Y_AXIS, y, accel)
                time.sleep(0.05)

        if z is not None:
            self.settings.set_velocity('z_axis', z)
            accel = self.settings.get_acceleration('z_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.Z_AXIS, z, accel)
                time.sleep(0.05)

        if save:
            self.settings.save()

        return success

    def configure_acceleration(self, x: Optional[float] = None,
                              y: Optional[float] = None,
                              z: Optional[float] = None,
                              save: bool = True) -> bool:
        """
        Configure acceleration for one or more axes

        Args:
            x: X-axis acceleration in mm/s² (None to keep current)
            y: Y-axis acceleration in mm/s² (None to keep current)
            z: Z-axis acceleration in mm/s² (None to keep current)
            save: Save settings to file after updating

        Returns:
            bool: True if configuration successful
        """
        success = True

        if x is not None:
            self.settings.set_acceleration('x_axis', x)
            vel = self.settings.get_velocity('x_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.X_AXIS, vel, x)
                time.sleep(0.05)

        if y is not None:
            self.settings.set_acceleration('y_axis', y)
            vel = self.settings.get_velocity('y_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.Y_AXIS, vel, y)
                time.sleep(0.05)

        if z is not None:
            self.settings.set_acceleration('z_axis', z)
            vel = self.settings.get_velocity('z_axis')
            if self.is_connected():
                success &= self._driver.set_velocity_params(self.Z_AXIS, vel, z)
                time.sleep(0.05)

        if save:
            self.settings.save()

        return success

    def configure_trigger(self, axis: str, mode: int,
                         polarity: int = 0x01,
                         start_pos_fwd: float = 0.0,
                         start_pos_rev: float = 0.0,
                         interval_fwd: float = 0.0,
                         interval_rev: float = 0.0,
                         save: bool = True) -> bool:
        """
        Configure trigger for specific axis

        Args:
            axis: Axis name ('X', 'Y', or 'Z')
            mode: Trigger mode (TriggerMode enum value)
            polarity: Trigger polarity (0x01 = active high, 0x02 = active low)
            start_pos_fwd: Start position for forward trigger (mm)
            start_pos_rev: Start position for reverse trigger (mm)
            interval_fwd: Interval for forward trigger (mm)
            interval_rev: Interval for reverse trigger (mm)
            save: Save settings to file after updating

        Returns:
            bool: True if configuration successful
        """
        axis = axis.upper()
        if axis not in ['X', 'Y', 'Z']:
            print(f"ERROR: Invalid axis: {axis}")
            return False

        axis_name = f"{axis.lower()}_axis"
        channel = {'X': self.X_AXIS, 'Y': self.Y_AXIS, 'Z': self.Z_AXIS}[axis]

        # Update settings
        self.settings.set_trigger_config(
            axis_name, mode, polarity,
            start_pos_fwd, start_pos_rev,
            interval_fwd, interval_rev
        )

        # Apply to hardware if connected
        success = True
        if self.is_connected():
            success = self._driver.set_trigger_mode(
                channel, mode, polarity,
                start_pos_fwd, start_pos_rev,
                interval_fwd, interval_rev
            )

        if save:
            self.settings.save()

        return success

    def get_detailed_status(self) -> Dict:
        """
        Get detailed status of all channels

        Returns:
            dict: Detailed status information
        """
        return {
            'connected': self.is_connected(),
            'scanning': self._scanning,
            'x_axis': self._driver.get_channel_status(self.X_AXIS),
            'y_axis': self._driver.get_channel_status(self.Y_AXIS),
            'z_axis': self._driver.get_channel_status(self.Z_AXIS),
            'position': self.get_position(),
            'settings': self.settings.get_all_settings()
        }
