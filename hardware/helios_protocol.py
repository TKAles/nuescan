"""
Helios Laser Protocol Handler
ASCII-based RS-232 communication protocol for Helios laser systems

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

from enum import IntEnum
from typing import Union, Optional


class PulseMode(IntEnum):
    """Helios pulse mode settings"""
    SINGLE_PULSE = 1
    GATING = 4
    CONTINUOUS_PULSING = 14


class HeliosCommand:
    """
    Helios laser command constants and builders

    All commands are ASCII strings terminated with carriage return <CR>
    Format: COMMAND value<CR> for setting
            COMMAND<CR> for querying
    """

    # Command constants
    LDO = "LDO"  # Laser enabled (0/1)
    LDG = "LDG"  # Pulse mode (1/4/14)
    LDF = "LDF"  # Period between pulses (ns)
    LRE = "LRE"  # Laser remote enable (0/1) - Single electronic only
    LDS = "LDS"  # Laser diode pulse current (mA)
    LTA = "LTA"  # Actual pump diode temperature (m°C)
    LMA = "LMA"  # Actual resonator/SHG temperature (mA)
    EOA = "EOA"  # Actual q-switch temperature (m°C)
    ELT = "ELT"  # Pump diode temp control deviation (m°C)
    ELM = "ELM"  # Resonator/SHG temp control deviation (m°C)
    EEO = "EEO"  # Q-switch temp control deviation (m°C)
    LTT = "LTT"  # Controller power stage temperature (m°C)
    LER = "LER"  # Status register (read)
    LCE = "LCE"  # Clear status register
    CCE = "CCE"  # Clear controller errors
    CSR = "CSR"  # Controller serial number
    HSR = "HSR"  # Laser head serial number
    HTR = "HTR"  # Laser diode operation time (hours)
    HPR = "HPR"  # Restore factory settings
    HMP = "HMP"  # Laser power monitor (mW)

    @staticmethod
    def build_command(command: str, value: Optional[Union[int, float]] = None) -> bytes:
        """
        Build a Helios command string

        Args:
            command: Command string (e.g., "LDO", "LDF")
            value: Optional value to set (None for query)

        Returns:
            bytes: Command ready to send over serial

        Example:
            build_command("LDO", 1) -> b"LDO 1\r"
            build_command("LDO") -> b"LDO\r"
        """
        if value is not None:
            cmd_str = f"{command} {value}\r"
        else:
            cmd_str = f"{command}\r"
        return cmd_str.encode('ascii')

    @staticmethod
    def parse_response(response: bytes) -> str:
        """
        Parse response from Helios laser

        Args:
            response: Raw bytes from serial port

        Returns:
            str: Parsed response string (stripped of CR/LF)
        """
        return response.decode('ascii').strip()


class HeliosStatus:
    """
    Helios status register decoder

    Status is sum of multiple bit flags:
    Example: 1*2^0 + 0*2^1 + 1*2^2 = 5
    """

    # Status bit definitions (from LER/LCE/CCE commands)
    # These are example flags - actual flags depend on controller model
    # Refer to "Troubleshooting" section in manual for complete list

    def __init__(self, status_value: int):
        """
        Initialize status decoder

        Args:
            status_value: Numeric status value from controller
        """
        self.value = status_value
        self.flags = self._decode_flags(status_value)

    def _decode_flags(self, value: int) -> list:
        """Decode status value into list of active bit positions"""
        flags = []
        bit_pos = 0
        while value > 0:
            if value & 1:
                flags.append(bit_pos)
            value >>= 1
            bit_pos += 1
        return flags

    def has_errors(self) -> bool:
        """Check if any error flags are set"""
        return self.value > 0

    def __str__(self) -> str:
        return f"Status: {self.value} (flags: {self.flags})"


class HeliosProtocol:
    """
    High-level Helios protocol handler
    Provides parameter validation and unit conversions
    """

    # Parameter ranges (from protocol document)
    RANGE_LDO = (0, 1)
    RANGE_LDG = (0, 14)
    RANGE_LDF = (8000, 60000)  # ns
    RANGE_LRE = (0, 1)
    RANGE_LDS = (0, 7000)  # mA
    RANGE_LTA = (5000, 50000)  # m°C
    RANGE_LMA = (0, 4000)  # mA (seems like error in doc, should be m°C)
    RANGE_EOA = (5000, 50000)  # m°C
    RANGE_ELT = (-32768, 32767)  # m°C
    RANGE_ELM = (-32768, 32767)  # m°C
    RANGE_EEO = (-32768, 32767)  # m°C
    RANGE_LTT = (5000, 65535)  # m°C
    RANGE_HTR = (0, 65535)  # hours
    RANGE_HMP = (0, 5000)  # mW

    def __init__(self):
        """Initialize protocol handler"""
        pass

    # Temperature conversions (m°C <-> °C)

    @staticmethod
    def celsius_to_millicelsius(temp_c: float) -> int:
        """Convert temperature from °C to m°C (milli-Celsius)"""
        return int(temp_c * 1000)

    @staticmethod
    def millicelsius_to_celsius(temp_mc: int) -> float:
        """Convert temperature from m°C to °C"""
        return temp_mc / 1000.0

    # Frequency conversions (Hz <-> ns period)

    @staticmethod
    def frequency_to_period_ns(freq_hz: float) -> int:
        """
        Convert frequency in Hz to period in nanoseconds

        Args:
            freq_hz: Frequency in Hz

        Returns:
            int: Period in nanoseconds

        Example:
            50000 Hz -> 20000 ns (50 kHz)
        """
        if freq_hz <= 0:
            raise ValueError("Frequency must be positive")
        period_ns = int(1e9 / freq_hz)
        return period_ns

    @staticmethod
    def period_ns_to_frequency(period_ns: int) -> float:
        """
        Convert period in nanoseconds to frequency in Hz

        Args:
            period_ns: Period in nanoseconds

        Returns:
            float: Frequency in Hz
        """
        if period_ns <= 0:
            raise ValueError("Period must be positive")
        freq_hz = 1e9 / period_ns
        return freq_hz

    # Command builders with validation

    def cmd_set_laser_enable(self, enabled: bool) -> bytes:
        """Build command to enable/disable laser"""
        value = 1 if enabled else 0
        return HeliosCommand.build_command(HeliosCommand.LDO, value)

    def cmd_query_laser_enable(self) -> bytes:
        """Build query for laser enable state"""
        return HeliosCommand.build_command(HeliosCommand.LDO)

    def cmd_set_pulse_mode(self, mode: PulseMode) -> bytes:
        """Build command to set pulse mode"""
        if mode not in [PulseMode.SINGLE_PULSE, PulseMode.GATING,
                       PulseMode.CONTINUOUS_PULSING]:
            raise ValueError(f"Invalid pulse mode: {mode}")
        return HeliosCommand.build_command(HeliosCommand.LDG, mode)

    def cmd_query_pulse_mode(self) -> bytes:
        """Build query for pulse mode"""
        return HeliosCommand.build_command(HeliosCommand.LDG)

    def cmd_set_frequency_hz(self, freq_hz: float) -> bytes:
        """
        Build command to set laser frequency (Hz)
        Converts to period in ns internally
        """
        period_ns = self.frequency_to_period_ns(freq_hz)
        if not (self.RANGE_LDF[0] <= period_ns <= self.RANGE_LDF[1]):
            raise ValueError(f"Frequency results in period {period_ns}ns, "
                           f"valid range: {self.RANGE_LDF[0]}-{self.RANGE_LDF[1]}ns")
        return HeliosCommand.build_command(HeliosCommand.LDF, period_ns)

    def cmd_query_frequency(self) -> bytes:
        """Build query for laser frequency (returns period in ns)"""
        return HeliosCommand.build_command(HeliosCommand.LDF)

    def cmd_set_current_ma(self, current_ma: float) -> bytes:
        """Build command to set laser diode current (mA)"""
        if not (self.RANGE_LDS[0] <= current_ma <= self.RANGE_LDS[1]):
            raise ValueError(f"Current {current_ma}mA outside valid range: "
                           f"{self.RANGE_LDS[0]}-{self.RANGE_LDS[1]}mA")
        return HeliosCommand.build_command(HeliosCommand.LDS, int(current_ma))

    def cmd_query_current(self) -> bytes:
        """Build query for laser diode current"""
        return HeliosCommand.build_command(HeliosCommand.LDS)

    def cmd_query_pump_temp(self) -> bytes:
        """Build query for actual pump diode temperature"""
        return HeliosCommand.build_command(HeliosCommand.LTA)

    def cmd_query_resonator_temp(self) -> bytes:
        """Build query for actual resonator/SHG temperature"""
        return HeliosCommand.build_command(HeliosCommand.LMA)

    def cmd_query_qswitch_temp(self) -> bytes:
        """Build query for actual q-switch temperature"""
        return HeliosCommand.build_command(HeliosCommand.EOA)

    def cmd_query_power_stage_temp(self) -> bytes:
        """Build query for controller power stage temperature"""
        return HeliosCommand.build_command(HeliosCommand.LTT)

    def cmd_query_status(self) -> bytes:
        """Build query for status register"""
        return HeliosCommand.build_command(HeliosCommand.LER)

    def cmd_clear_status(self) -> bytes:
        """Build command to clear status register"""
        return HeliosCommand.build_command(HeliosCommand.LCE, 0)

    def cmd_clear_errors(self) -> bytes:
        """Build command to clear controller errors"""
        return HeliosCommand.build_command(HeliosCommand.CCE, 0)

    def cmd_query_controller_serial(self) -> bytes:
        """Build query for controller serial number"""
        return HeliosCommand.build_command(HeliosCommand.CSR)

    def cmd_query_head_serial(self) -> bytes:
        """Build query for laser head serial number"""
        return HeliosCommand.build_command(HeliosCommand.HSR)

    def cmd_query_operation_time(self) -> bytes:
        """Build query for laser diode operation time (hours)"""
        return HeliosCommand.build_command(HeliosCommand.HTR)

    def cmd_query_power_monitor(self) -> bytes:
        """Build query for laser power monitor (mW)"""
        return HeliosCommand.build_command(HeliosCommand.HMP)

    def cmd_restore_factory(self) -> bytes:
        """
        Build command to restore factory settings

        WARNING: Laser must be disabled (LDO 0) before this command
        After sending, wait 2 seconds before rebooting/power cycling
        """
        return HeliosCommand.build_command(HeliosCommand.HPR)
