#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script downloads builds cloud connectors. Updates the one included with the repo. 
#
# Usage:
#
# $0
#

MY_DIR=`dirname $0` && cd $MY_DIR && MY_DIR=`pwd`
if [ -z "${BELY_ROOT_DIR}" ]; then
    BELY_ROOT_DIR=$MY_DIR/..
fi
BELY_ENV_FILE=${BELY_ROOT_DIR}/setup.sh
if [ ! -f ${BELY_ENV_FILE} ]; then
    echo "Environment file ${BELY_ENV_FILE} does not exist."
    exit 2
fi
. ${BELY_ENV_FILE} > /dev/null

# Constants
CONNECTOR_URL=https://github.com/payara/Cloud-Connectors/archive/refs/tags/0.8.0.tar.gz
TARGET_FILE_NAME=mqtt-rar-0.8.0.rar
TARGET_FILE_PATH=MQTT/MQTTRAR/target
DEST_DIR="${BELY_ROOT_DIR}/src/lib"    

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd $TMP_DIR

# Download and extract connector
curl -L --progress-bar $CONNECTOR_URL -o connector.tar.gz
tar -xzf connector.tar.gz

# Find extracted directory and build
EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "Cloud-Connectors-*" | head -1)
cd $EXTRACTED_DIR

# Run maven build
mvn clean install -DskipTests

# Find and print the newly built target
TARGET_FILE="$TARGET_FILE_PATH/$TARGET_FILE_NAME"
if [ -f "$TARGET_FILE" ]; then
    echo "Found target: $TARGET_FILE"
    ls -la "$TARGET_FILE"

    # Copy to root/src/lib    
    cp "$TARGET_FILE" "$DEST_DIR/"
    echo "Copied $TARGET_FILE_NAME to $DEST_DIR"
else
    echo "Target file not found: $TMP_DIR/$TARGET_FILE"
    exit 1
fi

# Clean up temporary directory
cd $MY_DIR
rm -rf $TMP_DIR
echo "Cleaned up temporary directory: $TMP_DIR"
