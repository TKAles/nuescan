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
    QSpinBox, QDoubleSpinBox, QCheckBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from hardware.thorlabs_stage import ThorLabsStage


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

        # Control sections in horizontal layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.create_homing_group())
        controls_layout.addWidget(self.create_motion_group())
        main_layout.addLayout(controls_layout)

        # Status section
        main_layout.addWidget(self.create_status_group())

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
