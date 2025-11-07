"""
ThorLabs Stage Settings Management
Handles saving and loading of stage configuration parameters

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path


class StageSettings:
    """
    Manages stage configuration settings including velocity, acceleration,
    and trigger I/O configuration
    """

    DEFAULT_SETTINGS = {
        'velocity': {
            'x_axis': 1.0,  # mm/s
            'y_axis': 1.0,  # mm/s
            'z_axis': 1.0,  # mm/s
        },
        'acceleration': {
            'x_axis': 5.0,  # mm/s²
            'y_axis': 5.0,  # mm/s²
            'z_axis': 5.0,  # mm/s²
        },
        'trigger': {
            'x_axis': {
                'mode': 0x00,  # Disabled
                'polarity': 0x01,  # Active high
                'start_pos_fwd': 0.0,
                'start_pos_rev': 0.0,
                'interval_fwd': 0.0,
                'interval_rev': 0.0
            },
            'y_axis': {
                'mode': 0x00,  # Disabled
                'polarity': 0x01,  # Active high
                'start_pos_fwd': 0.0,
                'start_pos_rev': 0.0,
                'interval_fwd': 0.0,
                'interval_rev': 0.0
            },
            'z_axis': {
                'mode': 0x00,  # Disabled
                'polarity': 0x01,  # Active high
                'start_pos_fwd': 0.0,
                'start_pos_rev': 0.0,
                'interval_fwd': 0.0,
                'interval_rev': 0.0
            }
        },
        'digital_io': {
            'output_bits': 0x00
        }
    }

    def __init__(self, settings_file: Optional[str] = None):
        """
        Initialize stage settings manager

        Args:
            settings_file: Path to settings file (default: ~/.nuescan/stage_settings.json)
        """
        if settings_file is None:
            # Default to user home directory
            home = Path.home()
            settings_dir = home / '.nuescan'
            settings_dir.mkdir(exist_ok=True)
            settings_file = str(settings_dir / 'stage_settings.json')

        self.settings_file = settings_file
        self.settings = self.DEFAULT_SETTINGS.copy()

        # Load existing settings if available
        self.load()

    def load(self) -> bool:
        """
        Load settings from file

        Returns:
            bool: True if settings loaded successfully, False otherwise
        """
        if not os.path.exists(self.settings_file):
            print(f"INFO: Settings file not found, using defaults: {self.settings_file}")
            return False

        try:
            with open(self.settings_file, 'r') as f:
                loaded_settings = json.load(f)

            # Merge with defaults to ensure all keys exist
            self._merge_settings(loaded_settings)

            print(f"INFO: Loaded stage settings from {self.settings_file}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to load settings from {self.settings_file}: {e}")
            return False

    def save(self) -> bool:
        """
        Save settings to file

        Returns:
            bool: True if settings saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)

            print(f"INFO: Saved stage settings to {self.settings_file}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save settings to {self.settings_file}: {e}")
            return False

    def _merge_settings(self, loaded_settings: Dict):
        """Merge loaded settings with defaults"""
        # Velocity
        if 'velocity' in loaded_settings:
            self.settings['velocity'].update(loaded_settings['velocity'])

        # Acceleration
        if 'acceleration' in loaded_settings:
            self.settings['acceleration'].update(loaded_settings['acceleration'])

        # Trigger
        if 'trigger' in loaded_settings:
            for axis in ['x_axis', 'y_axis', 'z_axis']:
                if axis in loaded_settings['trigger']:
                    self.settings['trigger'][axis].update(loaded_settings['trigger'][axis])

        # Digital I/O
        if 'digital_io' in loaded_settings:
            self.settings['digital_io'].update(loaded_settings['digital_io'])

    # ==================== Velocity Settings ====================

    def get_velocity(self, axis: str) -> float:
        """Get velocity for specific axis (x_axis, y_axis, z_axis)"""
        return self.settings['velocity'].get(axis, 1.0)

    def set_velocity(self, axis: str, velocity: float):
        """Set velocity for specific axis"""
        if axis in ['x_axis', 'y_axis', 'z_axis']:
            self.settings['velocity'][axis] = velocity

    def get_all_velocities(self) -> Dict[str, float]:
        """Get all axis velocities"""
        return self.settings['velocity'].copy()

    def set_all_velocities(self, x: float, y: float, z: float):
        """Set all axis velocities"""
        self.settings['velocity']['x_axis'] = x
        self.settings['velocity']['y_axis'] = y
        self.settings['velocity']['z_axis'] = z

    # ==================== Acceleration Settings ====================

    def get_acceleration(self, axis: str) -> float:
        """Get acceleration for specific axis"""
        return self.settings['acceleration'].get(axis, 5.0)

    def set_acceleration(self, axis: str, acceleration: float):
        """Set acceleration for specific axis"""
        if axis in ['x_axis', 'y_axis', 'z_axis']:
            self.settings['acceleration'][axis] = acceleration

    def get_all_accelerations(self) -> Dict[str, float]:
        """Get all axis accelerations"""
        return self.settings['acceleration'].copy()

    def set_all_accelerations(self, x: float, y: float, z: float):
        """Set all axis accelerations"""
        self.settings['acceleration']['x_axis'] = x
        self.settings['acceleration']['y_axis'] = y
        self.settings['acceleration']['z_axis'] = z

    # ==================== Trigger Settings ====================

    def get_trigger_config(self, axis: str) -> Dict:
        """Get trigger configuration for specific axis"""
        return self.settings['trigger'].get(axis, {}).copy()

    def set_trigger_config(self, axis: str, mode: int, polarity: int = 0x01,
                          start_pos_fwd: float = 0.0, start_pos_rev: float = 0.0,
                          interval_fwd: float = 0.0, interval_rev: float = 0.0):
        """Set trigger configuration for specific axis"""
        if axis in ['x_axis', 'y_axis', 'z_axis']:
            self.settings['trigger'][axis] = {
                'mode': mode,
                'polarity': polarity,
                'start_pos_fwd': start_pos_fwd,
                'start_pos_rev': start_pos_rev,
                'interval_fwd': interval_fwd,
                'interval_rev': interval_rev
            }

    def get_trigger_mode(self, axis: str) -> int:
        """Get trigger mode for specific axis"""
        return self.settings['trigger'].get(axis, {}).get('mode', 0x00)

    def set_trigger_mode(self, axis: str, mode: int):
        """Set trigger mode for specific axis"""
        if axis in ['x_axis', 'y_axis', 'z_axis']:
            if axis not in self.settings['trigger']:
                self.settings['trigger'][axis] = self.DEFAULT_SETTINGS['trigger'][axis].copy()
            self.settings['trigger'][axis]['mode'] = mode

    # ==================== Digital I/O Settings ====================

    def get_digital_outputs(self) -> int:
        """Get digital output bits"""
        return self.settings['digital_io'].get('output_bits', 0x00)

    def set_digital_outputs(self, output_bits: int):
        """Set digital output bits"""
        self.settings['digital_io']['output_bits'] = output_bits

    # ==================== Utility Methods ====================

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()

    def get_all_settings(self) -> Dict:
        """Get copy of all settings"""
        return json.loads(json.dumps(self.settings))  # Deep copy via JSON

    def update_from_dict(self, settings_dict: Dict):
        """Update settings from dictionary"""
        self._merge_settings(settings_dict)
