# Helios Laser System Driver

## Overview

This directory contains a complete implementation of the Helios laser system driver. The driver implements the full RS-232 ASCII communications protocol as specified in the helios_comms_protocol.pdf document.

The Helios laser system is a pulsed solid-state laser with:
- Diode-pumped Nd:YAG/Nd:YLF laser head
- Q-switched operation
- Frequency control (16.7 kHz - 125 kHz)
- Current control (0-7000 mA)
- Power monitoring
- Temperature monitoring (4 sensors)
- External trigger capability

## Architecture

The Helios driver is split into three layers:

### 1. Protocol Layer (`helios_protocol.py`)

Low-level protocol implementation that handles:
- ASCII command construction
- Response parsing and validation
- Unit conversions (Hz ↔ ns, °C ↔ m°C)
- Parameter range validation
- Status register decoding

**Key Classes:**
- `HeliosCommand`: Command constants and builders
- `HeliosProtocol`: High-level protocol interface with validation

### 2. Driver Layer (`helios_driver.py`)

Complete driver implementation providing:
- RS-232 serial communication (9600 baud, 8N1)
- Thread-safe command/query operations
- Comprehensive status monitoring
- Temperature monitoring (pump, resonator, q-switch, power stage)
- Power monitoring
- Laser enable/disable control
- Pulse mode control (single, gating, continuous)
- Frequency and current control

**Key Classes:**
- `PulseMode`: Enumeration of pulse modes
- `HeliosStatus`: Status data structure
- `HeliosDriver`: Main driver class for laser communication

### 3. Integration Layer (`hardware/microscope.py`)

Application-specific integration that:
- Combines Helios with Genesis microscope systems
- Provides unified status monitoring
- Integrates with nueScan application
- Implements safety interlocks
- Provides emergency stop functionality

## Features

### Communication
- ASCII-based RS-232 protocol
- Baud rate: 9600, 8 data bits, no parity, 1 stop bit
- Commands terminated with carriage return (CR)
- Thread-safe operation with mutex locking
- Configurable timeout (default: 1 second)

### Laser Control
- Laser enable/disable
- Three pulse modes:
  - Single pulse (one pulse per trigger)
  - Continuous gating (pulse train while triggered)
  - Continuous pulsing (free-running)
- Frequency control (16.7 kHz to 125 kHz)
- Diode current control (0-7000 mA)

### Monitoring
- Real-time power measurement (mW)
- Four temperature sensors:
  - Pump diode temperature
  - Resonator temperature
  - Q-switch temperature
  - Power stage temperature
- Operation hours counter
- Comprehensive status register
- Error detection

### Safety
- Temperature monitoring with warnings
- Error status detection
- Laser enable/disable control
- Emergency stop capability
- Integration with system interlocks

## Usage

### Connection Methods

The driver supports connection to a specific COM port:

```python
from hardware.helios_driver import HeliosDriver

# Create driver instance
driver = HeliosDriver(timeout=1.0)

# List available COM ports
ports = HeliosDriver.list_available_ports()
for port in ports:
    print(f"Available port: {port}")

# Connect to specific port
driver.connect('COM5')  # or '/dev/ttyUSB0' on Linux

# Get device information
print(f"Controller S/N: {driver.get_controller_serial()}")
print(f"Head S/N: {driver.get_head_serial()}")
```

### Basic Laser Control

```python
# Set frequency (in Hz)
driver.set_frequency_hz(10000)  # 10 kHz

# Set diode current (in mA)
driver.set_current_ma(500)  # 500 mA

# Set pulse mode
from hardware.helios_driver import PulseMode
driver.set_pulse_mode(PulseMode.CONTINUOUS_PULSING)

# Enable laser
driver.set_laser_enable(True)

# Check if laser is enabled
if driver.is_laser_enabled():
    print("Laser is ON")

# Disable laser
driver.set_laser_enable(False)

# Disconnect
driver.disconnect()
```

### Monitoring

```python
# Get current power
power_mw = driver.get_power_mw()
print(f"Output power: {power_mw} mW")

# Get temperatures (in Celsius)
temps = driver.get_all_temperatures()
print(f"Pump: {temps['pump_temp_c']:.1f}°C")
print(f"Resonator: {temps['resonator_temp_c']:.1f}°C")
print(f"Q-switch: {temps['qswitch_temp_c']:.1f}°C")
print(f"Power stage: {temps['power_stage_temp_c']:.1f}°C")

# Get operation hours
hours = driver.get_operation_hours()
print(f"Operation time: {hours} hours")

# Get comprehensive status
status = driver.get_status()
print(f"Connected: {status['connected']}")
print(f"Laser enabled: {status['laser_enabled']}")
print(f"Frequency: {status['frequency_hz']} Hz")
print(f"Current: {status['current_ma']} mA")
print(f"Power: {status['power_mw']} mW")
print(f"Has errors: {status['has_errors']}")
```

### Status Updates

```python
# Manually update status from hardware
driver.update_status()

# Status is automatically updated on each get_status() call
status = driver.get_status()

# Access cached values without querying hardware
freq = driver.get_frequency_hz()  # Returns last read value
current = driver.get_current_ma()  # Returns last read value
```

### Using Through Microscope Controller

The Helios driver is integrated into the application through the `MicroscopeController`:

```python
from hardware.microscope import MicroscopeController

# Create controller
microscope = MicroscopeController()

# Connect Helios
microscope.connect_helios('COM5')

# Apply settings from dialog
settings = {
    'com_port': 'COM5',
    'frequency_hz': 10000,
    'current_ma': 500
}
microscope.apply_helios_settings(settings)

# Enable laser
microscope.helios_enable_laser(True)

# Get status
status = microscope.get_helios_status()
print(f"Helios ready: {status['ready']}")
print(f"Power: {status['power_mw']} mW")

# Disable laser
microscope.helios_enable_laser(False)

# Disconnect
microscope.disconnect_helios()
```

## Configuration

### Frequency Control

The Helios laser operates by setting the pulse period in nanoseconds. The driver automatically converts between frequency (Hz) and period (ns):

```python
# Set frequency in Hz (driver converts to period in ns)
driver.set_frequency_hz(10000)  # 10 kHz → 100,000 ns period

# Valid frequency range: 16.7 kHz to 125 kHz
# Valid period range: 8000 ns to 60000 ns
```

Conversion formulas:
```
Period (ns) = 1,000,000,000 / Frequency (Hz)
Frequency (Hz) = 1,000,000,000 / Period (ns)
```

### Current Control

The diode current controls the laser output power:

```python
# Set current in milliamps
driver.set_current_ma(500)  # 500 mA

# Valid range: 0 to 7000 mA
```

**Important:** Higher currents produce more power but also more heat. Monitor temperatures when operating at high current.

### Pulse Modes

Three pulse modes are available:

```python
from hardware.helios_driver import PulseMode

# Single pulse mode (one pulse per trigger)
driver.set_pulse_mode(PulseMode.SINGLE_PULSE)

# Continuous gating mode (pulse train while triggered)
driver.set_pulse_mode(PulseMode.CONTINUOUS_GATING)

# Continuous pulsing mode (free-running)
driver.set_pulse_mode(PulseMode.CONTINUOUS_PULSING)
```

**Mode Descriptions:**
- **Single Pulse (LDG=0)**: One pulse generated per external trigger
- **Continuous Gating (LDG=1)**: Pulse train while external trigger is high
- **Continuous Pulsing (LDG=2)**: Free-running at set frequency (default)

### Temperature Monitoring

The driver monitors four temperature sensors:

```python
# Individual temperatures
pump_temp = driver.query_pump_temp_c()
resonator_temp = driver.query_resonator_temp_c()
qswitch_temp = driver.query_qswitch_temp_c()
power_stage_temp = driver.query_power_stage_temp_c()

# All temperatures at once
temps = driver.get_all_temperatures()
```

**Temperature Ranges:**
- Normal operation: < 50°C
- Warning threshold: > 60°C
- Critical threshold: > 70°C

## Integration with nueScan

The Helios driver is integrated into nueScan through the settings dialog and microscope controller.

### Configuration in UI

1. **Open Helios Settings**
   - Click "Helios Device Settings" button in main window

2. **Configure Parameters**
   - **COM Port**: Select from dropdown (automatically populated)
   - **Frequency**: Enter in Hz (16,666 - 125,000 Hz)
   - **Current**: Enter in mA (0 - 7000 mA)

3. **Apply Settings**
   - Click OK to apply and connect
   - Settings are validated before sending to hardware

### Settings Dialog Integration

The `HeliosDialog` class provides:
- Automatic COM port enumeration
- Input validation with range checking
- User-friendly error messages
- Settings persistence

```python
# Dialog usage (called from main window)
from dialogs.helios_dialog import HeliosDialog

dialog = HeliosDialog(parent=self)
if dialog.exec() == QDialog.DialogCode.Accepted:
    settings = dialog.get_settings()  # Returns None if validation fails
    if settings:
        self.microscope.apply_helios_settings(settings)
```

### Validation Rules

The dialog validates all inputs before accepting:

**Frequency Validation:**
- Range: 16,666 Hz to 125,000 Hz
- Reason: Hardware period limit of 8000-60000 ns
- Error message shows entered value and valid range

**Current Validation:**
- Range: 0 to 7000 mA
- Reason: Maximum diode current rating
- Error message shows entered value and valid range

**COM Port Validation:**
- Must select valid port from list
- Cannot accept "No ports found" placeholder
- Error message prompts to check connections

## Protocol Details

### Command Format

All commands follow the format:
```
COMMAND [value]<CR>
```

Where:
- `COMMAND` is a 3-letter mnemonic (e.g., LDO, LDF, LDS)
- `[value]` is optional numeric parameter
- `<CR>` is carriage return (0x0D)

### Command Set

| Command | Parameter | Description |
|---------|-----------|-------------|
| LDO | 0/1 | Laser enable (0=off, 1=on) |
| LDG | 0/1/2 | Pulse mode (0=single, 1=gating, 2=continuous) |
| LDF | 8000-60000 | Pulse period in nanoseconds |
| LDS | 0-7000 | Diode current in milliamps |
| LDP | - | Query output power (mW) |
| LDPT | - | Query pump temperature (m°C) |
| LDRT | - | Query resonator temperature (m°C) |
| LDQT | - | Query q-switch temperature (m°C) |
| LDPST | - | Query power stage temperature (m°C) |
| LDSR | - | Query status register |
| LDOH | - | Query operation hours |
| LDCSN | - | Query controller serial number |
| LDHSN | - | Query head serial number |

### Response Format

Responses are numeric values terminated with `<CR>`:
```
12345<CR>
```

**Exception:** Serial numbers are returned as strings:
```
SN12345678<CR>
```

### Status Register

The status register (LDSR) returns a 16-bit value with error flags:

| Bit | Mask | Meaning |
|-----|------|---------|
| 0 | 0x0001 | Pump temperature error |
| 1 | 0x0002 | Resonator temperature error |
| 2 | 0x0004 | Q-switch temperature error |
| 3 | 0x0008 | Power stage temperature error |
| 4 | 0x0010 | Diode current error |
| 5 | 0x0020 | Interlock open |
| 6 | 0x0040 | Over-power condition |
| 7 | 0x0080 | Under-voltage condition |

A status of 0 indicates no errors.

### Set and Verify Pattern

For critical parameters, the driver uses a set-and-verify pattern:

```python
def _set_and_verify(self, set_cmd: bytes, query_cmd: bytes, expected: str) -> bool:
    # Send set command
    self._serial.write(set_cmd)
    time.sleep(0.05)  # Allow hardware to process

    # Query back the value
    self._serial.write(query_cmd)
    response = self._read_response()

    # Verify it matches
    return response.strip() == expected.strip()
```

This ensures commands are executed correctly and hardware state matches software state.

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to laser

**Solutions:**
- Verify COM port name is correct (`HeliosDriver.list_available_ports()`)
- Check RS-232 cable connection
- Verify laser controller is powered on
- Try different COM port
- Check device permissions on Linux (`sudo usermod -a -G dialout $USER`)

### Communication Errors

**Problem:** Commands fail or no response

**Solutions:**
- Verify baud rate is 9600 (default)
- Check cable for proper null-modem configuration if needed
- Increase timeout: `driver = HeliosDriver(timeout=2.0)`
- Check for CR line termination (0x0D)
- Verify no other software has port open

### Frequency/Current Not Updating

**Problem:** Settings don't change on hardware

**Solutions:**
- Check return value of `set_frequency_hz()` and `set_current_ma()`
- Verify parameters are in valid range
- Check status register for errors: `driver.query_status_register()`
- Ensure laser is not in error state
- Try power cycling the controller

### Temperature Warnings

**Problem:** High temperature readings

**Solutions:**
- Check ventilation around laser head and controller
- Reduce diode current if at maximum
- Allow longer cool-down between operations
- Clean air filters if present
- Check for blocked cooling fans

### Laser Won't Enable

**Problem:** `set_laser_enable(True)` fails or laser stays off

**Solutions:**
- Check interlock connections (bit 5 of status register)
- Verify all interlocks are closed
- Check for error flags in status register
- Ensure parameters (frequency, current) are set
- Check external enable switch if present
- Review safety interlock documentation

### Status Register Errors

**Problem:** Status register shows error bits set

**Solutions:**
- Decode status register: `HeliosProtocol.decode_status_register(value)`
- Address specific error conditions:
  - Temperature errors: Improve cooling
  - Current error: Reduce current setting
  - Interlock open: Check safety connections
  - Over-power: Reduce current
  - Under-voltage: Check power supply

## Debug Output

The driver provides extensive debug output:

```
INFO: Informational messages about operations
DEBUG: Detailed command/response information
WARNING: Potential issues (high temp, errors)
ERROR: Operation failures
```

Enable Python logging to capture all output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Example debug output:
```
INFO: Connecting to Helios laser on COM5
DEBUG: Sending command: b'LDCSN\r'
DEBUG: Received response: SN12345678
INFO: Successfully connected to Helios on COM5
DEBUG: Sending command: b'LDF 100000\r'
DEBUG: Verifying frequency setting...
INFO: Frequency set to 10000.0 Hz (period: 100000 ns)
```

## Performance Notes

- Command response time: 50-100ms typical
- Temperature queries: ~100ms per sensor
- Status register query: ~50ms
- All queries are synchronous (blocking)
- Thread-safe for concurrent access (mutex protected)
- Set-and-verify adds ~50ms overhead for reliability

## Safety Considerations

### Laser Safety
- **Class 4 Laser**: Hazardous to eyes and skin
- Always verify laser is disabled before opening beam paths
- Use appropriate laser safety eyewear
- Follow all facility laser safety procedures
- Ensure proper interlock connections

### Thermal Management
- Monitor temperatures during operation
- Allow adequate cool-down between high-power operations
- Ensure proper ventilation
- Do not block cooling vents

### Electrical Safety
- Verify proper grounding
- Use shielded cables for trigger/status connections
- Follow proper ESD procedures when servicing

## Hardware Connections

### Utility Connector (9-pin D-Sub)

The utility connector provides external control:

| Pin | Signal | Description |
|-----|--------|-------------|
| 1 | GND | Ground |
| 2 | Laser Disable | Input: Pull low to disable laser |
| 3 | External Trigger | Input: Rising edge triggers pulse |
| 4 | Status Out | Output: High when ready |
| 5 | GND | Ground |
| 6-9 | NC | Not connected |

Trigger specifications:
- Input: TTL/CMOS compatible
- Minimum pulse width: 100ns
- Maximum frequency: Limited by pulse mode setting

## References

- **Protocol Documentation**: `helios_comms_protocol.pdf`
- **RS-232 Standard**: EIA/TIA-232
- **Integration Guide**: `SETUP.md`
- **Connection Guide**: See main window Helios settings dialog

## License

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
