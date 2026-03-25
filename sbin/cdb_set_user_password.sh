#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for setting/resetting a system user password
# Deployment configuration can be set in etc/$LOGR_DB_NAME.deploy.conf file
#
# Usage:
#
# $0 USERNAME [LOGR_DB_NAME]
#

LOGR_DB_NAME=logr
LOGR_DB_USER=logr
LOGR_DB_HOST=127.0.0.1
LOGR_DB_PORT=3306

CURRENT_DIR=`pwd`
MY_DIR=`dirname $0` && cd $MY_DIR && MY_DIR=`pwd`
cd $CURRENT_DIR

if [ -z "${LOGR_ROOT_DIR}" ]; then
    LOGR_ROOT_DIR=$MY_DIR/..
fi
LOGR_ENV_FILE=${LOGR_ROOT_DIR}/setup.sh
if [ ! -f ${LOGR_ENV_FILE} ]; then
    echo "Environment file ${LOGR_ENV_FILE} does not exist."
    exit 1
fi
. ${LOGR_ENV_FILE} > /dev/null

# First argument is the username (required)
if [ -z "$1" ]; then
    echo "Usage: $0 USERNAME [LOGR_DB_NAME]"
    exit 1
fi
USERNAME=$1

# Use second argument as db name, if provided
if [ ! -z "$2" ]; then
    LOGR_DB_NAME=$2
    LOGR_DB_USER=$2
fi
echo "Using DB name: $LOGR_DB_NAME"

# Look for deployment file in etc directory, and use it to override
# default entries
deployConfigFile=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.deploy.conf
if [ -f $deployConfigFile ]; then
    echo "Using deployment config file: $deployConfigFile"
    . $deployConfigFile
fi

# Check for database passwd file
databasePasswdFile=$LOGR_INSTALL_DIR/etc/$LOGR_DB_NAME.db.passwd
if [ -f $databasePasswdFile ]; then
    LOGR_DB_PASSWORD=`cat $databasePasswdFile`
else
    if [ -t 0 ]; then
	read -s -p "Enter MySQL $LOGR_DB_NAME password: " LOGR_DB_PASSWORD
	echo
    else
	>&2 echo "ERROR: $databasePasswdFile does not exist"
	exit 1
    fi
fi

if [ -z "$LOGR_DB_PASSWORD" ]; then
    >&2 echo "ERROR: database password is blank"
    exit 1
fi

mysqlCmd="mysql $LOGR_DB_NAME --port=$LOGR_DB_PORT --host=$LOGR_DB_HOST -u $LOGR_DB_USER -p$LOGR_DB_PASSWORD"

# Validate that the user exists
userExists=`echo "SELECT username FROM user_info WHERE username='$USERNAME';" | eval $mysqlCmd --skip-column-names 2>/dev/null`
if [ -z "$userExists" ]; then
    echo "ERROR: User '$USERNAME' not found in the $LOGR_DB_NAME database."
    exit 1
fi

# Prompt for new password
read -sp "Enter new password for user '$USERNAME': " NEW_PASSWORD
echo
read -sp "Confirm new password: " CONFIRM_PASSWORD
echo

if [ -z "$NEW_PASSWORD" ]; then
    echo "ERROR: Password cannot be blank."
    exit 1
fi

if [ "$NEW_PASSWORD" != "$CONFIRM_PASSWORD" ]; then
    echo "ERROR: Passwords do not match."
    exit 1
fi

# Hash the password using the existing Python utility
CRYPTED_PASSWORD=`python -c "from cdb.common.utility.cryptUtility import CryptUtility; print(str(CryptUtility.cryptPasswordWithPbkdf2('$NEW_PASSWORD')))"`
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to hash password."
    exit 1
fi

# Update the password in the database
echo "UPDATE user_info SET password = '$CRYPTED_PASSWORD' WHERE username = '$USERNAME';" | eval $mysqlCmd 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to update password in the database."
    exit 1
fi

echo "Password for user '$USERNAME' has been updated successfully."
