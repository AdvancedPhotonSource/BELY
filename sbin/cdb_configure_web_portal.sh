#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for configuring CDB webapp
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

# Look for deployment file in etc directory, and use it to override
# default entries
deployConfigFile=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.deploy.`hostname -s`.conf
if [ ! -f $deployConfigFile ]; then
    deployConfigFile=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.deploy.conf
fi

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

LOGR_DB_HOST=${LOGR_DB_HOST:=localhost}
LOGR_DB_PORT=${LOGR_DB_PORT:=3306}
LOGR_DB_USER=${LOGR_DB_USER:=logr}
LOGR_DB_POOL=mysql_${LOGR_DB_NAME}_DbPool
LOGR_DATA_SOURCE=${LOGR_DB_NAME}_DataSource
LOGR_DOMAIN=production

# Check password from file
passwordFile=$LOGR_INSTALL_DIR/etc/$LOGR_DB_NAME.db.passwd
if [ -f $passwordFile ]; then
    LOGR_DB_PASSWORD=`cat $passwordFile`
else
	LOGR_DB_PASSWORD=${LOGR_DB_PASSWORD:=logr}
fi

# copy mysql driver
echo "Copying mysql driver"
rsync -ar $LOGR_ROOT_DIR/src/java/LogrPortal/lib/mariadb-java-client-3.1.0.jar $GLASSFISH_DIR/glassfish/domains/${LOGR_DOMAIN}/lib/

# restart server
echo "Restarting glassfish"
$ASADMIN_CMD stop-domain ${LOGR_DOMAIN}
$ASADMIN_CMD start-domain ${LOGR_DOMAIN}

# create JDBC connection pool
echo "Creating JDBC connection pool $LOGR_DB_POOL"
$ASADMIN_CMD create-jdbc-connection-pool --datasourceclassname org.mariadb.jdbc.MariaDbDataSource --restype javax.sql.DataSource --property user=${LOGR_DB_USER}:password=${LOGR_DB_PASSWORD}:driverClass="org.mariadb.jdbc.Driver":portNumber=${LOGR_DB_PORT}:databaseName=${LOGR_DB_NAME}:serverName=${LOGR_DB_HOST}:url="jdbc\:mariadb\://${LOGR_DB_HOST}\:${LOGR_DB_PORT}/${LOGR_DB_NAME}?zeroDateTimeBehavior\=convertToNull" ${LOGR_DB_POOL}

# create JDBC resource associated with this connection pool
echo "Creating JDBC resource $LOGR_DATA_SOURCE"
$ASADMIN_CMD create-jdbc-resource --connectionpoolid ${LOGR_DB_POOL} ${LOGR_DATA_SOURCE}

# test the connection settings
echo "Testing connection"
$ASADMIN_CMD ping-connection-pool $LOGR_DB_POOL || exit 1
