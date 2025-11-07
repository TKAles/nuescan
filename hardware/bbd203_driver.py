"""
ThorLabs BBD203 3-Channel Motor Controller Driver
Complete implementation of the APT protocol for BBD203

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import serial
import serial.tools.list_ports
import time
import threading
from typing import Dict, List, Optional, Callable, Tuple
from queue import Queue, Empty

from hardware.bbd203_protocol import (
    APTProtocol, APTMessage, MessageID, StatusBits, Destination
)


class BBD203Channel:
    """Represents a single channel on the BBD203"""

    def __init__(self, channel_num: int):
        """
        Initialize channel

        Args:
            channel_num: Channel number (1, 2, or 3)
        """
        self.channel_num = channel_num
        self.enabled = False
        self.homed = False
        self.position_mm = 0.0
        self.encoder_count = 0
        self.status_bits = 0
        self.moving = False
        self.homing = False
        self.error = False

    def update_from_status(self, position: int, encoder: int, status: int,
                          protocol: APTProtocol):
        """Update channel state from status update"""
        self.position_mm = protocol.apt_to_position(position)
        self.encoder_count = encoder
        self.status_bits = status

        # Parse status bits
        self.homed = bool(status & StatusBits.HOMED)
        self.homing = bool(status & StatusBits.HOMING)
        self.enabled = bool(status & StatusBits.MOTOR_ENABLED)
        self.error = bool(status & StatusBits.MOTION_ERROR)

        # Check if moving
        self.moving = bool(status & (
            StatusBits.IN_MOTION_FORWARD |
            StatusBits.IN_MOTION_REVERSE |
            StatusBits.JOGGING_FORWARD |
            StatusBits.JOGGING_REVERSE |
            StatusBits.HOMING
        ))

    def is_ready(self) -> bool:
        """Check if channel is ready for operation"""
        return self.enabled and self.homed and not self.error


class BBD203Driver:
    """
    Complete driver for ThorLabs BBD203 3-Channel Motor Controller

    Features:
    - 3 independent motor channels
    - Binary APT protocol communication
    - Automatic status updates
    - Thread-safe operation
    - Position and velocity control
    """

    def __init__(self, encoder_counts_per_mm: int = 20000, timeout: float = 1.0):
        """
        Initialize BBD203 driver

        Args:
            encoder_counts_per_mm: Encoder resolution (default: 20000 for MLS203)
            timeout: Serial communication timeout in seconds
        """
        self.protocol = APTProtocol(encoder_counts_per_mm)
        self.timeout = timeout

        # Serial connection
        self._serial: Optional[serial.Serial] = None
        self._port_name = ""
        self._connected = False

        # Channels
        self.channels = {
            1: BBD203Channel(1),
            2: BBD203Channel(2),
            3: BBD203Channel(3)
        }

        # Communication thread
        self._rx_thread: Optional[threading.Thread] = None
        self._stop_thread = threading.Event()
        self._rx_queue = Queue()

        # Callbacks for asynchronous events
        self._move_complete_callbacks: Dict[int, List[Callable]] = {1: [], 2: [], 3: []}
        self._home_complete_callbacks: Dict[int, List[Callable]] = {1: [], 2: [], 3: []}

        # Hardware info
        self._hw_info = {}

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

    @staticmethod
    def list_thorlabs_devices() -> List[Dict[str, str]]:
        """
        List all ThorLabs APT devices connected via USB

        Returns:
            list: List of dictionaries containing device information
                  Each dict has: 'serial', 'port', 'description', 'vid', 'pid'
        """
        thorlabs_devices = []
        ports = serial.tools.list_ports.comports()

        # ThorLabs devices typically use FTDI chips
        # Common VID/PID combinations:
        # - FTDI: VID=0x0403, various PIDs
        thorlabs_vids = [0x0403]  # FTDI vendor ID

        for port in ports:
            # Check if this is a ThorLabs device by VID
            if port.vid in thorlabs_vids:
                device_info = {
                    'serial': port.serial_number or 'Unknown',
                    'port': port.device,
                    'description': port.description or 'Unknown',
                    'manufacturer': port.manufacturer or 'Unknown',
                    'vid': f"0x{port.vid:04X}" if port.vid else 'Unknown',
                    'pid': f"0x{port.pid:04X}" if port.pid else 'Unknown'
                }
                thorlabs_devices.append(device_info)
                print(f"DEBUG: Found ThorLabs device - Serial: {device_info['serial']}, "
                      f"Port: {device_info['port']}")

        return thorlabs_devices

    @staticmethod
    def find_device_by_serial(serial_number: str) -> Optional[str]:
        """
        Find ThorLabs device by serial number and return its port

        Args:
            serial_number: Device serial number (e.g., '83123456')

        Returns:
            str: COM port name if found, None otherwise
        """
        devices = BBD203Driver.list_thorlabs_devices()

        for device in devices:
            if device['serial'] == serial_number:
                print(f"INFO: Found device {serial_number} on port {device['port']}")
                return device['port']

        print(f"WARNING: Device with serial number {serial_number} not found")
        print(f"Available devices: {[d['serial'] for d in devices]}")
        return None

    def connect_by_serial(self, serial_number: str, baudrate: int = 115200) -> bool:
        """
        Connect to BBD203 controller by serial number (auto-find port)

        This is the preferred connection method - automatically finds the
        device by serial number over USB, similar to Kinesis library.

        Args:
            serial_number: Device serial number (e.g., '83123456')
            baudrate: Baud rate (default: 115200)

        Returns:
            bool: True if connection successful

        Example:
            driver.connect_by_serial('83123456')
        """
        # Find device port by serial number
        port = self.find_device_by_serial(serial_number)

        if port is None:
            print(f"ERROR: Could not find BBD203 with serial number {serial_number}")
            print("Available ThorLabs devices:")
            for device in self.list_thorlabs_devices():
                print(f"  Serial: {device['serial']}, Port: {device['port']}, "
                      f"Description: {device['description']}")
            return False

        # Connect using the found port
        return self.connect(port, baudrate)

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """
        Connect to BBD203 controller by port name

        Note: It's recommended to use connect_by_serial() instead, which
        automatically finds the device by serial number.

        Args:
            port: Serial port name (e.g., 'COM3' or '/dev/ttyUSB0')
            baudrate: Baud rate (default: 115200)

        Returns:
            bool: True if connection successful
        """
        try:
            print(f"INFO: Connecting to BBD203 on {port}")

            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )

            self._port_name = port
            self._connected = True

            # Start receive thread
            self._stop_thread.clear()
            self._rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._rx_thread.start()

            # Initialize controller
            time.sleep(0.1)  # Allow thread to start

            # Request hardware info
            self._send_command(self.protocol.cmd_req_hw_info())
            time.sleep(0.1)

            # Start automatic status updates
            self._send_command(self.protocol.cmd_start_update_msgs())
            time.sleep(0.1)

            print(f"INFO: Successfully connected to BBD203 on {port}")
            return True

        except serial.SerialException as e:
            print(f"ERROR: Failed to connect to {port}: {e}")
            self._connected = False
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from BBD203 controller

        Returns:
            bool: True if disconnection successful
        """
        if not self._connected:
            return True

        try:
            print("INFO: Disconnecting from BBD203")

            # Stop status updates
            self._send_command(self.protocol.cmd_stop_update_msgs())
            time.sleep(0.1)

            # Stop receive thread
            self._stop_thread.set()
            if self._rx_thread:
                self._rx_thread.join(timeout=2.0)

            # Close serial port
            if self._serial and self._serial.is_open:
                self._serial.close()

            self._connected = False
            print("INFO: Disconnected from BBD203")
            return True

        except Exception as e:
            print(f"ERROR: Error during disconnect: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if controller is connected"""
        return self._connected and self._serial and self._serial.is_open

    # ==================== Communication Methods ====================

    def _send_command(self, cmd: bytes) -> bool:
        """
        Send command to controller

        Args:
            cmd: Command bytes to send

        Returns:
            bool: True if send successful
        """
        if not self.is_connected():
            print("ERROR: Cannot send command - not connected")
            return False

        try:
            self._serial.write(cmd)
            return True
        except serial.SerialException as e:
            print(f"ERROR: Failed to send command: {e}")
            return False

    def _receive_loop(self):
        """Background thread to receive messages from controller"""
        buffer = bytearray()

        while not self._stop_thread.is_set():
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    buffer.extend(data)

                    # Process complete messages
                    while len(buffer) >= 6:
                        # Parse header
                        msg_id, data_len, dest, source = APTMessage.parse_header(buffer)

                        # Determine total message length
                        if data_len == 0 or data_len > 255:
                            # Header-only message
                            msg_len = 6
                        else:
                            # Message with data
                            msg_len = 6 + data_len

                        # Wait for complete message
                        if len(buffer) < msg_len:
                            break

                        # Extract message
                        msg = bytes(buffer[:msg_len])
                        buffer = buffer[msg_len:]

                        # Process message
                        self._process_message(msg_id, msg)

                else:
                    time.sleep(0.001)  # Small delay to prevent busy waiting

            except Exception as e:
                if not self._stop_thread.is_set():
                    print(f"ERROR: Exception in receive loop: {e}")
                time.sleep(0.1)

    def _process_message(self, msg_id: int, msg: bytes):
        """
        Process received message

        Args:
            msg_id: Message ID
            msg: Complete message bytes
        """
        try:
            if msg_id == MessageID.MGMSG_MOT_GET_STATUSUPDATE:
                # Status update
                channel, position, encoder, status = APTMessage.parse_status_update(msg)
                # Determine which channel this is for (from destination byte)
                dest = msg[4]
                channel_num = dest - 0x20  # 0x21->1, 0x22->2, 0x23->3

                if channel_num in self.channels:
                    self.channels[channel_num].update_from_status(
                        position, encoder, status, self.protocol
                    )

            elif msg_id == MessageID.MGMSG_MOT_MOVE_COMPLETED:
                # Move completed
                dest = msg[4]
                channel_num = dest - 0x20

                if channel_num in self.channels:
                    self.channels[channel_num].moving = False

                    # Call callbacks
                    for callback in self._move_complete_callbacks.get(channel_num, []):
                        callback(channel_num)

            elif msg_id == MessageID.MGMSG_MOT_MOVE_HOMED:
                # Homing completed
                dest = msg[4]
                channel_num = dest - 0x20

                if channel_num in self.channels:
                    self.channels[channel_num].homed = True
                    self.channels[channel_num].homing = False

                    # Call callbacks
                    for callback in self._home_complete_callbacks.get(channel_num, []):
                        callback(channel_num)

            elif msg_id == MessageID.MGMSG_MOT_MOVE_STOPPED:
                # Motion stopped
                dest = msg[4]
                channel_num = dest - 0x20

                if channel_num in self.channels:
                    self.channels[channel_num].moving = False

            elif msg_id == MessageID.MGMSG_MOD_GET_CHANENABLESTATE:
                # Channel enable state
                channel, enabled = APTMessage.parse_channel_enable_state(msg)
                dest = msg[4]
                channel_num = dest - 0x20

                if channel_num in self.channels:
                    self.channels[channel_num].enabled = enabled

            elif msg_id == MessageID.MGMSG_HW_RESPONSE:
                # Hardware response (error or acknowledgement)
                print(f"DEBUG: Received HW_RESPONSE: {msg.hex()}")

            elif msg_id == MessageID.MGMSG_HW_GET_INFO:
                # Hardware info
                print(f"DEBUG: Received hardware info")

        except Exception as e:
            print(f"ERROR: Failed to process message {msg_id:04X}: {e}")

    def _set_and_verify_enable(self, channel: int, enable: bool, retries: int = 3) -> bool:
        """
        Set channel enable state and verify it was set correctly

        Args:
            channel: Channel number (1, 2, or 3)
            enable: True to enable, False to disable
            retries: Number of retry attempts

        Returns:
            bool: True if value was set and verified
        """
        for attempt in range(retries):
            # Send enable command
            cmd = self.protocol.cmd_enable_channel(channel, enable)
            if not self._send_command(cmd):
                continue

            time.sleep(0.1)  # Wait for controller to process

            # Request status update to verify
            self.request_status_update(channel)
            time.sleep(0.1)  # Wait for status response

            # Check if state matches expected
            if self.channels[channel].enabled == enable:
                return True

            if attempt < retries - 1:
                print(f"DEBUG: Enable verification failed for channel {channel}, "
                      f"retrying ({attempt + 1}/{retries})")
                time.sleep(0.1)

        print(f"ERROR: Failed to set and verify enable state for channel {channel} "
              f"after {retries} attempts")
        return False

    # ==================== Channel Control ====================

    def enable_channel(self, channel: int, enable: bool = True) -> bool:
        """
        Enable or disable a motor channel

        Args:
            channel: Channel number (1, 2, or 3)
            enable: True to enable, False to disable

        Returns:
            bool: True if command sent successfully
        """
        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        action = "Enabling" if enable else "Disabling"
        print(f"DEBUG: {action} channel {channel}")

        # Use set and verify to ensure command was processed
        return self._set_and_verify_enable(channel, enable)

    def identify(self, channel: int) -> bool:
        """
        Flash front panel LEDs to identify controller

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            bool: True if command sent successfully
        """
        print(f"DEBUG: Identifying channel {channel}")
        cmd = self.protocol.cmd_identify(channel)
        return self._send_command(cmd)

    # ==================== Homing ====================

    def home_channel(self, channel: int, wait: bool = False, timeout: float = 30.0) -> bool:
        """
        Home a motor channel

        Args:
            channel: Channel number (1, 2, or 3)
            wait: If True, block until homing complete
            timeout: Timeout in seconds if waiting

        Returns:
            bool: True if homing initiated (or completed if wait=True)
        """
        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        print(f"DEBUG: Homing channel {channel}")

        self.channels[channel].homing = True
        self.channels[channel].homed = False

        cmd = self.protocol.cmd_move_home(channel)
        if not self._send_command(cmd):
            return False

        if wait:
            # Wait for homing to complete
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.channels[channel].homed and not self.channels[channel].homing:
                    print(f"INFO: Channel {channel} homing completed")
                    return True
                time.sleep(0.1)

            print(f"ERROR: Homing timeout for channel {channel}")
            return False

        return True

    def home_all_channels(self, wait: bool = False, timeout: float = 30.0) -> bool:
        """
        Home all enabled channels

        Args:
            wait: If True, block until all homing complete
            timeout: Timeout in seconds if waiting

        Returns:
            bool: True if all homing operations successful
        """
        success = True
        for channel in [1, 2, 3]:
            if self.channels[channel].enabled:
                if not self.home_channel(channel, wait=False):
                    success = False

        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout:
                all_homed = all(
                    ch.homed for ch in self.channels.values() if ch.enabled
                )
                if all_homed:
                    print("INFO: All channels homed successfully")
                    return True
                time.sleep(0.1)

            print("ERROR: Timeout waiting for all channels to home")
            return False

        return success

    # ==================== Motion Control ====================

    def move_absolute(self, channel: int, position_mm: float,
                     wait: bool = False, timeout: float = 30.0) -> bool:
        """
        Move to absolute position

        Args:
            channel: Channel number (1, 2, or 3)
            position_mm: Target position in mm
            wait: If True, block until move complete
            timeout: Timeout in seconds if waiting

        Returns:
            bool: True if move initiated (or completed if wait=True)
        """
        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        if not self.channels[channel].is_ready():
            print(f"ERROR: Channel {channel} not ready for movement")
            return False

        print(f"DEBUG: Moving channel {channel} to {position_mm} mm")

        self.channels[channel].moving = True

        cmd = self.protocol.cmd_move_absolute(channel, position_mm)
        if not self._send_command(cmd):
            return False

        if wait:
            # Wait for move to complete
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.channels[channel].moving:
                    print(f"INFO: Channel {channel} move completed")
                    return True
                time.sleep(0.01)

            print(f"ERROR: Move timeout for channel {channel}")
            return False

        return True

    def move_relative(self, channel: int, distance_mm: float,
                     wait: bool = False, timeout: float = 30.0) -> bool:
        """
        Move relative distance

        Args:
            channel: Channel number (1, 2, or 3)
            distance_mm: Distance to move in mm (positive or negative)
            wait: If True, block until move complete
            timeout: Timeout in seconds if waiting

        Returns:
            bool: True if move initiated (or completed if wait=True)
        """
        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        if not self.channels[channel].is_ready():
            print(f"ERROR: Channel {channel} not ready for movement")
            return False

        print(f"DEBUG: Moving channel {channel} by {distance_mm} mm")

        self.channels[channel].moving = True

        cmd = self.protocol.cmd_move_relative(channel, distance_mm)
        if not self._send_command(cmd):
            return False

        if wait:
            # Wait for move to complete
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.channels[channel].moving:
                    print(f"INFO: Channel {channel} move completed")
                    return True
                time.sleep(0.01)

            print(f"ERROR: Move timeout for channel {channel}")
            return False

        return True

    def stop(self, channel: int, immediate: bool = True) -> bool:
        """
        Stop motion

        Args:
            channel: Channel number (1, 2, or 3), or 0 for all channels
            immediate: If True, stop immediately; if False, decelerate

        Returns:
            bool: True if stop command sent successfully
        """
        if channel == 0:
            # Stop all channels
            success = True
            for ch in [1, 2, 3]:
                if not self.stop(ch, immediate):
                    success = False
            return success

        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        print(f"DEBUG: Stopping channel {channel}")

        cmd = self.protocol.cmd_move_stop(channel, immediate)
        return self._send_command(cmd)

    # ==================== Parameter Setting ====================

    def set_velocity_params(self, channel: int, max_vel_mm_s: float,
                           accel_mm_s2: float) -> bool:
        """
        Set velocity and acceleration parameters

        Args:
            channel: Channel number (1, 2, or 3)
            max_vel_mm_s: Maximum velocity in mm/s
            accel_mm_s2: Acceleration in mm/s²

        Returns:
            bool: True if parameters set successfully
        """
        if channel not in [1, 2, 3]:
            print(f"ERROR: Invalid channel number: {channel}")
            return False

        print(f"DEBUG: Setting velocity params for channel {channel}: "
              f"vel={max_vel_mm_s} mm/s, accel={accel_mm_s2} mm/s²")

        cmd = self.protocol.cmd_set_velocity_params(channel, max_vel_mm_s, accel_mm_s2)
        if self._send_command(cmd):
            time.sleep(0.1)  # Wait for controller to process

            # Request status update to confirm parameters were accepted
            self.request_status_update(channel)
            time.sleep(0.1)  # Wait for status response
            return True
        return False

    # ==================== Status and Position ====================

    def get_position(self, channel: int) -> Optional[float]:
        """
        Get current position of channel

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            float: Current position in mm, or None if unavailable
        """
        if channel not in [1, 2, 3]:
            return None

        return self.channels[channel].position_mm

    def get_channel_status(self, channel: int) -> Optional[Dict]:
        """
        Get detailed status of channel

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            dict: Channel status dictionary
        """
        if channel not in [1, 2, 3]:
            return None

        ch = self.channels[channel]
        return {
            'channel': channel,
            'enabled': ch.enabled,
            'homed': ch.homed,
            'homing': ch.homing,
            'moving': ch.moving,
            'error': ch.error,
            'ready': ch.is_ready(),
            'position_mm': ch.position_mm,
            'encoder_count': ch.encoder_count,
            'status_bits': ch.status_bits
        }

    def request_status_update(self, channel: int) -> bool:
        """
        Request immediate status update for channel

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            bool: True if request sent successfully
        """
        if channel not in [1, 2, 3]:
            return False

        cmd = self.protocol.cmd_req_status_update(channel)
        return self._send_command(cmd)

    # ==================== Callbacks ====================

    def register_move_complete_callback(self, channel: int, callback: Callable):
        """Register callback for move complete event"""
        if channel in [1, 2, 3]:
            self._move_complete_callbacks[channel].append(callback)

    def register_home_complete_callback(self, channel: int, callback: Callable):
        """Register callback for home complete event"""
        if channel in [1, 2, 3]:
            self._home_complete_callbacks[channel].append(callback)
