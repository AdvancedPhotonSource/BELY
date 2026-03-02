"""Test script for conda package."""

import sys
import subprocess

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        import bely_mqtt
        print(f"✓ bely_mqtt version: {bely_mqtt.__version__}")
        
        from bely_mqtt import MQTTHandler, BelyMQTTClient, PluginManager
        print("✓ Core classes imported")
        
        from bely_mqtt.models import (
            LogEntryAddEvent, 
            LogEntryUpdateEvent,
            MQTTMessage
        )
        print("✓ Event models imported")
        
        from bely_mqtt.events import EventType
        print("✓ Event types imported")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    return True

def test_cli():
    """Test CLI commands."""
    print("\nTesting CLI...")
    
    # Test help command
    result = subprocess.run(
        [sys.executable, "-m", "bely_mqtt.cli", "--help"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ CLI help failed: {result.stderr}")
        return False
    print("✓ CLI help works")
    
    # Test version command
    result = subprocess.run(
        [sys.executable, "-m", "bely_mqtt.cli", "--version"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ CLI version failed: {result.stderr}")
        return False
    print(f"✓ CLI version: {result.stdout.strip()}")
    
    return True

def main():
    """Run all tests."""
    print("Running conda package tests...\n")
    
    tests_passed = True
    
    if not test_imports():
        tests_passed = False
    
    if not test_cli():
        tests_passed = False
    
    if tests_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())