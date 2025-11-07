#!/usr/bin/env python3
"""
Test script for stage settings functionality
Verifies save/load operations without requiring actual hardware

Copyright (C) 2025 Thomas Ales
Licensed under GNU General Public License v2.0
"""

import os
import tempfile
import json
from hardware.stage_settings import StageSettings
from hardware.bbd203_protocol import TriggerMode


def test_settings_save_load():
    """Test saving and loading settings"""
    print("Testing settings save/load...")

    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name

    try:
        # Create settings instance
        settings = StageSettings(temp_file)

        # Modify settings
        print("  Setting velocity values...")
        settings.set_all_velocities(2.0, 3.0, 1.5)

        print("  Setting acceleration values...")
        settings.set_all_accelerations(10.0, 15.0, 8.0)

        print("  Setting trigger configuration...")
        settings.set_trigger_config('x_axis', TriggerMode.OUT_POSITION,
                                   polarity=0x01, start_pos_fwd=10.0, interval_fwd=2.0)

        # Save settings
        print("  Saving settings...")
        if not settings.save():
            print("ERROR: Failed to save settings")
            return False

        # Verify file was created
        if not os.path.exists(temp_file):
            print("ERROR: Settings file was not created")
            return False

        print("  Settings file created successfully")

        # Load settings into new instance
        print("  Loading settings into new instance...")
        settings2 = StageSettings(temp_file)

        # Verify loaded values
        print("  Verifying loaded values...")
        velocities = settings2.get_all_velocities()
        if velocities['x_axis'] != 2.0 or velocities['y_axis'] != 3.0 or velocities['z_axis'] != 1.5:
            print(f"ERROR: Velocity mismatch: {velocities}")
            return False

        accelerations = settings2.get_all_accelerations()
        if accelerations['x_axis'] != 10.0 or accelerations['y_axis'] != 15.0 or accelerations['z_axis'] != 8.0:
            print(f"ERROR: Acceleration mismatch: {accelerations}")
            return False

        trigger = settings2.get_trigger_config('x_axis')
        if trigger['mode'] != TriggerMode.OUT_POSITION:
            print(f"ERROR: Trigger mode mismatch: {trigger['mode']}")
            return False

        print("  All values verified successfully")

        # Print settings file content for inspection
        print("\n  Settings file content:")
        with open(temp_file, 'r') as f:
            content = json.load(f)
            print(json.dumps(content, indent=2))

        print("\nSettings save/load test: PASSED")
        return True

    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_default_settings():
    """Test default settings"""
    print("\nTesting default settings...")

    # Create temporary file that doesn't exist
    temp_file = tempfile.mktemp(suffix='.json')

    try:
        # Create settings instance (file doesn't exist, should use defaults)
        settings = StageSettings(temp_file)

        # Verify defaults
        velocities = settings.get_all_velocities()
        if velocities['x_axis'] != 1.0 or velocities['y_axis'] != 1.0 or velocities['z_axis'] != 1.0:
            print(f"ERROR: Default velocity mismatch: {velocities}")
            return False

        accelerations = settings.get_all_accelerations()
        if accelerations['x_axis'] != 5.0 or accelerations['y_axis'] != 5.0 or accelerations['z_axis'] != 5.0:
            print(f"ERROR: Default acceleration mismatch: {accelerations}")
            return False

        trigger = settings.get_trigger_config('x_axis')
        if trigger['mode'] != 0x00:  # Disabled
            print(f"ERROR: Default trigger mode mismatch: {trigger['mode']}")
            return False

        print("Default settings test: PASSED")
        return True

    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_individual_setters():
    """Test individual setter methods"""
    print("\nTesting individual setter methods...")

    temp_file = tempfile.mktemp(suffix='.json')

    try:
        settings = StageSettings(temp_file)

        # Test individual velocity setter
        settings.set_velocity('x_axis', 2.5)
        if settings.get_velocity('x_axis') != 2.5:
            print("ERROR: set_velocity failed")
            return False

        # Test individual acceleration setter
        settings.set_acceleration('y_axis', 12.0)
        if settings.get_acceleration('y_axis') != 12.0:
            print("ERROR: set_acceleration failed")
            return False

        # Test trigger mode setter
        settings.set_trigger_mode('z_axis', TriggerMode.OUT_ONLY)
        if settings.get_trigger_mode('z_axis') != TriggerMode.OUT_ONLY:
            print("ERROR: set_trigger_mode failed")
            return False

        # Test digital outputs
        settings.set_digital_outputs(0x55)
        if settings.get_digital_outputs() != 0x55:
            print("ERROR: set_digital_outputs failed")
            return False

        print("Individual setters test: PASSED")
        return True

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Run all tests"""
    print("=" * 60)
    print("Stage Settings Test Suite")
    print("=" * 60)

    tests = [
        test_default_settings,
        test_individual_setters,
        test_settings_save_load,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
