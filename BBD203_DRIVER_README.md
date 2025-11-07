# ThorLabs BBD203 Motor Controller Driver

## Overview

This directory contains a complete implementation of the ThorLabs BBD203 3-channel benchtop brushless DC motor controller driver. The driver implements the full APT (Advanced Positioning Technology) binary communications protocol as specified in the BBD203_Communications_Protocol.md document.

## Architecture

The BBD203 driver is split into three layers:

### 1. Protocol Layer (`bbd203_protocol.py`)

Low-level protocol implementation that handles:
- Binary message construction and parsing
- APT protocol message IDs and structures
- Unit conversions (mm ↔ encoder counts, velocity/acceleration scaling)
- Status bit definitions

**Key Classes:**
- `MessageID`: Enumeration of all APT message IDs
- `APTMessage`: Message builder and parser for binary protocol
- `APTProtocol`: High-level protocol interface with unit conversions

### 2. Driver Layer (`bbd203_driver.py`)

Complete driver implementation providing:
- Serial communication with automatic message reception thread
- 3-channel management (independent motor control)
- Blocking and non-blocking move operations
- Status monitoring with automatic updates
- Event callbacks for move/home completion
- Thread-safe operation

**Key Classes:**
- `BBD203Channel`: Represents state of a single motor channel
- `BBD203Driver`: Main driver class for controller communication

### 3. Stage Interface Layer (`thorlabs_stage.py`)

Application-specific wrapper that:
- Maps 3 motor channels to X/Y/Z axes
- Provides simplified API for stage control
- Integrates with the nueScan application
- Maintains compatibility with existing UI

**Channel Mapping:**
- Channel 1 → X-axis
- Channel 2 → Y-axis
- Channel 3 → Z-axis (optional)

## Features

### Communication
- Binary APT protocol over USB/RS232
- Baud rate: 115200 (configurable)
- Automatic message reception in background thread
- Command/response handling with proper timeout

### Motion Control
- Absolute positioning
- Relative moves
- Velocity control
- Immediate and profiled stops
- Configurable acceleration

### Position Feedback
- Real-time position updates (encoder counts)
- Position in mm (with configurable scaling)
- Status bit monitoring (homing, moving, errors, etc.)

### Homing
- Individual axis homing
- All-axes homing
- Blocking or non-blocking operation
- Completion callbacks

### Safety
- Interlock checking before moves
- Error detection and reporting
- Motion error monitoring
- Limit switch status

## Usage

### Connection Methods

The driver supports two connection methods:

#### Method 1: Connect by Serial Number (Recommended)

Similar to ThorLabs Kinesis library - automatically finds the USB device:

```python
from hardware.bbd203_driver import BBD203Driver

# Create driver instance
driver = BBD203Driver(encoder_counts_per_mm=20000)

# List available ThorLabs devices
devices = driver.list_thorlabs_devices()
for device in devices:
    print(f"Serial: {device['serial']}, Port: {device['port']}")

# Connect by serial number (auto-finds the port)
driver.connect_by_serial('83123456')  # Serial printed on controller
```

#### Method 2: Connect by Port Name

Direct connection to a specific port:

```python
# Connect to specific port
driver.connect('/dev/ttyUSB0')  # or 'COM3' on Windows
```

### Basic Movement

```python

# Enable all channels
driver.enable_channel(1, True)  # X-axis
driver.enable_channel(2, True)  # Y-axis
driver.enable_channel(3, True)  # Z-axis

# Home all channels (blocking)
driver.home_all_channels(wait=True, timeout=60)

# Set velocity parameters
driver.set_velocity_params(channel=1, max_vel_mm_s=5.0, accel_mm_s2=10.0)

# Move to absolute position (non-blocking)
driver.move_absolute(channel=1, position_mm=10.0, wait=False)

# Move to absolute position (blocking)
driver.move_absolute(channel=2, position_mm=25.0, wait=True, timeout=30)

# Move relative
driver.move_relative(channel=1, distance_mm=-5.0, wait=True)

# Stop motion
driver.stop(channel=1, immediate=True)

# Get position
pos = driver.get_position(channel=1)
print(f"Position: {pos} mm")

# Get detailed status
status = driver.get_channel_status(channel=1)
print(f"Enabled: {status['enabled']}")
print(f"Homed: {status['homed']}")
print(f"Moving: {status['moving']}")

# Disconnect
driver.disconnect()
```

### Using the Stage Interface

```python
from hardware.thorlabs_stage import ThorLabsStage

# Create stage controller
stage = ThorLabsStage(encoder_counts_per_mm=20000)

# List available devices
devices = stage.list_devices()
for device in devices:
    print(f"BBD203 Serial: {device['serial']}")

# Connect by serial number (automatically enables all channels)
stage.connect('83123456')  # Serial number from controller label

# Home all axes
stage.home_all_axes(wait=True)

# Move to position
stage.move_absolute(x=10.0, y=20.0, wait=True)

# Move relative
stage.move_relative(dx=5.0, dy=-2.5, wait=True)

# Get position
pos = stage.get_position()
print(f"X: {pos['x']} mm, Y: {pos['y']} mm, Z: {pos['z']} mm")

# Check status
status = stage.get_status()
print(f"Ready: {status['ready']}")
print(f"X Homed: {status['x_homed']}")

# Disconnect
stage.disconnect()
```

### Event Callbacks

```python
# Define callback function
def on_move_complete(channel):
    print(f"Channel {channel} move completed!")

# Register callback
driver.register_move_complete_callback(1, on_move_complete)

# Start non-blocking move - callback will be called when complete
driver.move_absolute(channel=1, position_mm=50.0, wait=False)
```

## Configuration

### Encoder Scaling

The encoder resolution must be configured to match your specific motor/stage combination:

```python
# Example: MLS203 stage with 20,000 counts/mm
driver = BBD203Driver(encoder_counts_per_mm=20000)

# Example: Custom stage with 2,000 counts/mm
driver = BBD203Driver(encoder_counts_per_mm=2000)
```

Common encoder resolutions:
- **MLS203**: 20,000 counts/mm
- **DDS220**: 2,000 counts/mm
- **Custom**: Varies (check motor specifications)

### Velocity and Acceleration

Velocity and acceleration use the APT scaling formulas:

```
VEL_APT = EncCnt × 102.4e-6 × 65536 × Vel
ACC_APT = EncCnt × (102.4e-6)² × 65536 × Acc
```

The driver handles these conversions automatically:

```python
# Set velocity to 5 mm/s, acceleration to 10 mm/s²
driver.set_velocity_params(
    channel=1,
    max_vel_mm_s=5.0,
    accel_mm_s2=10.0
)
```

## Integration with nueScan

The driver is integrated into nueScan through the `ThorLabsStage` wrapper class. The connection is simplified using serial number auto-detection:

### Connecting in the UI

1. **Find Serial Number**: Look at the label on your BBD203 controller (e.g., `83123456`)
2. **Enter Serial**: Type the serial number in the "ThorLABS MLS Stage Serial" field
3. **Connect**: Click "Connect" button
   - Driver automatically finds the USB device
   - All 3 channels are enabled
   - Status updates begin
4. **Ready**: The controller is now ready to home and move axes

### Connection Process

When you click "Connect":
- The driver scans all USB ports for ThorLabs devices (FTDI VID: 0x0403)
- Finds the device matching your serial number
- Automatically uses the correct COM port
- Enables all channels (X/Y/Z axes)
- Sets default velocity parameters

### Troubleshooting Connection

If connection fails, a dialog will show:
- The serial number you entered
- List of all detected ThorLabs devices with their serial numbers
- Helps you identify the correct serial to use

## Protocol Details

### Message Structure

All APT messages consist of:
- 6-byte header (message ID, length, destination, source)
- Optional data packet (variable length)

### Destination Addressing

- `0x21`: Channel 1 (X-axis)
- `0x22`: Channel 2 (Y-axis)
- `0x23`: Channel 3 (Z-axis)
- `0x11`: All channels
- `0x50`: USB interface

### Status Bits

Key status bits monitored by the driver:

| Bit | Mask | Meaning |
|-----|------|---------|
| HOMING | 0x00000200 | Homing in progress |
| HOMED | 0x00000400 | Axis has been homed |
| TRACKING | 0x00001000 | Following target position |
| SETTLED | 0x00002000 | Position settled |
| MOTION_ERROR | 0x00004000 | Following error exceeded |
| MOTOR_ENABLED | 0x80000000 | Motor drive enabled |
| IN_MOTION_FORWARD | 0x00000010 | Moving forward |
| IN_MOTION_REVERSE | 0x00000020 | Moving reverse |

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to controller

**Solutions:**
- Verify COM port name is correct (`ThorLabsStage.list_available_ports()`)
- Check USB cable connection
- Verify no other software has the port open
- Try different baud rate (default: 115200)
- Check device permissions on Linux

### Homing Fails

**Problem:** Homing timeout or never completes

**Solutions:**
- Increase homing timeout parameter
- Check limit switches are functioning
- Verify motor is enabled
- Check for mechanical obstructions
- Review homing parameters (direction, velocity)

### Position Errors

**Problem:** Reported position doesn't match reality

**Solutions:**
- Verify `encoder_counts_per_mm` setting matches your stage
- Check encoder connections
- Reset position counter if needed: `driver.cmd_set_position_counter()`
- Verify stage is homed before moves

### Communication Errors

**Problem:** Commands not acknowledged or responses missing

**Solutions:**
- Increase serial timeout
- Check for message buffer overflow
- Verify automatic status updates are enabled
- Add delays between rapid commands

## Debug Output

The driver provides extensive debug output:

```
INFO: Messages about successful operations
DEBUG: Detailed command/response information
ERROR: Error conditions and failures
WARNING: Potential issues
```

Enable Python logging to capture all output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Notes

- Message processing runs in separate thread (no blocking)
- Typical command response time: 10-50ms
- Position updates: ~10Hz when status messages enabled
- Move completion detected via asynchronous message
- Thread-safe for concurrent channel operations

## References

- **Protocol Documentation**: `BBD203_Communications_Protocol.md`
- **APT Protocol Version**: 42.1
- **Product Manual**: Available from Thorlabs.com
- **Technical Support**: techsupport@thorlabs.com

## License

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
