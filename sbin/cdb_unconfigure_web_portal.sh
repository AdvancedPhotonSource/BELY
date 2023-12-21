#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for un-configuring CDB webapp
# Deployment configuration can be set in etc/$LOGR_DB_NAME.deploy.conf file
#
# Usage:
#
# $0 [LOGR_DB_NAME]
#

MY_DIR=`dirname $0` && cd $MY_DIR && MY_DIR=`pwd`
if [ -z "${LOGR_ROOT_DIR}" ]; then
    LOGR_ROOT_DIR=$MY_DIR/..
fi
LOGR_ENV_FILE=${LOGR_ROOT_DIR}/setup.sh
if [ ! -f ${LOGR_ENV_FILE} ]; then
    echo "Environment file ${LOGR_ENV_FILE} does not exist."
    exit 2
fi
. ${LOGR_ENV_FILE} > /dev/null

# Use first argument as db name, if provided
LOGR_DB_NAME=${LOGR_DB_NAME:=logr}
if [ ! -z "$1" ]; then
    LOGR_DB_NAME=$1
fi
echo "Using DB name: $LOGR_DB_NAME"

LOGR_INSTALL_DIR=${LOGR_INSTALL_DIR:=$LOGR_ROOT_DIR/..}

# Look for deployment file in etc directory, and use it to override
# default entries
deployConfigFile=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.deploy.conf
if [ -f $deployConfigFile ]; then
    echo "Using deployment config file: $deployConfigFile"
    . $deployConfigFile
else
    echo "Deployment config file $deployConfigFile not found, using defaults"
fi

LOGR_HOST_ARCH=$(uname -sm | tr -s '[:upper:][:blank:]' '[:lower:][\-]')
GLASSFISH_DIR=$LOGR_SUPPORT_DIR/payara/$LOGR_HOST_ARCH
JAVA_HOME=$LOGR_SUPPORT_DIR/java/$LOGR_HOST_ARCH

export AS_JAVA=$JAVA_HOME
ASADMIN_CMD=$GLASSFISH_DIR/bin/asadmin

LOGR_DB_POOL=mysql_${LOGR_DB_NAME}_DbPool
LOGR_DATA_SOURCE=${LOGR_DB_NAME}_DataSource
LOGR_DOMAIN=production

# restart server
echo "Restarting glassfish"
$ASADMIN_CMD stop-domain ${LOGR_DOMAIN}
$ASADMIN_CMD start-domain ${LOGR_DOMAIN}

# delete JDBC resource associated with this connection pool
echo "Deleting JDBC resource $LOGR_DATA_SOURCE"
$ASADMIN_CMD delete-jdbc-resource ${LOGR_DATA_SOURCE}

# delete JDBC connection pool
echo "Deleting JDBC connection pool $LOGR_DB_POOL"
$ASADMIN_CMD delete-jdbc-connection-pool ${LOGR_DB_POOL}
