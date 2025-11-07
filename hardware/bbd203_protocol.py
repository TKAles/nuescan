"""
ThorLabs BBD203 APT Protocol Handler
Binary message protocol for BBD203 motor controller

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import struct
from enum import IntEnum
from typing import Tuple, Optional, List


# Message IDs
class MessageID(IntEnum):
    """APT Protocol Message IDs for BBD203"""

    # Module Control
    MGMSG_MOD_IDENTIFY = 0x0223
    MGMSG_MOD_SET_CHANENABLESTATE = 0x0210
    MGMSG_MOD_REQ_CHANENABLESTATE = 0x0211
    MGMSG_MOD_GET_CHANENABLESTATE = 0x0212

    # Hardware Control
    MGMSG_HW_DISCONNECT = 0x0002
    MGMSG_HW_RESPONSE = 0x0080
    MGMSG_HW_RICHRESPONSE = 0x0081
    MGMSG_HW_START_UPDATEMSGS = 0x0011
    MGMSG_HW_STOP_UPDATEMSGS = 0x0012
    MGMSG_HW_REQ_INFO = 0x0005
    MGMSG_HW_GET_INFO = 0x0006

    # Motor Control - Basic
    MGMSG_MOT_SET_POSCOUNTER = 0x0410
    MGMSG_MOT_REQ_POSCOUNTER = 0x0411
    MGMSG_MOT_GET_POSCOUNTER = 0x0412
    MGMSG_MOT_SET_ENCCOUNTER = 0x0409
    MGMSG_MOT_REQ_ENCCOUNTER = 0x040A
    MGMSG_MOT_GET_ENCCOUNTER = 0x040B

    # Motor Control - Homing
    MGMSG_MOT_SET_HOMEPARAMS = 0x0440
    MGMSG_MOT_REQ_HOMEPARAMS = 0x0441
    MGMSG_MOT_GET_HOMEPARAMS = 0x0442
    MGMSG_MOT_MOVE_HOME = 0x0443
    MGMSG_MOT_MOVE_HOMED = 0x0444

    # Motor Control - Movement
    MGMSG_MOT_SET_MOVERELPARAMS = 0x0445
    MGMSG_MOT_REQ_MOVERELPARAMS = 0x0446
    MGMSG_MOT_GET_MOVERELPARAMS = 0x0447
    MGMSG_MOT_MOVE_RELATIVE = 0x0448
    MGMSG_MOT_SET_MOVEABSPARAMS = 0x0450
    MGMSG_MOT_REQ_MOVEABSPARAMS = 0x0451
    MGMSG_MOT_GET_MOVEABSPARAMS = 0x0452
    MGMSG_MOT_MOVE_ABSOLUTE = 0x0453
    MGMSG_MOT_MOVE_COMPLETED = 0x0464
    MGMSG_MOT_MOVE_VELOCITY = 0x0457
    MGMSG_MOT_MOVE_STOP = 0x0465
    MGMSG_MOT_MOVE_STOPPED = 0x0466

    # Motor Control - Velocity
    MGMSG_MOT_SET_VELPARAMS = 0x0413
    MGMSG_MOT_REQ_VELPARAMS = 0x0414
    MGMSG_MOT_GET_VELPARAMS = 0x0415

    # Motor Control - Status
    MGMSG_MOT_REQ_STATUSUPDATE = 0x0480
    MGMSG_MOT_GET_STATUSUPDATE = 0x0481
    MGMSG_MOT_REQ_STATUSBITS = 0x0429
    MGMSG_MOT_GET_STATUSBITS = 0x042A


# Destination addresses
class Destination(IntEnum):
    """BBD203 Destination addresses"""
    USB = 0x50
    ALL_CHANNELS = 0x11
    CHANNEL_1 = 0x21
    CHANNEL_2 = 0x22
    CHANNEL_3 = 0x23


# Source addresses
class Source(IntEnum):
    """Source addresses"""
    HOST = 0x01


# Status bits
class StatusBits(IntEnum):
    """Motor status bit definitions"""
    HOMING = 0x00000200
    HOMED = 0x00000400
    TRACKING = 0x00001000
    SETTLED = 0x00002000
    MOTION_ERROR = 0x00004000
    MOTOR_ENABLED = 0x80000000
    FORWARD_LIMIT = 0x00000001
    REVERSE_LIMIT = 0x00000002
    IN_MOTION_FORWARD = 0x00000010
    IN_MOTION_REVERSE = 0x00000020
    JOGGING_FORWARD = 0x00000040
    JOGGING_REVERSE = 0x00000080


class APTMessage:
    """
    APT Protocol Message Builder and Parser
    Handles construction and parsing of binary APT messages
    """

    @staticmethod
    def build_header_only(msg_id: int, param1: int, param2: int,
                          dest: int, source: int = Source.HOST) -> bytes:
        """
        Build a 6-byte header-only message

        Args:
            msg_id: Message ID (16-bit)
            param1: Parameter 1 (8-bit)
            param2: Parameter 2 (8-bit)
            dest: Destination address
            source: Source address (default: HOST)

        Returns:
            bytes: 6-byte message
        """
        return struct.pack('<HBBBB', msg_id, param1, param2, dest, source)

    @staticmethod
    def build_with_data(msg_id: int, dest: int, data: bytes,
                       source: int = Source.HOST) -> bytes:
        """
        Build a message with data packet

        Args:
            msg_id: Message ID (16-bit)
            dest: Destination address
            data: Data packet bytes
            source: Source address (default: HOST)

        Returns:
            bytes: Complete message (header + data)
        """
        data_len = len(data)
        header = struct.pack('<HHBB', msg_id, data_len, dest, source)
        return header + data

    @staticmethod
    def parse_header(data: bytes) -> Tuple[int, int, int, int, int]:
        """
        Parse message header

        Args:
            data: At least 6 bytes of message data

        Returns:
            tuple: (msg_id, data_len, dest, source, has_data)
        """
        if len(data) < 6:
            raise ValueError("Insufficient data for header")

        msg_id, byte2, byte3, dest, source = struct.unpack('<HBBBB', data[:6])

        # Determine if this is header-only or has data
        # Header-only messages use bytes 2-3 as parameters
        # Messages with data use bytes 2-3 as data length
        data_len = (byte3 << 8) | byte2

        return msg_id, data_len, dest, source

    @staticmethod
    def parse_position_counter(data: bytes) -> Tuple[int, int]:
        """Parse MGMSG_MOT_GET_POSCOUNTER response"""
        if len(data) < 12:
            raise ValueError("Insufficient data for position counter")

        _, channel, position = struct.unpack('<HHI', data[6:12])
        return channel, position

    @staticmethod
    def parse_encoder_counter(data: bytes) -> Tuple[int, int]:
        """Parse MGMSG_MOT_GET_ENCCOUNTER response"""
        if len(data) < 12:
            raise ValueError("Insufficient data for encoder counter")

        _, channel, encoder = struct.unpack('<HHI', data[6:12])
        return channel, encoder

    @staticmethod
    def parse_status_update(data: bytes) -> Tuple[int, int, int, int]:
        """
        Parse MGMSG_MOT_GET_STATUSUPDATE response

        Returns:
            tuple: (channel, position, enc_count, status_bits)
        """
        if len(data) < 20:
            raise ValueError("Insufficient data for status update")

        # Skip 6-byte header, parse data packet
        channel, position, enc_count, status = struct.unpack('<HIII', data[6:20])
        return channel, position, enc_count, status

    @staticmethod
    def parse_velocity_params(data: bytes) -> Tuple[int, int, int, int]:
        """
        Parse MGMSG_MOT_GET_VELPARAMS response

        Returns:
            tuple: (channel, min_vel, max_vel, accel)
        """
        if len(data) < 20:
            raise ValueError("Insufficient data for velocity params")

        channel, min_vel, max_vel, accel = struct.unpack('<HIII', data[6:20])
        return channel, min_vel, max_vel, accel

    @staticmethod
    def parse_channel_enable_state(data: bytes) -> Tuple[int, bool]:
        """Parse MGMSG_MOD_GET_CHANENABLESTATE response"""
        if len(data) < 6:
            raise ValueError("Insufficient data for channel enable state")

        # Header only message, params in bytes 2-3
        _, enable_state, channel, _, _ = struct.unpack('<HBBBB', data[:6])
        return channel, (enable_state == 0x01)


class APTProtocol:
    """
    High-level APT Protocol interface for BBD203
    Provides methods to build common command messages
    """

    # Scaling constants
    T_SAMPLE = 102.4e-6  # Controller sample time
    VELOCITY_SCALE = int(T_SAMPLE * 65536)
    ACCEL_SCALE = int((T_SAMPLE ** 2) * 65536)

    def __init__(self, encoder_counts_per_mm: int = 20000):
        """
        Initialize APT Protocol handler

        Args:
            encoder_counts_per_mm: Encoder resolution (default: 20000 for MLS203)
        """
        self.enc_cnt = encoder_counts_per_mm

    def position_to_apt(self, pos_mm: float) -> int:
        """Convert position in mm to APT units"""
        return int(pos_mm * self.enc_cnt)

    def apt_to_position(self, apt_units: int) -> float:
        """Convert APT units to position in mm"""
        return apt_units / self.enc_cnt

    def velocity_to_apt(self, vel_mm_s: float) -> int:
        """Convert velocity in mm/s to APT units"""
        return int(self.enc_cnt * self.T_SAMPLE * 65536 * vel_mm_s)

    def apt_to_velocity(self, apt_units: int) -> float:
        """Convert APT units to velocity in mm/s"""
        return apt_units / (self.enc_cnt * self.T_SAMPLE * 65536)

    def accel_to_apt(self, accel_mm_s2: float) -> int:
        """Convert acceleration in mm/s² to APT units"""
        return int(self.enc_cnt * (self.T_SAMPLE ** 2) * 65536 * accel_mm_s2)

    def apt_to_accel(self, apt_units: int) -> float:
        """Convert APT units to acceleration in mm/s²"""
        return apt_units / (self.enc_cnt * (self.T_SAMPLE ** 2) * 65536)

    # Command builders

    def cmd_identify(self, channel: int) -> bytes:
        """Build identify command (flash LEDs)"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOD_IDENTIFY, 0x00, 0x00, dest
        )

    def cmd_enable_channel(self, channel: int, enable: bool = True) -> bytes:
        """Build enable/disable channel command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        state = 0x01 if enable else 0x02
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOD_SET_CHANENABLESTATE, state, 0x01, dest
        )

    def cmd_req_channel_enable_state(self, channel: int) -> bytes:
        """Build request channel enable state command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOD_REQ_CHANENABLESTATE, 0x01, 0x00, dest
        )

    def cmd_start_update_msgs(self) -> bytes:
        """Build start automatic status updates command"""
        return APTMessage.build_header_only(
            MessageID.MGMSG_HW_START_UPDATEMSGS, 0x00, 0x00, Destination.ALL_CHANNELS
        )

    def cmd_stop_update_msgs(self) -> bytes:
        """Build stop automatic status updates command"""
        return APTMessage.build_header_only(
            MessageID.MGMSG_HW_STOP_UPDATEMSGS, 0x00, 0x00, Destination.ALL_CHANNELS
        )

    def cmd_req_hw_info(self) -> bytes:
        """Build request hardware info command"""
        return APTMessage.build_header_only(
            MessageID.MGMSG_HW_REQ_INFO, 0x00, 0x00, Destination.USB
        )

    def cmd_move_home(self, channel: int) -> bytes:
        """Build move home command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_MOVE_HOME, 0x01, 0x00, dest
        )

    def cmd_move_absolute(self, channel: int, position_mm: float) -> bytes:
        """Build move absolute command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        pos_apt = self.position_to_apt(position_mm)
        data = struct.pack('<HI', 0x0001, pos_apt)  # Channel 1 in data packet
        return APTMessage.build_with_data(
            MessageID.MGMSG_MOT_MOVE_ABSOLUTE, dest, data
        )

    def cmd_move_relative(self, channel: int, distance_mm: float) -> bytes:
        """Build move relative command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        dist_apt = self.position_to_apt(distance_mm)
        data = struct.pack('<Hi', 0x0001, dist_apt)  # Signed for direction
        return APTMessage.build_with_data(
            MessageID.MGMSG_MOT_MOVE_RELATIVE, dest, data
        )

    def cmd_move_stop(self, channel: int, immediate: bool = True) -> bytes:
        """Build stop motion command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        stop_mode = 0x01 if immediate else 0x02
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_MOVE_STOP, 0x01, stop_mode, dest
        )

    def cmd_set_velocity_params(self, channel: int, max_vel_mm_s: float,
                                accel_mm_s2: float) -> bytes:
        """Build set velocity parameters command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        max_vel_apt = self.velocity_to_apt(max_vel_mm_s)
        accel_apt = self.accel_to_apt(accel_mm_s2)

        data = struct.pack('<HIII',
            0x0001,      # Channel 1 in data packet
            0,           # Min velocity (0)
            max_vel_apt, # Max velocity
            accel_apt    # Acceleration
        )
        return APTMessage.build_with_data(
            MessageID.MGMSG_MOT_SET_VELPARAMS, dest, data
        )

    def cmd_req_velocity_params(self, channel: int) -> bytes:
        """Build request velocity parameters command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_REQ_VELPARAMS, 0x01, 0x00, dest
        )

    def cmd_req_position(self, channel: int) -> bytes:
        """Build request position counter command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_REQ_POSCOUNTER, 0x01, 0x00, dest
        )

    def cmd_req_encoder(self, channel: int) -> bytes:
        """Build request encoder counter command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_REQ_ENCCOUNTER, 0x01, 0x00, dest
        )

    def cmd_req_status_update(self, channel: int) -> bytes:
        """Build request status update command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_REQ_STATUSUPDATE, 0x01, 0x00, dest
        )

    def cmd_req_status_bits(self, channel: int) -> bytes:
        """Build request status bits command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        return APTMessage.build_header_only(
            MessageID.MGMSG_MOT_REQ_STATUSBITS, 0x01, 0x00, dest
        )

    def cmd_set_position_counter(self, channel: int, position_mm: float) -> bytes:
        """Build set position counter command"""
        dest = Destination.CHANNEL_1 + (channel - 1)
        pos_apt = self.position_to_apt(position_mm)
        data = struct.pack('<HI', 0x0001, pos_apt)
        return APTMessage.build_with_data(
            MessageID.MGMSG_MOT_SET_POSCOUNTER, dest, data
        )
