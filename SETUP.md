# nueScan Setup Guide

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Method 1: Run as module
```bash
python -m nuescan
```

### Method 2: Run __main__.py directly
```bash
python __main__.py
```

## Project Structure

```
nuescan/
├── __main__.py                    # Application entry point
├── main_window.py                 # Main window controller
├── requirements.txt               # Python dependencies
├── SETUP.md                       # This file
│
├── dialogs/                       # Dialog controllers
│   ├── __init__.py
│   ├── genesis_dialog.py          # Genesis settings dialog
│   ├── helios_dialog.py           # Helios settings dialog
│   └── scan_active_dialog.py      # Scan progress dialog
│
├── hardware/                      # Hardware interface stubs
│   ├── __init__.py
│   ├── thorlabs_stage.py          # ThorLabs MLS stage controller
│   ├── t3r_device.py              # T3R-SL device controller
│   └── microscope.py              # Genesis/Helios controller
│
└── *.ui                           # Qt Designer UI files
```

## Hardware Interfaces

### Current Implementation Status

All hardware modules are currently **STUB IMPLEMENTATIONS** for development and testing. They simulate hardware responses without requiring actual devices.

#### ThorLabs MLS Stage
- **File**: `hardware/thorlabs_stage.py`
- **Purpose**: 3-axis positioning control
- **Connection**: USB/Serial
- **Status**: Stub - simulates connection, homing, and positioning

#### T3R-SL Device
- **File**: `hardware/t3r_device.py`
- **Purpose**: Timing and trigger control
- **Connection**: USB/Serial (COM port)
- **Status**: Stub - simulates device connection and status

#### Microscope Systems (Genesis/Helios)
- **File**: `hardware/microscope.py`
- **Purpose**: Laser system control
- **Connection**: USB/Serial
- **Status**: Stub - simulates laser parameters and interlocks

### Implementing Real Hardware Support

To add actual hardware support, modify the stub methods in the respective hardware files:

1. Add real serial communication using `pyserial`
2. Implement manufacturer-specific protocols
3. Add error handling and timeout logic
4. Implement actual status polling from devices

## UI Event Connections

All UI elements are connected to handler methods:

### Buttons
- ThorLabs stage connect/disconnect
- COM port refresh and connect
- Genesis/Helios settings dialogs
- Begin scanning
- Advanced oscilloscope settings

### ComboBoxes
- COM port selection
- Number of scans
- Row spacing
- Oscilloscope channel selections

### Text Inputs
- Stage serial number
- Scan coordinates (X/Y start, delta)
- Trigger voltage
- VISA address

## Development Notes

### Adding New Hardware
1. Create new controller class in `hardware/` directory
2. Import and instantiate in `main_window.py`
3. Add status update methods
4. Connect to UI elements as needed

### Modifying UI
1. Edit `.ui` files with Qt Designer
2. UI elements are accessed by their object names
3. Connections are made in `_connect_signals()` method

### Debug Output
All stub methods print debug information to console. Look for:
- `DEBUG:` - Function calls and state changes
- `INFO:` - Successful operations
- `WARNING:` - Potential issues
- `ERROR:` - Operation failures

## Testing

The application can be run without any hardware connected. All hardware interfaces will simulate proper responses.

### Test Progress Dialog
To test the scan progress dialog with simulated progress:
1. Configure scan parameters
2. Click "Begin Scan"
3. The dialog will show with demo progress animation

## License

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
