"""
nueScan - Main Window Controller
Handles all UI interactions and coordinates hardware communication

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer

# Import dialog controllers
from dialogs.genesis_dialog import GenesisDialog
from dialogs.helios_dialog import HeliosDialog
from dialogs.scan_active_dialog import ScanActiveDialog

# Import hardware controllers
from hardware.thorlabs_stage import ThorLabsStage
from hardware.t3r_device import T3RDevice
from hardware.microscope import MicroscopeController


class NueScanMainWindow(QMainWindow):
    """Main window for nueScan application"""

    def __init__(self):
        super().__init__()

        # Load UI file
        ui_path = os.path.join(os.path.dirname(__file__), 'nuescan_mainwindow.ui')
        uic.loadUi(ui_path, self)

        # Set window title
        self.setWindowTitle("nueScan - SRAS Scan Planning and Control")

        # Initialize hardware controllers
        self.thorlabs_stage = ThorLabsStage()
        self.t3r_device = T3RDevice()
        self.microscope = MicroscopeController()

        # Initialize dialogs (create on demand)
        self.genesis_dialog = None
        self.helios_dialog = None
        self.scan_active_dialog = None

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_all_status)
        self.status_timer.start(100)  # Update every 100ms

        # Connect all UI signals
        self._connect_signals()

        # Initialize UI state
        self._initialize_ui()

    def _connect_signals(self):
        """Connect all UI signals to handler methods"""

        # ===== Button Click Handlers =====
        self.btn_toggle_mls.clicked.connect(self.on_toggle_mls_clicked)
        self.btn_refresh_com.clicked.connect(self.on_refresh_com_clicked)
        self.button_connect_com.clicked.connect(self.on_connect_com_clicked)
        self.btn_show_helios_settings.clicked.connect(self.on_show_helios_settings_clicked)
        self.btn_show_genesis_settings.clicked.connect(self.on_show_genesis_settings_clicked)
        self.btn_begin_scanning.clicked.connect(self.on_begin_scanning_clicked)
        self.btn_show_oscope_settings.clicked.connect(self.on_show_oscope_settings_clicked)

        # ===== ComboBox Value Changed Handlers =====
        self.combo_com_ports.currentIndexChanged.connect(self.on_com_port_changed)
        self.cb_num_scans.currentIndexChanged.connect(self.on_num_scans_changed)
        self.cb_row_spacing.currentIndexChanged.connect(self.on_row_spacing_changed)
        self.cb_set_dc_sample_ch.currentIndexChanged.connect(self.on_dc_sample_channel_changed)
        self.cb_set_trig_channel.currentIndexChanged.connect(self.on_trigger_channel_changed)
        self.cb_set_saw_channel.currentIndexChanged.connect(self.on_saw_channel_changed)

        # ===== LineEdit Text Changed Handlers =====
        self.le_stage_serial.textChanged.connect(self.on_stage_serial_changed)
        self.le_x_start_coord.textChanged.connect(self.on_x_start_coord_changed)
        self.le_x_delta.textChanged.connect(self.on_x_delta_changed)
        self.le_y_start_coord.textChanged.connect(self.on_y_start_coord_changed)
        self.le_y_delta.textChanged.connect(self.on_y_delta_changed)
        self.le_oscope_visa_address.textChanged.connect(self.on_oscope_visa_address_changed)
        self.le_set_trigger_voltage.textChanged.connect(self.on_trigger_voltage_changed)

    def _initialize_ui(self):
        """Initialize UI with default values"""
        # Set placeholder text for stage serial
        self.le_stage_serial.setPlaceholderText("Enter BBD203 serial (e.g., 83123456)")

        # Populate combo boxes with dummy data
        self._populate_combo_boxes()

        # Refresh COM ports
        self.on_refresh_com_clicked()

    def _populate_combo_boxes(self):
        """Populate all combo boxes with initial values"""
        # Number of scans
        self.cb_num_scans.addItems([str(i) for i in range(1, 21)])

        # Row spacing options
        self.cb_row_spacing.addItems(["0.1", "0.2", "0.5", "1.0", "2.0", "5.0"])

        # Oscilloscope channels
        channels = ["CH1", "CH2", "CH3", "CH4"]
        self.cb_set_dc_sample_ch.addItems(channels)
        self.cb_set_trig_channel.addItems(channels)
        self.cb_set_saw_channel.addItems(channels)

    # ==================== Button Click Handlers ====================

    def on_toggle_mls_clicked(self):
        """Handle ThorLabs MLS stage connect/disconnect"""
        print("DEBUG: MLS toggle button clicked")
        if self.thorlabs_stage.is_connected():
            self.thorlabs_stage.disconnect()
            self.btn_toggle_mls.setText("Connect")
        else:
            serial_number = self.le_stage_serial.text().strip()
            if not serial_number:
                QMessageBox.warning(
                    self, "No Serial Number",
                    "Please enter the BBD203 serial number.\n\n"
                    "The serial number is printed on the controller label\n"
                    "(e.g., '83123456')."
                )
                return

            print(f"INFO: Attempting to connect to BBD203 serial: {serial_number}")
            success = self.thorlabs_stage.connect(serial_number)
            if success:
                self.btn_toggle_mls.setText("Disconnect")
                QMessageBox.information(
                    self, "Connected",
                    f"Successfully connected to BBD203 controller\n"
                    f"Serial: {serial_number}\n\n"
                    f"All channels enabled. Ready to home axes."
                )
            else:
                # Show available devices
                devices = self.thorlabs_stage.list_devices()
                if devices:
                    device_list = "\n".join([
                        f"  Serial: {d['serial']} ({d['description']})"
                        for d in devices
                    ])
                    msg = (f"Failed to connect to BBD203 with serial: {serial_number}\n\n"
                           f"Available ThorLabs devices:\n{device_list}")
                else:
                    msg = (f"Failed to connect to BBD203 with serial: {serial_number}\n\n"
                           f"No ThorLabs devices found.\n"
                           f"Check USB connection and driver installation.")

                QMessageBox.warning(self, "Connection Error", msg)

    def on_refresh_com_clicked(self):
        """Refresh available COM ports"""
        print("DEBUG: Refresh COM ports clicked")
        self.combo_com_ports.clear()
        ports = self.t3r_device.get_available_ports()
        self.combo_com_ports.addItems(ports)

    def on_connect_com_clicked(self):
        """Connect to selected COM port"""
        print("DEBUG: Connect COM button clicked")
        port = self.combo_com_ports.currentText()
        if port:
            success = self.t3r_device.connect(port)
            if success:
                self.button_connect_com.setText("Disconnect")
            else:
                QMessageBox.warning(self, "Connection Error", f"Failed to connect to {port}")
        else:
            QMessageBox.warning(self, "No Port Selected", "Please select a COM port")

    def on_show_helios_settings_clicked(self):
        """Show Helios settings dialog"""
        print("DEBUG: Show Helios settings clicked")
        if not self.helios_dialog:
            self.helios_dialog = HeliosDialog(self)

        if self.helios_dialog.exec():
            # User clicked OK, apply settings
            settings = self.helios_dialog.get_settings()
            self.microscope.apply_helios_settings(settings)
            print(f"DEBUG: Applied Helios settings: {settings}")

    def on_show_genesis_settings_clicked(self):
        """Show Genesis settings dialog"""
        print("DEBUG: Show Genesis settings clicked")
        if not self.genesis_dialog:
            self.genesis_dialog = GenesisDialog(self)

        if self.genesis_dialog.exec():
            # User clicked OK, apply settings
            settings = self.genesis_dialog.get_settings()
            self.microscope.apply_genesis_settings(settings)
            print(f"DEBUG: Applied Genesis settings: {settings}")

    def on_begin_scanning_clicked(self):
        """Start the scanning process"""
        print("DEBUG: Begin scanning clicked")

        # Validate that all systems are ready
        if not self._validate_scan_ready():
            return

        # Create and show scan active dialog
        if not self.scan_active_dialog:
            self.scan_active_dialog = ScanActiveDialog(self)

        # Start the scan
        self._start_scan()

        # Show progress dialog
        self.scan_active_dialog.exec()

    def on_show_oscope_settings_clicked(self):
        """Show advanced oscilloscope settings"""
        print("DEBUG: Show oscilloscope settings clicked")
        QMessageBox.information(
            self,
            "Oscilloscope Settings",
            "Advanced oscilloscope settings dialog not yet implemented"
        )

    # ==================== ComboBox Change Handlers ====================

    def on_com_port_changed(self, index):
        """Handle COM port selection change"""
        port = self.combo_com_ports.currentText()
        print(f"DEBUG: COM port changed to: {port}")
        self._recalculate_scan_parameters()

    def on_num_scans_changed(self, index):
        """Handle number of scans change"""
        num_scans = self.cb_num_scans.currentText()
        print(f"DEBUG: Number of scans changed to: {num_scans}")
        self._recalculate_scan_parameters()

    def on_row_spacing_changed(self, index):
        """Handle row spacing change"""
        spacing = self.cb_row_spacing.currentText()
        print(f"DEBUG: Row spacing changed to: {spacing}")
        self._recalculate_scan_parameters()

    def on_dc_sample_channel_changed(self, index):
        """Handle DC sample channel change"""
        channel = self.cb_set_dc_sample_ch.currentText()
        print(f"DEBUG: DC sample channel changed to: {channel}")

    def on_trigger_channel_changed(self, index):
        """Handle trigger channel change"""
        channel = self.cb_set_trig_channel.currentText()
        print(f"DEBUG: Trigger channel changed to: {channel}")

    def on_saw_channel_changed(self, index):
        """Handle SAW channel change"""
        channel = self.cb_set_saw_channel.currentText()
        print(f"DEBUG: SAW channel changed to: {channel}")

    # ==================== LineEdit Text Change Handlers ====================

    def on_stage_serial_changed(self, text):
        """Handle stage serial number change"""
        print(f"DEBUG: Stage serial changed to: {text}")

    def on_x_start_coord_changed(self, text):
        """Handle X start coordinate change"""
        print(f"DEBUG: X start coordinate changed to: {text}")
        self._recalculate_scan_parameters()

    def on_x_delta_changed(self, text):
        """Handle X delta change"""
        print(f"DEBUG: X delta changed to: {text}")
        self._recalculate_scan_parameters()

    def on_y_start_coord_changed(self, text):
        """Handle Y start coordinate change"""
        print(f"DEBUG: Y start coordinate changed to: {text}")
        self._recalculate_scan_parameters()

    def on_y_delta_changed(self, text):
        """Handle Y delta change"""
        print(f"DEBUG: Y delta changed to: {text}")
        self._recalculate_scan_parameters()

    def on_oscope_visa_address_changed(self, text):
        """Handle oscilloscope VISA address change"""
        print(f"DEBUG: Oscilloscope VISA address changed to: {text}")

    def on_trigger_voltage_changed(self, text):
        """Handle trigger voltage change"""
        print(f"DEBUG: Trigger voltage changed to: {text}")

    # ==================== Status Update Methods ====================

    def _update_all_status(self):
        """Update all status labels with current hardware states"""
        self._update_stage_status()
        self._update_t3r_status()
        self._update_microscope_status()
        self._update_transfer_system_status()

    def _update_stage_status(self):
        """Update ThorLabs stage status indicators"""
        status = self.thorlabs_stage.get_status()

        self.l_is_mls_connected.setText("Yes" if status['connected'] else "No")
        self.l_is_mls_x_home.setText("Yes" if status['x_homed'] else "No")
        self.l_is_mls_y_home.setText("Yes" if status['y_homed'] else "No")
        self.l_is_mls_ready.setText("Yes" if status['ready'] else "No")
        self.l_is_mls_scanning.setText("Yes" if status['scanning'] else "No")

    def _update_t3r_status(self):
        """Update T3R device status indicators"""
        status = self.t3r_device.get_status()

        self.l_is_t3r_connected.setText("Yes" if status['connected'] else "No")
        self.l_is_t3r_homed.setText("Yes" if status['homed'] else "No")
        self.l_is_t3r_ready.setText("Yes" if status['ready'] else "No")

    def _update_microscope_status(self):
        """Update microscope (Genesis/Helios) status indicators"""
        status = self.microscope.get_status()

        # Microscope interlocks
        self.l_is_mx_interlocked.setText("Yes" if status['interlocked'] else "No")

        # Helios status
        self.l_is_helios_ready.setText("Yes" if status['helios_ready'] else "No")
        self.l_is_helios_interlocked.setText("Yes" if status['helios_interlocked'] else "No")

        # Genesis status
        self.l_is_genesis_ready.setText("Yes" if status['genesis_ready'] else "No")
        self.l_is_genesis_interlocked.setText("Yes" if status['genesis_interlocked'] else "No")

    def _update_transfer_system_status(self):
        """Update Robo-met.3D transfer system status indicators"""
        # Stub implementation - would read from actual I/O
        # These represent digital I/O states
        io_states = self._read_transfer_io_states()

        # SRAS outputs
        self.l_sras_ok.setText("High (1)" if io_states['sras_ok'] else "Low (0)")
        self.l_sras_ctl.setText("High (1)" if io_states['sras_ctl'] else "Low (0)")
        self.l_sras_done.setText("High (1)" if io_states['sras_done'] else "Low (0)")
        self.l_sras_error.setText("High (1)" if io_states['sras_error'] else "Low (0)")

        # R3D inputs
        self.l_r3d_estop_ok.setText("High (1)" if io_states['r3d_estop'] else "Low (0)")
        self.l_r3d_rtl.setText("High (1)" if io_states['r3d_ready_to_load'] else "Low (0)")
        self.l_r3d_rts.setText("High (1)" if io_states['r3d_ready_to_start'] else "Low (0)")
        self.l_r3d_spare.setText("High (1)" if io_states['r3d_spare'] else "Low (0)")

    def _read_transfer_io_states(self):
        """
        Stub method to read transfer system I/O states
        In production, this would read from actual hardware I/O
        """
        return {
            'sras_ok': False,
            'sras_ctl': False,
            'sras_done': False,
            'sras_error': False,
            'r3d_estop': True,  # Active low, so True = OK
            'r3d_ready_to_load': False,
            'r3d_ready_to_start': False,
            'r3d_spare': False
        }

    # ==================== Scan Management Methods ====================

    def _validate_scan_ready(self):
        """Validate that all systems are ready for scanning"""
        if not self.thorlabs_stage.is_connected():
            QMessageBox.warning(self, "Not Ready", "ThorLabs stage is not connected")
            return False

        if not self.t3r_device.is_connected():
            QMessageBox.warning(self, "Not Ready", "T3R device is not connected")
            return False

        # Add more validation as needed
        return True

    def _start_scan(self):
        """Initialize and start the scanning process"""
        print("DEBUG: Starting scan process")

        # Collect scan parameters
        params = self._collect_scan_parameters()

        # Initialize hardware for scanning
        self.thorlabs_stage.prepare_for_scan(params)
        self.t3r_device.prepare_for_scan(params)
        self.microscope.prepare_for_scan(params)

        # Start the scan (would be implemented in actual hardware controllers)
        print(f"DEBUG: Scan parameters: {params}")

    def _collect_scan_parameters(self):
        """Collect all scan parameters from UI"""
        try:
            params = {
                'x_start': float(self.le_x_start_coord.text() or 0),
                'x_delta': float(self.le_x_delta.text() or 0),
                'y_start': float(self.le_y_start_coord.text() or 0),
                'y_delta': float(self.le_y_delta.text() or 0),
                'num_scans': int(self.cb_num_scans.currentText() or 1),
                'row_spacing': float(self.cb_row_spacing.currentText() or 0.1),
                'trigger_voltage': float(self.le_set_trigger_voltage.text() or 0),
                'visa_address': self.le_oscope_visa_address.text()
            }
        except ValueError:
            params = {
                'x_start': 0, 'x_delta': 0, 'y_start': 0, 'y_delta': 0,
                'num_scans': 1, 'row_spacing': 0.1, 'trigger_voltage': 0,
                'visa_address': ''
            }

        return params

    def _recalculate_scan_parameters(self):
        """Recalculate and update scan statistics"""
        params = self._collect_scan_parameters()

        # Calculate points per row (stub calculation)
        if params['x_delta'] > 0:
            points_per_row = int(abs(params['x_start']) / params['x_delta'])
        else:
            points_per_row = 0

        # Calculate rows per scan (stub calculation)
        if params['row_spacing'] > 0 and params['y_delta'] > 0:
            rows_per_scan = int(abs(params['y_delta']) / params['row_spacing'])
        else:
            rows_per_scan = 0

        # Calculate totals
        scans_in_set = params['num_scans']
        total_records = points_per_row * rows_per_scan * scans_in_set
        total_points = total_records

        # Estimate file size (1KB per point as example)
        estimated_size_gb = (total_points * 1024) / (1024 ** 3)

        # Update labels
        self.l_scan_ppr.setText(str(points_per_row))
        self.l_scan_rps.setText(str(rows_per_scan))
        self.l_scan_sis.setText(str(scans_in_set))
        self.l_scan_total_records.setText(str(total_records))
        self.l_scan_total_points.setText(str(total_points))
        self.l_scan_estimated_size.setText(f"{estimated_size_gb:.2f}GB")

        # Calculate angle spacing
        if scans_in_set > 1:
            angle_spacing = 360.0 / scans_in_set
        else:
            angle_spacing = 0
        self.l_scan_angle_spacing.setText(f"{angle_spacing:.2f}°")

    # ==================== Progress Update Methods ====================

    def update_total_progress(self, current, total):
        """
        Update total scan progress
        Called from scan control logic to update progress bar
        """
        if self.scan_active_dialog:
            self.scan_active_dialog.update_total_progress(current, total)

    def update_current_scan_progress(self, current, total):
        """
        Update current scan progress
        Called from scan control logic to update progress bar
        """
        if self.scan_active_dialog:
            self.scan_active_dialog.update_current_scan_progress(current, total)

    def update_scan_status(self, scan_num, total_scans, row_num, total_rows, time_remaining):
        """
        Update scan status information
        Called from scan control logic
        """
        if self.scan_active_dialog:
            self.scan_active_dialog.update_status(
                scan_num, total_scans, row_num, total_rows, time_remaining
            )
