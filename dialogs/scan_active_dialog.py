"""
Scan Active Dialog
Displays real-time scanning progress and status
"""

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QTimer


class ScanActiveDialog(QDialog):
    """Dialog for displaying active scan progress"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load UI file
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'nuescan_scan_active_dialog.ui'
        )
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Scan in Progress")

        # Make dialog modal
        self.setModal(True)

        # Initialize state
        self.scan_cancelled = False

        # Connect signals
        self._connect_signals()

        # Initialize progress
        self._initialize_progress()

        # Demo timer (for testing progress updates)
        self._demo_timer = QTimer()
        self._demo_timer.timeout.connect(self._demo_update)
        self._demo_progress = 0

    def _connect_signals(self):
        """Connect dialog signals"""
        self.pb_cancel_scan.clicked.connect(self.on_cancel_clicked)

    def _initialize_progress(self):
        """Initialize progress bars and status"""
        self.pbar_total_scan.setValue(0)
        self.pbar_this_scan.setValue(0)
        self.l_status_current_scan.setText("1")
        self.l_status_total_scans.setText("1")
        self.l_status_current_row.setText("0")
        self.l_status_total_rows.setText("0")
        self.l_est_time_done.setText("Calculating...")

    def on_cancel_clicked(self):
        """Handle cancel button click"""
        print("DEBUG: Scan cancelled by user")
        self.scan_cancelled = True
        self.reject()

    # ==================== Progress Update Methods ====================

    def update_total_progress(self, current, total):
        """
        Update the total scan progress bar

        Args:
            current (int): Current scan number
            total (int): Total number of scans
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.pbar_total_scan.setValue(percentage)

    def update_current_scan_progress(self, current, total):
        """
        Update the current scan progress bar

        Args:
            current (int): Current row number
            total (int): Total number of rows
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.pbar_this_scan.setValue(percentage)

    def update_status(self, scan_num, total_scans, row_num, total_rows, time_remaining):
        """
        Update scan status information

        Args:
            scan_num (int): Current scan number
            total_scans (int): Total number of scans
            row_num (int): Current row number
            total_rows (int): Total number of rows
            time_remaining (str): Estimated time remaining (formatted string)
        """
        self.l_status_current_scan.setText(str(scan_num))
        self.l_status_total_scans.setText(str(total_scans))
        self.l_status_current_row.setText(str(row_num))
        self.l_status_total_rows.setText(str(total_rows))
        self.l_est_time_done.setText(f"{time_remaining} remaining...")

    def start_demo_progress(self):
        """
        Start a demo progress animation (for testing)
        Remove this method in production
        """
        self._demo_progress = 0
        self._demo_timer.start(100)  # Update every 100ms

    def _demo_update(self):
        """
        Demo progress update (for testing)
        Remove this method in production
        """
        self._demo_progress += 1

        # Simulate scan progress
        total_scans = 5
        rows_per_scan = 100
        total_steps = total_scans * rows_per_scan

        current_scan = (self._demo_progress // rows_per_scan) + 1
        current_row = (self._demo_progress % rows_per_scan)

        if current_scan > total_scans:
            self._demo_timer.stop()
            self.accept()
            return

        # Update progress
        self.update_total_progress(current_scan - 1, total_scans)
        self.update_current_scan_progress(current_row, rows_per_scan)

        # Calculate time remaining (demo)
        remaining_steps = total_steps - self._demo_progress
        seconds_remaining = remaining_steps * 0.1  # 0.1s per step
        hours = int(seconds_remaining // 3600)
        minutes = int((seconds_remaining % 3600) // 60)
        seconds = int(seconds_remaining % 60)

        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        self.update_status(
            current_scan,
            total_scans,
            current_row,
            rows_per_scan,
            time_str
        )

    def is_cancelled(self):
        """
        Check if scan was cancelled

        Returns:
            bool: True if cancelled, False otherwise
        """
        return self.scan_cancelled
