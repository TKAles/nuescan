# BBD203 Motor Controller - APT Communications Protocol

## Version 42.1 - Extracted Documentation

This document contains only the information relevant to the **BBD203 3-Channel Benchtop Brushless DC Motor Controller**, extracted from the complete Thorlabs APT Communications Protocol documentation.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [General Protocol Information](#2-general-protocol-information)
3. [BBD203 Specifications](#3-bbd203-specifications)
4. [Message Format](#4-message-format)
5. [BBD203 Applicable Messages](#5-bbd203-applicable-messages)
6. [Command Examples](#6-command-examples)
7. [Important Notes for BBD203](#7-important-notes-for-bbd203)

---

## 1. Introduction

The BBD203 is a 3-channel benchtop brushless DC motor controller that is part of Thorlabs' APT motion control system. This document describes the communication protocol used to control the BBD203 via USB or RS232 interfaces.

### 1.1 Device Overview

The BBD203 provides independent control of up to three brushless DC motors with the following key features:

- 3 independent motor channels
- USB and RS232 communication interfaces
- Closed-loop position and velocity control
- Encoder feedback support
- Digital I/O for triggering and synchronization
- Compatible with Thorlabs' APT software suite

### 1.2 Related Controllers

The BBD203 shares its protocol with other controllers in the BBD series:
- **BBD201** - 1 Channel Benchtop Brushless DC Motor Driver
- **BBD202** - 2 Channel Benchtop Brushless DC Motor Driver
- **BBD203** - 3 Channel Benchtop Brushless DC Motor Driver

---

## 2. General Protocol Information

### 2.1 Communication Format

All communications with the BBD203 use a binary message protocol. Messages consist of a 6-byte header followed by an optional data packet.

#### Header Structure (6 bytes):

| Byte | Description |
|------|------------|
| 0-1 | Message ID (16-bit, little-endian) |
| 2 | Data length (bytes) or parameter 1 |
| 3 | Data length MSB or parameter 2 |
| 4 | Destination |
| 5 | Source |

#### Destination Byte Values:

| Value | Description |
|-------|------------|
| 0x50 | Generic USB device |
| 0x11 | Rack controller (card slot unit) |
| 0x21 | Bay 1 / Channel 1 |
| 0x22 | Bay 2 / Channel 2 |
| 0x23 | Bay 3 / Channel 3 |

#### Source Byte Values:

| Value | Description |
|-------|------------|
| 0x01 | Host PC |

### 2.2 Channel Addressing

The BBD203 has three motor channels. When addressing specific channels:

- **Channel 1**: Use destination byte `0x21`
- **Channel 2**: Use destination byte `0x22`
- **Channel 3**: Use destination byte `0x23`
- **All channels**: Use destination byte `0x11`

**Important**: Although the BBD203 has 3 channels, each channel operates as an independent single-channel controller. In the data packet's channel identifier field, always use Channel 1 (`0x01 0x00`), and use the destination byte in the header to specify the physical channel.

### 2.3 Data Types

| Type | Size | Description |
|------|------|------------|
| char | 1 byte | 8-bit signed integer |
| short | 2 bytes | 16-bit signed integer (little-endian) |
| long | 4 bytes | 32-bit signed integer (little-endian) |
| word | 2 bytes | 16-bit unsigned integer (little-endian) |
| dword | 4 bytes | 32-bit unsigned integer (little-endian) |

---

## 3. BBD203 Specifications

### 3.1 Encoder and Position Scaling

For BBD203 controllers, position and velocity values are scaled based on encoder counts. The scaling formulas are:

#### Position Scaling:
```
POS_APT = EncCnt × Pos
```
Where:
- `POS_APT` = Position value to send/receive via APT protocol
- `EncCnt` = Encoder counts per unit (stage-specific)
- `Pos` = Position in real units (mm, degrees, etc.)

#### Velocity Scaling:
```
VEL_APT = EncCnt × T × 65536 × Vel
```
Where:
- `VEL_APT` = Velocity value to send/receive via APT protocol
- `T` = 102.4 × 10⁻⁶ seconds (controller sample time)
- `Vel` = Velocity in real units per second

#### Acceleration Scaling:
```
ACC_APT = EncCnt × T² × 65536 × Acc
```
Where:
- `ACC_APT` = Acceleration value to send/receive via APT protocol
- `T²` = (102.4 × 10⁻⁶)²
- `Acc` = Acceleration in real units per second²

### 3.2 Example Scaling Values

For a stage with 20,000 encoder counts per mm:
- Position of 10 mm = 200,000 counts
- Velocity of 1 mm/s = 134,218 APT units
- Acceleration of 1 mm/s² = 13.7 APT units

---

## 4. Message Format

### 4.1 Message Types

Messages are categorized into several types:

- **MOD** - Module control messages (identify, enable/disable)
- **HW** - Hardware information and control
- **MOT** - Motor control messages (move, velocity, position)
- **RACK** - Rack and bay status messages

### 4.2 Message Flow

1. **Command Messages**: Sent from host to controller
2. **Request Messages**: Request data from controller
3. **Get Messages**: Controller response with requested data
4. **Status Messages**: Unsolicited updates from controller

---

## 5. BBD203 Applicable Messages

### 5.1 Module Control Messages

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOD_IDENTIFY | 0x0223 | Host→Device | Flash front panel LEDs to identify unit |
| MGMSG_MOD_SET_CHANENABLESTATE | 0x0210 | Host→Device | Enable/disable a motor channel |
| MGMSG_MOD_REQ_CHANENABLESTATE | 0x0211 | Host→Device | Request channel enable state |
| MGMSG_MOD_GET_CHANENABLESTATE | 0x0212 | Device→Host | Get channel enable state response |

### 5.2 Hardware Control Messages

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_HW_DISCONNECT | 0x0002 | Host→Device | Disconnect from USB bus |
| MGMSG_HW_RESPONSE | 0x0080 | Device→Host | Response/error message |
| MGMSG_HW_RICHRESPONSE | 0x0081 | Device→Host | Detailed response with error info |
| MGMSG_HW_START_UPDATEMSGS | 0x0011 | Host→Device | Start automatic status updates |
| MGMSG_HW_STOP_UPDATEMSGS | 0x0012 | Host→Device | Stop automatic status updates |
| MGMSG_HW_REQ_INFO | 0x0005 | Host→Device | Request hardware information |
| MGMSG_HW_GET_INFO | 0x0006 | Device→Host | Hardware information response |

### 5.3 Rack Status Messages

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_RACK_REQ_BAYUSED | 0x0060 | Host→Device | Request which bays are occupied |
| MGMSG_RACK_GET_BAYUSED | 0x0061 | Device→Host | Bay occupation status |
| MGMSG_RACK_REQ_STATUSBITS | 0x0226 | Host→Device | Request rack status bits |
| MGMSG_RACK_GET_STATUSBITS | 0x0227 | Device→Host | Rack status bits response |
| MGMSG_RACK_SET_DIGOUTPUTS | 0x0228 | Host→Device | Set digital outputs |
| MGMSG_RACK_REQ_DIGOUTPUTS | 0x0229 | Host→Device | Request digital output states |
| MGMSG_RACK_GET_DIGOUTPUTS | 0x0230 | Device→Host | Digital output states |

### 5.4 Motor Control Messages - Basic

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_SET_POSCOUNTER | 0x0410 | Host→Device | Set position counter value |
| MGMSG_MOT_REQ_POSCOUNTER | 0x0411 | Host→Device | Request position counter |
| MGMSG_MOT_GET_POSCOUNTER | 0x0412 | Device→Host | Position counter value |
| MGMSG_MOT_SET_ENCCOUNTER | 0x0409 | Host→Device | Set encoder counter value |
| MGMSG_MOT_REQ_ENCCOUNTER | 0x040A | Host→Device | Request encoder counter |
| MGMSG_MOT_GET_ENCCOUNTER | 0x040B | Device→Host | Encoder counter value |

### 5.5 Motor Control Messages - Homing

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_SET_HOMEPARAMS | 0x0440 | Host→Device | Set homing parameters |
| MGMSG_MOT_REQ_HOMEPARAMS | 0x0441 | Host→Device | Request homing parameters |
| MGMSG_MOT_GET_HOMEPARAMS | 0x0442 | Device→Host | Homing parameters |
| MGMSG_MOT_MOVE_HOME | 0x0443 | Host→Device | Start homing sequence |
| MGMSG_MOT_MOVE_HOMED | 0x0444 | Device→Host | Homing completed |

### 5.6 Motor Control Messages - Movement

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_SET_MOVERELPARAMS | 0x0445 | Host→Device | Set relative move parameters |
| MGMSG_MOT_REQ_MOVERELPARAMS | 0x0446 | Host→Device | Request relative move parameters |
| MGMSG_MOT_GET_MOVERELPARAMS | 0x0447 | Device→Host | Relative move parameters |
| MGMSG_MOT_MOVE_RELATIVE | 0x0448 | Host→Device | Start relative move |
| MGMSG_MOT_SET_MOVEABSPARAMS | 0x0450 | Host→Device | Set absolute move parameters |
| MGMSG_MOT_REQ_MOVEABSPARAMS | 0x0451 | Host→Device | Request absolute move parameters |
| MGMSG_MOT_GET_MOVEABSPARAMS | 0x0452 | Device→Host | Absolute move parameters |
| MGMSG_MOT_MOVE_ABSOLUTE | 0x0453 | Host→Device | Start absolute move |
| MGMSG_MOT_MOVE_COMPLETED | 0x0464 | Device→Host | Move completed notification |
| MGMSG_MOT_MOVE_VELOCITY | 0x0457 | Host→Device | Start velocity move |
| MGMSG_MOT_MOVE_STOP | 0x0465 | Host→Device | Stop any motion |
| MGMSG_MOT_MOVE_STOPPED | 0x0466 | Device→Host | Motion stopped notification |

### 5.7 Motor Control Messages - Velocity Parameters

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_SET_VELPARAMS | 0x0413 | Host→Device | Set velocity parameters |
| MGMSG_MOT_REQ_VELPARAMS | 0x0414 | Host→Device | Request velocity parameters |
| MGMSG_MOT_GET_VELPARAMS | 0x0415 | Device→Host | Velocity parameters |

### 5.8 Motor Control Messages - Status

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_REQ_STATUSUPDATE | 0x0480 | Host→Device | Request status update |
| MGMSG_MOT_GET_STATUSUPDATE | 0x0481 | Device→Host | Status update |
| MGMSG_MOT_REQ_STATUSBITS | 0x0429 | Host→Device | Request status bits |
| MGMSG_MOT_GET_STATUSBITS | 0x042A | Device→Host | Status bits |

### 5.9 BBD-Specific Control Messages

| Message | Hex Code | Direction | Description |
|---------|----------|-----------|-------------|
| MGMSG_MOT_SET_DCPIDPARAMS | 0x04A0 | Host→Device | Set DC motor PID parameters |
| MGMSG_MOT_REQ_DCPIDPARAMS | 0x04A1 | Host→Device | Request DC motor PID parameters |
| MGMSG_MOT_GET_DCPIDPARAMS | 0x04A2 | Device→Host | DC motor PID parameters |
| MGMSG_MOT_SET_POSITIONLOOPPARAMS | 0x04D7 | Host→Device | Set position loop parameters |
| MGMSG_MOT_REQ_POSITIONLOOPPARAMS | 0x04D8 | Host→Device | Request position loop parameters |
| MGMSG_MOT_GET_POSITIONLOOPPARAMS | 0x04D9 | Device→Host | Position loop parameters |
| MGMSG_MOT_SET_MOTOROUTPUTPARAMS | 0x04DA | Host→Device | Set motor output parameters |
| MGMSG_MOT_REQ_MOTOROUTPUTPARAMS | 0x04DB | Host→Device | Request motor output parameters |
| MGMSG_MOT_GET_MOTOROUTPUTPARAMS | 0x04DC | Device→Host | Motor output parameters |
| MGMSG_MOT_SET_TRACKSETTLEDPARAMS | 0x04E0 | Host→Device | Set tracking/settled parameters |
| MGMSG_MOT_REQ_TRACKSETTLEDPARAMS | 0x04E1 | Host→Device | Request tracking/settled parameters |
| MGMSG_MOT_GET_TRACKSETTLEDPARAMS | 0x04E2 | Device→Host | Tracking/settled parameters |
| MGMSG_MOT_SET_PROFILEMODEPARAMS | 0x04E3 | Host→Device | Set profile mode parameters |
| MGMSG_MOT_REQ_PROFILEMODEPARAMS | 0x04E4 | Host→Device | Request profile mode parameters |
| MGMSG_MOT_GET_PROFILEMODEPARAMS | 0x04E5 | Device→Host | Profile mode parameters |
| MGMSG_MOT_SET_JOYSTICKPARAMS | 0x04E6 | Host→Device | Set joystick parameters |
| MGMSG_MOT_REQ_JOYSTICKPARAMS | 0x04E7 | Host→Device | Request joystick parameters |
| MGMSG_MOT_GET_JOYSTICKPARAMS | 0x04E8 | Device→Host | Joystick parameters |
| MGMSG_MOT_SET_CURRENTLOOPPARAMS | 0x04D4 | Host→Device | Set current loop parameters |
| MGMSG_MOT_REQ_CURRENTLOOPPARAMS | 0x04D5 | Host→Device | Request current loop parameters |
| MGMSG_MOT_GET_CURRENTLOOPPARAMS | 0x04D6 | Device→Host | Current loop parameters |
| MGMSG_MOT_SET_SETTLEDCURRENTLOOPPARAMS | 0x04E9 | Host→Device | Set settled current loop parameters |
| MGMSG_MOT_REQ_SETTLEDCURRENTLOOPPARAMS | 0x04EA | Host→Device | Request settled current loop parameters |
| MGMSG_MOT_GET_SETTLEDCURRENTLOOPPARAMS | 0x04EB | Device→Host | Settled current loop parameters |
| MGMSG_MOT_SET_STAGEAXISPARAMS | 0x04F0 | Host→Device | Set stage axis parameters |
| MGMSG_MOT_REQ_STAGEAXISPARAMS | 0x04F1 | Host→Device | Request stage axis parameters |
| MGMSG_MOT_GET_STAGEAXISPARAMS | 0x04F2 | Device→Host | Stage axis parameters |
| MGMSG_MOT_SET_TRIGGER | 0x0500 | Host→Device | Set trigger configuration |
| MGMSG_MOT_REQ_TRIGGER | 0x0501 | Host→Device | Request trigger configuration |
| MGMSG_MOT_GET_TRIGGER | 0x0502 | Device→Host | Trigger configuration |

---

## 6. Command Examples

### 6.1 Enable Channel 1

To enable channel 1 on the BBD203:

**Command bytes:**
```
TX: 10 02 01 01 21 01
```

**Breakdown:**
- `10 02` - MGMSG_MOD_SET_CHANENABLESTATE
- `01` - Enable channel (0x02 to disable)
- `01` - Channel 1
- `21` - Destination (Channel 1)
- `01` - Source (Host PC)

### 6.2 Home Channel 2

To initiate homing on channel 2:

**Command bytes:**
```
TX: 43 04 01 00 22 01
```

**Breakdown:**
- `43 04` - MGMSG_MOT_MOVE_HOME
- `01` - Channel identifier (always 0x01 for BBD203)
- `00` - Not used
- `22` - Destination (Channel 2)
- `01` - Source (Host PC)

### 6.3 Set Position Counter

To set the position counter for channel 1 to 10.0 mm (assuming 20,000 counts/mm):

**Command bytes:**
```
TX: 10 04 06 00 21 01 01 00 40 0D 03 00
```

**Breakdown:**
- `10 04` - MGMSG_MOT_SET_POSCOUNTER
- `06 00` - 6 byte data packet
- `21` - Destination (Channel 1)
- `01` - Source (Host PC)
- `01 00` - Channel 1 (in data packet)
- `40 0D 03 00` - Position = 200,000 counts (10 mm × 20,000)

### 6.4 Move Absolute

To move channel 3 to absolute position 50 mm:

**Command bytes:**
```
TX: 53 04 06 00 23 01 01 00 A0 86 01 00
```

**Breakdown:**
- `53 04` - MGMSG_MOT_MOVE_ABSOLUTE
- `06 00` - 6 byte data packet
- `23` - Destination (Channel 3)
- `01` - Source (Host PC)
- `01 00` - Channel 1 (in data packet, always 0x01 0x00)
- `A0 86 01 00` - Position = 1,000,000 counts (50 mm × 20,000)

### 6.5 Set Velocity Parameters

To set velocity parameters for channel 2 (max velocity = 5 mm/s, acceleration = 10 mm/s²):

**Command bytes:**
```
TX: 13 04 0E 00 22 01 01 00 00 00 8A 44 0A 00 89 00 00 00
```

**Breakdown:**
- `13 04` - MGMSG_MOT_SET_VELPARAMS
- `0E 00` - 14 byte data packet
- `22` - Destination (Channel 2)
- `01` - Source (Host PC)
- `01 00` - Channel 1 (in data packet)
- `00 00` - Min velocity (usually 0)
- `8A 44 0A 00` - Max velocity = 671,090 APT units (5 mm/s)
- `89 00 00 00` - Acceleration = 137 APT units (10 mm/s²)

### 6.6 Stop Motion

To immediately stop motion on all channels:

**Command bytes:**
```
TX: 65 04 01 01 11 01
```

**Breakdown:**
- `65 04` - MGMSG_MOT_MOVE_STOP
- `01` - Channel identifier
- `01` - Stop mode (0x01 = immediate, 0x02 = profiled)
- `11` - Destination (All channels)
- `01` - Source (Host PC)

### 6.7 Request Status Update

To request a status update from channel 1:

**Command bytes:**
```
TX: 80 04 01 00 21 01
```

**Breakdown:**
- `80 04` - MGMSG_MOT_REQ_STATUSUPDATE
- `01` - Channel identifier
- `00` - Not used
- `21` - Destination (Channel 1)
- `01` - Source (Host PC)

**Response format (20 bytes):**
```
RX: 81 04 14 00 01 00 [Channel] [Position-4bytes] [EncCount-4bytes] [StatusBits-4bytes]
```

### 6.8 Set Position Loop Parameters

To set position loop PID parameters for channel 1:

**Command bytes:**
```
TX: D7 04 1C 00 21 01 01 00 41 00 AF 00 80 38 01 00 [12 more bytes...]
```

**Data packet structure:**
- Bytes 0-1: Channel (0x01 0x00)
- Bytes 2-3: Proportional gain
- Bytes 4-5: Integral gain
- Bytes 6-9: Integral limit
- Bytes 10-13: Derivative gain
- Bytes 14-15: Derivative time
- Bytes 16-17: Loop rate
- Bytes 18-19: Output gain
- Bytes 20-23: Velocity feedforward gain
- Bytes 24-25: Acceleration feedforward gain
- Bytes 26-27: Position error limit

---

## 7. Important Notes for BBD203

### 7.1 Digital Output Configuration

On the BBD203, the digital output and trigger output share a common pin. Before using the digital output functionality, the trigger functionality must be disabled by calling the `MGMSG_MOT_SET_TRIGGER` message with appropriate parameters.

**To disable trigger and enable digital output:**
```
TX: 00 05 06 00 21 01 01 00 00 00 00 00
```

### 7.2 Multi-Channel Operation

Although the BBD203 has three channels, each channel operates as an independent single-channel controller. Important points:

- Always use Channel 1 (`0x01 0x00`) in the channel identifier field of data packets
- Use the destination byte (`0x21`, `0x22`, or `0x23`) in the header to specify the physical channel
- Each channel maintains its own parameters and status independently

### 7.3 Encoder Scaling

All position values must be scaled according to the encoder counts per unit of your specific motor and stage combination. Common encoder resolutions:

| Stage Type | Encoder Counts/mm | Notes |
|------------|-------------------|-------|
| MLS203 | 20,000 | Standard linear stage |
| DDS220 | 2,000 | Direct drive stage |
| Custom | Varies | Check motor specification |

### 7.4 Status Updates

After connecting to the BBD203, it is important to:

1. Call `MGMSG_HW_START_UPDATEMSGS` to enable automatic status updates
2. This ensures move completed and other status messages are received properly
3. Status updates can be disabled with `MGMSG_HW_STOP_UPDATEMSGS` when not needed

**Enable status updates:**
```
TX: 11 00 00 00 11 01
```

### 7.5 Error Handling

The BBD203 returns error messages via `MGMSG_HW_RESPONSE` (0x0080) or `MGMSG_HW_RICHRESPONSE` (0x0081). Common error conditions:

| Error | Description |
|-------|------------|
| Over current | Motor drawing excessive current |
| Following error | Position error exceeds limit |
| Limit switch | Hardware limit reached |
| Not homed | Attempting move before homing |

### 7.6 Trigger Configuration

The BBD203 supports hardware triggering for synchronized motion. Trigger modes:

| Mode | Value | Description |
|------|-------|------------|
| Disabled | 0x00 | No triggering |
| In/Out Relative Move | 0x01 | Trigger initiates relative move |
| In/Out Absolute Move | 0x02 | Trigger initiates absolute move |
| In/Out Home | 0x03 | Trigger initiates homing |
| In/Out Stop | 0x04 | Trigger stops motion |
| Out Only | 0x10 | Generate trigger output on move |
| Out Position | 0x11 | Trigger at specific position |

### 7.7 Profile Modes

The BBD203 supports different motion profile modes:

| Mode | Value | Description |
|------|-------|------------|
| Trapezoidal | 0x00 | Linear acceleration/deceleration |
| S-Curve | 0x02 | Smooth acceleration with jerk limiting |

### 7.8 Communication Best Practices

1. **Initialization Sequence:**
   - Send `MGMSG_HW_REQ_INFO` to verify connection
   - Enable required channels with `MGMSG_MOD_SET_CHANENABLESTATE`
   - Start update messages with `MGMSG_HW_START_UPDATEMSGS`
   - Home axes if required

2. **Movement Sequence:**
   - Set velocity/acceleration parameters
   - Clear any errors
   - Send move command
   - Wait for move completed message

3. **Shutdown Sequence:**
   - Stop any motion with `MGMSG_MOT_MOVE_STOP`
   - Disable channels if needed
   - Send `MGMSG_HW_DISCONNECT` before closing port

---

## Additional Information

This document contains only the essential information for controlling the BBD203 motor controller. For complete protocol details, advanced features, and other Thorlabs motion control products, please refer to the full APT Communications Protocol documentation.

### Contact Information

**Thorlabs, Inc.**
- Website: www.thorlabs.com
- Technical Support: techsupport@thorlabs.com

---

*Document generated from Thorlabs APT Communications Protocol v42.1*

## Table of Contents

1. [Introduction](#1-introduction)
2. [General Protocol Information](#2-general-protocol-information)
3. [BBD203 Specifications](#3-bbd203-specifications)
4. [Message Format](#4-message-format)
5. [BBD203 Applicable Messages](#5-bbd203-applicable-messages)
6. [Command Examples](#6-command-examples)
7. [Important Notes](#7-important-notes)

---

## 1. Introduction

The BBD203 is a 3-channel benchtop brushless DC motor controller that is part of Thorlabs' APT motion control system. This document describes the communication protocol used to control the BBD203 via USB or RS232 interfaces.

### 1.1 Device Overview

The BBD203 provides independent control of up to three brushless DC motors with the following key features:

- 3 independent motor channels
- USB and RS232 communication interfaces
- Closed-loop position and velocity control
- Encoder feedback support
- Digital I/O for triggering and synchronization
- Compatible with Thorlabs' APT software suite

### 1.2 Device Information

- **Product Name**: BBD203 - 3 Channel Benchtop Brushless DC Motor Driver
- **Protocol Version**: 42.1
- **Communication**: Binary message protocol over USB/RS232

---

## 2. General Protocol Information

### 2.1 Communication Format

All communications with the BBD203 use a binary message protocol. Messages consist of a 6-byte header followed by an optional data packet.

#### Header Structure

| Byte | Description |
|------|-------------|
| 0-1  | Message ID (16-bit, little-endian) |
| 2    | Data length (bytes) or parameter 1 |
| 3    | Data length MSB or parameter 2 |
| 4    | Destination |
| 5    | Source |

#### Destination Byte Values

| Value | Description |
|-------|-------------|
| 0x50  | USB interface |
| 0x11  | All channels (unit) |
| 0x21  | Channel 1 (Bay 1) |
| 0x22  | Channel 2 (Bay 2) |
| 0x23  | Channel 3 (Bay 3) |

#### Source Byte Values

| Value | Description |
|-------|-------------|
| 0x01  | Host PC |

### 2.2 Channel Addressing

The BBD203 has three motor channels. When addressing specific channels:

- **Channel 1**: Use destination byte `0x21`
- **Channel 2**: Use destination byte `0x22`
- **Channel 3**: Use destination byte `0x23`
- **All channels**: Use destination byte `0x11`

**Important**: Although the BBD203 has three channels, each channel operates as an independent single-channel controller. In the data packet's channel identifier field, always use Channel 1 (0x01), and specify the physical channel using the destination byte in the header.

### 2.3 Data Types

| Type | Size | Description |
|------|------|-------------|
| char | 1 byte | 8-bit signed integer |
| short | 2 bytes | 16-bit signed integer |
| long | 4 bytes | 32-bit signed integer |
| word | 2 bytes | 16-bit unsigned integer |
| dword | 4 bytes | 32-bit unsigned integer |

All multi-byte values are transmitted in little-endian format.

---

## 3. BBD203 Specifications

### 3.1 Encoder and Position Scaling

For BBD203 controllers, position and velocity values are scaled based on encoder counts. The scaling depends on your specific motor and stage combination.

#### Position Scaling
```
POSAPT = EncCnt × Pos
```
Where:
- `POSAPT` = Position value to send/receive via APT protocol
- `EncCnt` = Encoder counts per unit (e.g., counts per mm)
- `Pos` = Actual position in real units

#### Velocity Scaling
```
VELAPT = EncCnt × T × 65536 × Vel
```
Where:
- `VELAPT` = Velocity value to send/receive via APT protocol
- `EncCnt` = Encoder counts per unit
- `T` = 102.4 × 10⁻⁶
- `Vel` = Actual velocity in real units per second

#### Acceleration Scaling
```
ACCAPT = EncCnt × T² × 65536 × Acc
```
Where:
- `ACCAPT` = Acceleration value to send/receive via APT protocol
- `EncCnt` = Encoder counts per unit
- `T` = 102.4 × 10⁻⁶
- `Acc` = Actual acceleration in real units per second²

### 3.2 Example Scaling Values

For a stage with 20,000 encoder counts per mm:

| Parameter | Real Value | APT Value |
|-----------|------------|-----------|
| Position | 10 mm | 200,000 |
| Position | 50 mm | 1,000,000 |
| Velocity | 1 mm/s | 134.218 |
| Acceleration | 1 mm/s² | 0.0137 |

---

## 4. Message Format

### 4.1 Message Categories

Messages are organized into the following categories:

- **MOD** - Module control messages (identify, enable/disable)
- **HW** - Hardware information and control
- **MOT** - Motor control messages (move, velocity, position)
- **RACK** - Rack and bay status messages

### 4.2 Message Direction

- **SET** - Host sends command with parameters to controller
- **REQ