# BBD203 Connection Guide

## Quick Start - Connecting Your BBD203 Controller

This guide explains how to connect your ThorLabs BBD203 motor controller to nueScan using the simplified serial number method.

---

## Step 1: Physical Connection

1. **Connect USB Cable**
   - Connect the USB cable from your BBD203 controller to your computer
   - Wait for Windows/Linux to recognize the device
   - No special drivers needed (uses standard FTDI USB-Serial)

2. **Power On Controller**
   - Ensure BBD203 is powered on
   - Front panel should be lit

---

## Step 2: Find Serial Number

The serial number is printed on a label on your BBD203 controller.

**Common Locations:**
- Back panel of the controller
- Side panel
- Original packaging

**Format:**
- Usually 8 digits (e.g., `83123456`)
- May include letters (e.g., `83A12345`)

**Example Label:**
```
ThorLabs BBD203
S/N: 83123456
```

---

## Step 3: Connect in nueScan

### Using the GUI

1. **Launch nueScan**
   ```bash
   python -m nuescan
   ```

2. **Enter Serial Number**
   - Locate the "ThorLABS MLS Stage Serial:" field at the top of the window
   - Type your serial number (e.g., `83123456`)

3. **Click Connect**
   - Click the "Connect" button next to the serial field
   - Wait 1-2 seconds for connection

4. **Success!**
   - If successful, you'll see a confirmation dialog
   - Button changes to "Disconnect"
   - All 3 motor channels are now enabled

### Programmatic Connection

```python
from hardware.thorlabs_stage import ThorLabsStage

# Create stage instance
stage = ThorLabsStage(encoder_counts_per_mm=20000)

# Connect by serial number
success = stage.connect('83123456')

if success:
    print("Connected! Ready to home axes.")
else:
    print("Connection failed.")
```

---

## Troubleshooting

### "Device not found" Error

**Problem:** Connection fails with "Could not find BBD203 with serial number..."

**Solutions:**

1. **Check USB Connection**
   - Ensure USB cable is fully inserted
   - Try a different USB port
   - Try a different USB cable

2. **Verify Serial Number**
   - Double-check the serial number on the controller label
   - Ensure no typos (0 vs O, 1 vs I, etc.)

3. **List Available Devices**
   - The error dialog will show all detected ThorLabs devices
   - Check if your device appears with a different serial number
   - If no devices shown, check USB connection and drivers

4. **Windows: Check Device Manager**
   - Open Device Manager
   - Look under "Ports (COM & LPT)"
   - Should see "USB Serial Port (COMx)" with FTDI in description
   - If device shows with "!" icon, driver issue

5. **Linux: Check Permissions**
   ```bash
   # Check if device is detected
   lsusb | grep -i ftdi

   # Check serial ports
   ls -l /dev/ttyUSB*

   # Add user to dialout group (may require logout)
   sudo usermod -a -G dialout $USER
   ```

### Connection Succeeds but No Response

**Problem:** Connection successful but motors don't respond

**Solutions:**

1. **Check Power**
   - Verify motors are connected and powered
   - Check motor power LEDs on BBD203 front panel

2. **Enable Channels**
   - Channels should auto-enable on connection
   - Check status indicators in UI

3. **Home Axes**
   - Axes may need homing before movement
   - Try homing each axis

### Multiple Controllers

**Problem:** You have multiple BBD203 controllers connected

**Solution:**
- Each controller has a unique serial number
- Connect to specific controller by entering its serial number
- Error dialog will show all connected devices

---

## What Happens During Connection

### Automatic Process

When you click "Connect", the following happens automatically:

1. **USB Enumeration**
   - Scans all USB ports
   - Finds ThorLabs devices (FTDI vendor ID: 0x0403)
   - Matches your serial number

2. **Port Assignment**
   - Determines the COM port (e.g., COM3, /dev/ttyUSB0)
   - Opens serial connection at 115200 baud

3. **Controller Initialization**
   - Requests hardware information
   - Enables automatic status updates
   - Enables all 3 motor channels

4. **Default Configuration**
   - Sets velocity: 1.0 mm/s
   - Sets acceleration: 5.0 mm/s²
   - Starts position monitoring

### Status Updates

After connection:
- Position updates received every ~100ms
- Status bits monitored (homed, moving, errors)
- Move completion notifications enabled

---

## Advanced Configuration

### Custom Encoder Resolution

If you're using a stage with different encoder resolution:

```python
# Example: Stage with 2,000 counts/mm instead of default 20,000
stage = ThorLabsStage(encoder_counts_per_mm=2000)
stage.connect('83123456')
```

Common resolutions:
- **MLS203**: 20,000 counts/mm (default)
- **DDS220**: 2,000 counts/mm
- **Custom**: Check your stage specifications

### Direct Port Connection (Not Recommended)

If you need to connect to a specific port instead of using serial number:

```python
from hardware.bbd203_driver import BBD203Driver

driver = BBD203Driver()
driver.connect('COM3')  # or '/dev/ttyUSB0' on Linux
```

---

## System Requirements

### Operating Systems
- ✅ Windows 7/8/10/11
- ✅ Linux (Ubuntu, Fedora, etc.)
- ✅ macOS (with FTDI driver)

### Dependencies
- Python 3.8+
- PySerial 3.5+
- PyQt6 6.4+

### USB Requirements
- USB 2.0 or higher
- FTDI USB-Serial drivers (usually automatic)

---

## Next Steps

After successful connection:

1. **Home the Axes**
   - Required before first movement
   - Establishes zero position reference

2. **Test Movement**
   - Try small movements to verify operation
   - Check position feedback in UI

3. **Configure Scan Parameters**
   - Set scan area (X/Y start, delta)
   - Set row spacing
   - Configure velocity if needed

4. **Begin Scanning**
   - All systems should show "Ready"
   - Click "Begin Scan" to start

---

## Support

For issues with the BBD203 driver or connection:

1. **Check Debug Output**
   - Console window shows connection details
   - Look for "INFO:", "DEBUG:", and "ERROR:" messages

2. **Review Driver Documentation**
   - `BBD203_DRIVER_README.md` - Complete driver reference
   - `BBD203_Communications_Protocol.md` - Protocol details

3. **ThorLabs Support**
   - For hardware issues: techsupport@thorlabs.com
   - For driver/protocol questions: Review APT documentation

---

## Example Session

```
$ python -m nuescan

# UI appears
# Enter serial: 83123456
# Click Connect

# Console output:
INFO: Connecting to BBD203 with serial number 83123456
DEBUG: Found ThorLabs device - Serial: 83123456, Port: COM3
INFO: Found device 83123456 on port COM3
INFO: Connecting to BBD203 on COM3
INFO: Successfully connected to BBD203 on COM3
INFO: Stage connected and channels enabled

# Success dialog appears
# Button changes to "Disconnect"
# Ready to home and move!
```

---

*For detailed technical information, see `BBD203_DRIVER_README.md`*
