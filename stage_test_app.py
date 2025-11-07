#!/usr/bin/env python3
"""
ThorLabs Stage Test Application
Qt6-based GUI for testing and verifying the BBD203/MLS stage driver functionality

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGridLayout, QMessageBox, QTabWidget
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from hardware.thorlabs_stage import ThorLabsStage
from hardware.bbd203_protocol import TriggerMode


class StageTestWindow(QMainWindow):
    """Main window for stage testing application"""

    def __init__(self):
        super().__init__()
        self.stage = ThorLabsStage()
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)

        self.init_ui()
        self.refresh_devices()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ThorLabs Stage Test Application")
        self.setGeometry(100, 100, 900, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("ThorLabs BBD203/MLS Stage Driver Test")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Connection section
        main_layout.addWidget(self.create_connection_group())

        # Tabbed interface for different sections
        tab_widget = QTabWidget()

        # Control tab
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.create_homing_group())
        controls_layout.addWidget(self.create_motion_group())
        control_layout.addLayout(controls_layout)

        control_layout.addWidget(self.create_status_group())

        tab_widget.addTab(control_widget, "Control")

        # Settings tab
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.addWidget(self.create_settings_group())
        tab_widget.addTab(settings_widget, "Settings")

        main_layout.addWidget(tab_widget)

        # Log section
        main_layout.addWidget(self.create_log_group())

        # Start status updates
        self.status_timer.start(200)  # Update every 200ms

    def create_connection_group(self) -> QGroupBox:
        """Create connection control group"""
        group = QGroupBox("Connection")
        layout = QGridLayout()

        # Device selection
        layout.addWidget(QLabel("Device:"), 0, 0)
        self.device_combo = QComboBox()
        layout.addWidget(self.device_combo, 0, 1, 1, 2)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(self.refresh_btn, 0, 3)

        # Serial number entry
        layout.addWidget(QLabel("Serial Number:"), 1, 0)
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("e.g., 83123456")
        layout.addWidget(self.serial_edit, 1, 1, 1, 2)

        # Baudrate
        layout.addWidget(QLabel("Baudrate:"), 2, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["115200", "9600", "19200", "38400", "57600"])
        self.baudrate_combo.setCurrentText("115200")
        layout.addWidget(self.baudrate_combo, 2, 1)

        # Connect/Disconnect buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_stage)
        layout.addWidget(self.connect_btn, 2, 2)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_stage)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn, 2, 3)

        # Identify button
        self.identify_btn = QPushButton("Identify (Flash LEDs)")
        self.identify_btn.clicked.connect(self.identify_stage)
        self.identify_btn.setEnabled(False)
        layout.addWidget(self.identify_btn, 3, 0, 1, 4)

        group.setLayout(layout)
        return group

    def create_homing_group(self) -> QGroupBox:
        """Create homing control group"""
        group = QGroupBox("Homing")
        layout = QVBoxLayout()

        # Home all button
        self.home_all_btn = QPushButton("Home All Axes")
        self.home_all_btn.clicked.connect(self.home_all)
        self.home_all_btn.setEnabled(False)
        layout.addWidget(self.home_all_btn)

        # Individual axis homing
        axis_layout = QHBoxLayout()

        self.home_x_btn = QPushButton("Home X")
        self.home_x_btn.clicked.connect(lambda: self.home_axis('X'))
        self.home_x_btn.setEnabled(False)
        axis_layout.addWidget(self.home_x_btn)

        self.home_y_btn = QPushButton("Home Y")
        self.home_y_btn.clicked.connect(lambda: self.home_axis('Y'))
        self.home_y_btn.setEnabled(False)
        axis_layout.addWidget(self.home_y_btn)

        self.home_z_btn = QPushButton("Home Z")
        self.home_z_btn.clicked.connect(lambda: self.home_axis('Z'))
        self.home_z_btn.setEnabled(False)
        axis_layout.addWidget(self.home_z_btn)

        layout.addLayout(axis_layout)

        group.setLayout(layout)
        return group

    def create_motion_group(self) -> QGroupBox:
        """Create motion control group"""
        group = QGroupBox("Motion Control")
        layout = QGridLayout()

        # Absolute move controls
        layout.addWidget(QLabel("Absolute Move (mm):"), 0, 0, 1, 3)

        layout.addWidget(QLabel("X:"), 1, 0)
        self.abs_x_spin = QDoubleSpinBox()
        self.abs_x_spin.setRange(-100, 100)
        self.abs_x_spin.setDecimals(3)
        self.abs_x_spin.setSingleStep(0.1)
        layout.addWidget(self.abs_x_spin, 1, 1)

        layout.addWidget(QLabel("Y:"), 2, 0)
        self.abs_y_spin = QDoubleSpinBox()
        self.abs_y_spin.setRange(-100, 100)
        self.abs_y_spin.setDecimals(3)
        self.abs_y_spin.setSingleStep(0.1)
        layout.addWidget(self.abs_y_spin, 2, 1)

        layout.addWidget(QLabel("Z:"), 3, 0)
        self.abs_z_spin = QDoubleSpinBox()
        self.abs_z_spin.setRange(-100, 100)
        self.abs_z_spin.setDecimals(3)
        self.abs_z_spin.setSingleStep(0.1)
        layout.addWidget(self.abs_z_spin, 3, 1)

        self.move_abs_btn = QPushButton("Move Absolute")
        self.move_abs_btn.clicked.connect(self.move_absolute)
        self.move_abs_btn.setEnabled(False)
        layout.addWidget(self.move_abs_btn, 4, 0, 1, 2)

        # Relative move controls
        layout.addWidget(QLabel("Relative Move (mm):"), 5, 0, 1, 3)

        layout.addWidget(QLabel("dX:"), 6, 0)
        self.rel_x_spin = QDoubleSpinBox()
        self.rel_x_spin.setRange(-10, 10)
        self.rel_x_spin.setDecimals(3)
        self.rel_x_spin.setSingleStep(0.1)
        layout.addWidget(self.rel_x_spin, 6, 1)

        layout.addWidget(QLabel("dY:"), 7, 0)
        self.rel_y_spin = QDoubleSpinBox()
        self.rel_y_spin.setRange(-10, 10)
        self.rel_y_spin.setDecimals(3)
        self.rel_y_spin.setSingleStep(0.1)
        layout.addWidget(self.rel_y_spin, 7, 1)

        layout.addWidget(QLabel("dZ:"), 8, 0)
        self.rel_z_spin = QDoubleSpinBox()
        self.rel_z_spin.setRange(-10, 10)
        self.rel_z_spin.setDecimals(3)
        self.rel_z_spin.setSingleStep(0.1)
        layout.addWidget(self.rel_z_spin, 8, 1)

        self.move_rel_btn = QPushButton("Move Relative")
        self.move_rel_btn.clicked.connect(self.move_relative)
        self.move_rel_btn.setEnabled(False)
        layout.addWidget(self.move_rel_btn, 9, 0, 1, 2)

        # Stop button
        self.stop_btn = QPushButton("STOP ALL")
        self.stop_btn.clicked.connect(self.stop_all)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        layout.addWidget(self.stop_btn, 10, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_settings_group(self) -> QGroupBox:
        """Create settings configuration group"""
        group = QGroupBox("Stage Settings")
        layout = QVBoxLayout()

        # Velocity settings
        vel_group = QGroupBox("Velocity (mm/s)")
        vel_layout = QGridLayout()

        vel_layout.addWidget(QLabel("X Axis:"), 0, 0)
        self.vel_x_spin = QDoubleSpinBox()
        self.vel_x_spin.setRange(0.01, 10.0)
        self.vel_x_spin.setDecimals(3)
        self.vel_x_spin.setSingleStep(0.1)
        self.vel_x_spin.setValue(1.0)
        vel_layout.addWidget(self.vel_x_spin, 0, 1)

        vel_layout.addWidget(QLabel("Y Axis:"), 1, 0)
        self.vel_y_spin = QDoubleSpinBox()
        self.vel_y_spin.setRange(0.01, 10.0)
        self.vel_y_spin.setDecimals(3)
        self.vel_y_spin.setSingleStep(0.1)
        self.vel_y_spin.setValue(1.0)
        vel_layout.addWidget(self.vel_y_spin, 1, 1)

        vel_layout.addWidget(QLabel("Z Axis:"), 2, 0)
        self.vel_z_spin = QDoubleSpinBox()
        self.vel_z_spin.setRange(0.01, 10.0)
        self.vel_z_spin.setDecimals(3)
        self.vel_z_spin.setSingleStep(0.1)
        self.vel_z_spin.setValue(1.0)
        vel_layout.addWidget(self.vel_z_spin, 2, 1)

        self.apply_vel_btn = QPushButton("Apply Velocity")
        self.apply_vel_btn.clicked.connect(self.apply_velocity_settings)
        self.apply_vel_btn.setEnabled(False)
        vel_layout.addWidget(self.apply_vel_btn, 3, 0, 1, 2)

        vel_group.setLayout(vel_layout)
        layout.addWidget(vel_group)

        # Acceleration settings
        accel_group = QGroupBox("Acceleration (mm/s²)")
        accel_layout = QGridLayout()

        accel_layout.addWidget(QLabel("X Axis:"), 0, 0)
        self.accel_x_spin = QDoubleSpinBox()
        self.accel_x_spin.setRange(0.1, 100.0)
        self.accel_x_spin.setDecimals(2)
        self.accel_x_spin.setSingleStep(1.0)
        self.accel_x_spin.setValue(5.0)
        accel_layout.addWidget(self.accel_x_spin, 0, 1)

        accel_layout.addWidget(QLabel("Y Axis:"), 1, 0)
        self.accel_y_spin = QDoubleSpinBox()
        self.accel_y_spin.setRange(0.1, 100.0)
        self.accel_y_spin.setDecimals(2)
        self.accel_y_spin.setSingleStep(1.0)
        self.accel_y_spin.setValue(5.0)
        accel_layout.addWidget(self.accel_y_spin, 1, 1)

        accel_layout.addWidget(QLabel("Z Axis:"), 2, 0)
        self.accel_z_spin = QDoubleSpinBox()
        self.accel_z_spin.setRange(0.1, 100.0)
        self.accel_z_spin.setDecimals(2)
        self.accel_z_spin.setSingleStep(1.0)
        self.accel_z_spin.setValue(5.0)
        accel_layout.addWidget(self.accel_z_spin, 2, 1)

        self.apply_accel_btn = QPushButton("Apply Acceleration")
        self.apply_accel_btn.clicked.connect(self.apply_acceleration_settings)
        self.apply_accel_btn.setEnabled(False)
        accel_layout.addWidget(self.apply_accel_btn, 3, 0, 1, 2)

        accel_group.setLayout(accel_layout)
        layout.addWidget(accel_group)

        # Trigger settings
        trigger_group = QGroupBox("Trigger Configuration")
        trigger_layout = QGridLayout()

        trigger_layout.addWidget(QLabel("Axis:"), 0, 0)
        self.trigger_axis_combo = QComboBox()
        self.trigger_axis_combo.addItems(["X", "Y", "Z"])
        trigger_layout.addWidget(self.trigger_axis_combo, 0, 1)

        trigger_layout.addWidget(QLabel("Mode:"), 1, 0)
        self.trigger_mode_combo = QComboBox()
        self.trigger_mode_combo.addItems([
            "Disabled",
            "In/Out Relative Move",
            "In/Out Absolute Move",
            "In/Out Home",
            "In/Out Stop",
            "Out Only",
            "Out Position"
        ])
        trigger_layout.addWidget(self.trigger_mode_combo, 1, 1)

        trigger_layout.addWidget(QLabel("Polarity:"), 2, 0)
        self.trigger_polarity_combo = QComboBox()
        self.trigger_polarity_combo.addItems(["Active High", "Active Low"])
        trigger_layout.addWidget(self.trigger_polarity_combo, 2, 1)

        self.apply_trigger_btn = QPushButton("Apply Trigger Settings")
        self.apply_trigger_btn.clicked.connect(self.apply_trigger_settings)
        self.apply_trigger_btn.setEnabled(False)
        trigger_layout.addWidget(self.apply_trigger_btn, 3, 0, 1, 2)

        trigger_group.setLayout(trigger_layout)
        layout.addWidget(trigger_group)

        # Save/Load buttons
        buttons_layout = QHBoxLayout()

        self.load_settings_btn = QPushButton("Load Settings")
        self.load_settings_btn.clicked.connect(self.load_settings)
        buttons_layout.addWidget(self.load_settings_btn)

        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.save_settings_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_settings_btn)

        layout.addLayout(buttons_layout)

        group.setLayout(layout)
        return group

    def create_status_group(self) -> QGroupBox:
        """Create status display group"""
        group = QGroupBox("Status")
        layout = QGridLayout()

        # Connection status
        layout.addWidget(QLabel("Connected:"), 0, 0)
        self.connected_label = QLabel("No")
        self.connected_label.setStyleSheet("font-weight: bold; color: red;")
        layout.addWidget(self.connected_label, 0, 1)

        # Homed status
        layout.addWidget(QLabel("X Homed:"), 1, 0)
        self.x_homed_label = QLabel("No")
        layout.addWidget(self.x_homed_label, 1, 1)

        layout.addWidget(QLabel("Y Homed:"), 2, 0)
        self.y_homed_label = QLabel("No")
        layout.addWidget(self.y_homed_label, 2, 1)

        layout.addWidget(QLabel("Z Homed:"), 3, 0)
        self.z_homed_label = QLabel("No")
        layout.addWidget(self.z_homed_label, 3, 1)

        # Position
        layout.addWidget(QLabel("X Position:"), 1, 2)
        self.x_pos_label = QLabel("0.000 mm")
        layout.addWidget(self.x_pos_label, 1, 3)

        layout.addWidget(QLabel("Y Position:"), 2, 2)
        self.y_pos_label = QLabel("0.000 mm")
        layout.addWidget(self.y_pos_label, 2, 3)

        layout.addWidget(QLabel("Z Position:"), 3, 2)
        self.z_pos_label = QLabel("0.000 mm")
        layout.addWidget(self.z_pos_label, 3, 3)

        # Ready/Moving status
        layout.addWidget(QLabel("Stage Ready:"), 4, 0)
        self.ready_label = QLabel("No")
        layout.addWidget(self.ready_label, 4, 1)

        layout.addWidget(QLabel("Moving:"), 4, 2)
        self.moving_label = QLabel("No")
        layout.addWidget(self.moving_label, 4, 3)

        group.setLayout(layout)
        return group

    def create_log_group(self) -> QGroupBox:
        """Create log display group"""
        group = QGroupBox("Log")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)

        group.setLayout(layout)
        return group

    # ==================== Connection Methods ====================

    def refresh_devices(self):
        """Refresh list of available devices"""
        self.log("Searching for ThorLabs devices...")
        devices = ThorLabsStage.list_devices()

        self.device_combo.clear()

        if devices:
            for device in devices:
                label = f"{device['serial']} - {device['port']} ({device['description']})"
                self.device_combo.addItem(label, device['serial'])
                self.log(f"Found: {label}")

            # Auto-fill serial number from first device
            if self.device_combo.count() > 0:
                self.serial_edit.setText(self.device_combo.currentData())
        else:
            self.log("No ThorLabs devices found")

    def connect_stage(self):
        """Connect to stage"""
        serial = self.serial_edit.text().strip()
        if not serial:
            self.log("ERROR: Please enter a serial number")
            return

        baudrate = int(self.baudrate_combo.currentText())

        self.log(f"Connecting to device {serial} at {baudrate} baud...")

        if self.stage.connect(serial, baudrate):
            self.log("Successfully connected to stage")
            self.connected_label.setText("Yes")
            self.connected_label.setStyleSheet("font-weight: bold; color: green;")

            # Enable controls
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.identify_btn.setEnabled(True)
            self.home_all_btn.setEnabled(True)
            self.home_x_btn.setEnabled(True)
            self.home_y_btn.setEnabled(True)
            self.home_z_btn.setEnabled(True)
            self.move_abs_btn.setEnabled(True)
            self.move_rel_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.apply_vel_btn.setEnabled(True)
            self.apply_accel_btn.setEnabled(True)
            self.apply_trigger_btn.setEnabled(True)
            self.save_settings_btn.setEnabled(True)

            # Load current settings into UI
            self.load_settings_to_ui()
        else:
            self.log("ERROR: Failed to connect to stage")

    def disconnect_stage(self):
        """Disconnect from stage"""
        self.log("Disconnecting from stage...")

        if self.stage.disconnect():
            self.log("Disconnected successfully")
            self.connected_label.setText("No")
            self.connected_label.setStyleSheet("font-weight: bold; color: red;")

            # Disable controls
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.identify_btn.setEnabled(False)
            self.home_all_btn.setEnabled(False)
            self.home_x_btn.setEnabled(False)
            self.home_y_btn.setEnabled(False)
            self.home_z_btn.setEnabled(False)
            self.move_abs_btn.setEnabled(False)
            self.move_rel_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.apply_vel_btn.setEnabled(False)
            self.apply_accel_btn.setEnabled(False)
            self.apply_trigger_btn.setEnabled(False)
            self.save_settings_btn.setEnabled(False)
        else:
            self.log("ERROR: Failed to disconnect")

    def identify_stage(self):
        """Flash LEDs to identify controller"""
        self.log("Flashing LEDs for identification...")
        if self.stage.identify():
            self.log("Identification command sent")
        else:
            self.log("ERROR: Failed to send identify command")

    # ==================== Homing Methods ====================

    def home_all(self):
        """Home all axes"""
        self.log("Homing all axes...")
        if self.stage.home_all_axes(wait=False):
            self.log("Homing started for all axes")
        else:
            self.log("ERROR: Failed to start homing")

    def home_axis(self, axis: str):
        """Home specific axis"""
        self.log(f"Homing {axis} axis...")
        if self.stage.home_axis(axis, wait=False):
            self.log(f"{axis} axis homing started")
        else:
            self.log(f"ERROR: Failed to home {axis} axis")

    # ==================== Motion Methods ====================

    def move_absolute(self):
        """Move to absolute position"""
        x = self.abs_x_spin.value()
        y = self.abs_y_spin.value()
        z = self.abs_z_spin.value()

        self.log(f"Moving to absolute position: X={x}, Y={y}, Z={z}")

        if self.stage.move_absolute(x=x, y=y, z=z, wait=False):
            self.log("Absolute move started")
        else:
            self.log("ERROR: Failed to start absolute move")

    def move_relative(self):
        """Move relative distance"""
        dx = self.rel_x_spin.value()
        dy = self.rel_y_spin.value()
        dz = self.rel_z_spin.value()

        self.log(f"Moving relative: dX={dx}, dY={dy}, dZ={dz}")

        if self.stage.move_relative(dx=dx, dy=dy, dz=dz, wait=False):
            self.log("Relative move started")
        else:
            self.log("ERROR: Failed to start relative move")

    def stop_all(self):
        """Stop all motion"""
        self.log("STOPPING ALL MOTION")
        if self.stage.stop_all(immediate=True):
            self.log("Stop command sent")
        else:
            self.log("ERROR: Failed to send stop command")

    # ==================== Status Update ====================

    def update_status(self):
        """Update status display"""
        if not self.stage.is_connected():
            return

        try:
            # Get status
            status = self.stage.get_status()
            position = self.stage.get_position()

            # Update homed status
            self.x_homed_label.setText("Yes" if status.get('x_homed') else "No")
            self.x_homed_label.setStyleSheet(
                "color: green;" if status.get('x_homed') else "color: red;"
            )

            self.y_homed_label.setText("Yes" if status.get('y_homed') else "No")
            self.y_homed_label.setStyleSheet(
                "color: green;" if status.get('y_homed') else "color: red;"
            )

            self.z_homed_label.setText("Yes" if status.get('z_homed') else "No")
            self.z_homed_label.setStyleSheet(
                "color: green;" if status.get('z_homed') else "color: red;"
            )

            # Update position
            self.x_pos_label.setText(f"{position.get('x', 0.0):.3f} mm")
            self.y_pos_label.setText(f"{position.get('y', 0.0):.3f} mm")
            self.z_pos_label.setText(f"{position.get('z', 0.0):.3f} mm")

            # Update ready/moving status
            self.ready_label.setText("Yes" if status.get('ready') else "No")
            self.ready_label.setStyleSheet(
                "color: green; font-weight: bold;" if status.get('ready')
                else "color: orange;"
            )

            self.moving_label.setText("Yes" if status.get('moving') else "No")
            self.moving_label.setStyleSheet(
                "color: orange; font-weight: bold;" if status.get('moving')
                else "color: green;"
            )

        except Exception as e:
            self.log(f"ERROR: Failed to update status: {e}")

    # ==================== Settings Methods ====================

    def load_settings_to_ui(self):
        """Load current settings from stage into UI"""
        if not self.stage.is_connected():
            return

        try:
            # Get current settings
            velocities = self.stage.settings.get_all_velocities()
            accelerations = self.stage.settings.get_all_accelerations()

            # Update velocity spinboxes
            self.vel_x_spin.setValue(velocities['x_axis'])
            self.vel_y_spin.setValue(velocities['y_axis'])
            self.vel_z_spin.setValue(velocities['z_axis'])

            # Update acceleration spinboxes
            self.accel_x_spin.setValue(accelerations['x_axis'])
            self.accel_y_spin.setValue(accelerations['y_axis'])
            self.accel_z_spin.setValue(accelerations['z_axis'])

            # Update trigger settings for X axis (default)
            trigger_config = self.stage.settings.get_trigger_config('x_axis')
            self.trigger_mode_combo.setCurrentIndex(trigger_config.get('mode', 0))

            polarity = trigger_config.get('polarity', 0x01)
            self.trigger_polarity_combo.setCurrentIndex(0 if polarity == 0x01 else 1)

            self.log("Settings loaded into UI")

        except Exception as e:
            self.log(f"ERROR: Failed to load settings to UI: {e}")

    def apply_velocity_settings(self):
        """Apply velocity settings to stage"""
        self.log("Applying velocity settings...")

        x = self.vel_x_spin.value()
        y = self.vel_y_spin.value()
        z = self.vel_z_spin.value()

        if self.stage.configure_velocity(x=x, y=y, z=z, save=False):
            self.log(f"Velocity settings applied: X={x}, Y={y}, Z={z} mm/s")
        else:
            self.log("ERROR: Failed to apply velocity settings")

    def apply_acceleration_settings(self):
        """Apply acceleration settings to stage"""
        self.log("Applying acceleration settings...")

        x = self.accel_x_spin.value()
        y = self.accel_y_spin.value()
        z = self.accel_z_spin.value()

        if self.stage.configure_acceleration(x=x, y=y, z=z, save=False):
            self.log(f"Acceleration settings applied: X={x}, Y={y}, Z={z} mm/s²")
        else:
            self.log("ERROR: Failed to apply acceleration settings")

    def apply_trigger_settings(self):
        """Apply trigger settings to stage"""
        self.log("Applying trigger settings...")

        axis = self.trigger_axis_combo.currentText()
        mode_index = self.trigger_mode_combo.currentIndex()

        # Map mode index to TriggerMode enum
        mode_map = {
            0: TriggerMode.DISABLED,
            1: TriggerMode.IN_OUT_RELATIVE_MOVE,
            2: TriggerMode.IN_OUT_ABSOLUTE_MOVE,
            3: TriggerMode.IN_OUT_HOME,
            4: TriggerMode.IN_OUT_STOP,
            5: TriggerMode.OUT_ONLY,
            6: TriggerMode.OUT_POSITION
        }
        mode = mode_map.get(mode_index, TriggerMode.DISABLED)

        # Get polarity
        polarity = 0x01 if self.trigger_polarity_combo.currentIndex() == 0 else 0x02

        if self.stage.configure_trigger(axis, mode, polarity=polarity, save=False):
            mode_name = self.trigger_mode_combo.currentText()
            pol_name = self.trigger_polarity_combo.currentText()
            self.log(f"Trigger settings applied: {axis} axis, {mode_name}, {pol_name}")
        else:
            self.log("ERROR: Failed to apply trigger settings")

    def save_settings(self):
        """Save current settings to file"""
        self.log("Saving settings to file...")

        if self.stage.save_current_settings():
            self.log("Settings saved successfully")
            QMessageBox.information(self, "Settings Saved",
                                   "Stage settings have been saved successfully.")
        else:
            self.log("ERROR: Failed to save settings")
            QMessageBox.warning(self, "Save Failed",
                               "Failed to save stage settings.")

    def load_settings(self):
        """Load settings from file"""
        self.log("Loading settings from file...")

        if self.stage.reload_settings():
            self.log("Settings loaded successfully")

            # Update UI with loaded settings
            if self.stage.is_connected():
                self.load_settings_to_ui()

            # Apply to hardware if connected
            if self.stage.is_connected():
                self.stage.apply_startup_settings()

            QMessageBox.information(self, "Settings Loaded",
                                   "Stage settings have been loaded successfully.")
        else:
            self.log("WARNING: No settings file found, using defaults")
            QMessageBox.information(self, "No Settings Found",
                                   "No settings file found. Using default values.")

    # ==================== Logging ====================

    def log(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle window close event"""
        if self.stage.is_connected():
            reply = QMessageBox.question(
                self, 'Disconnect Stage',
                'Stage is still connected. Disconnect before closing?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.stage.disconnect()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = StageTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
