#!/bin/bash
# Pre-unlink script that runs before package removal

echo "Removing BELY MQTT Framework..."

# Clean up any cached files
if [ -d "$HOME/.cache/bely-mqtt" ]; then
    echo "Cleaning cache directory..."
    rm -rf "$HOME/.cache/bely-mqtt"
fi