#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for deploying CDB MySQL DB Server
#
# Usage:
#
# $0
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
LOGR_SHORT_HOSTNAME=`hostname -s`
LOGR_SUPPORT_DIR=${LOGR_SUPPORT_DIR:=$LOGR_INSTALL_DIR/support-$LOGR_SHORT_HOSTNAME}
LOGR_ETC_DIR=${LOGR_INSTALL_DIR}/etc
LOGR_LOG_DIR=${LOGR_INSTALL_DIR}/var/log
LOGR_MYSQLD_INIT_CMD=$LOGR_ROOT_DIR/etc/init.d/cdb-mysqld
LOGR_MYSQLD_CONFIG_FILE=$LOGR_ETC_DIR/mysql.conf

echo "CDB install directory: $LOGR_INSTALL_DIR"

mkdir -p $LOGR_ETC_DIR
mkdir -p $LOGR_LOG_DIR

echo "Checking service configuration file"
setRootPassword=false
if [ ! -f $LOGR_MYSQLD_CONFIG_FILE ]; then
    echo "Generating service config file"
    if [ -z $LOGR_DB_HOST ]; then
        LOGR_DB_HOST=127.0.0.1
        read -p "Please specify the MYSQL_DB_HOST: [$LOGR_DB_HOST]" dbHost
        if [ ! -z $dbHost ]; then
            LOGR_DB_HOST=$dbHost
        fi
    fi
    if [ -z $LOGR_DB_PORT ]; then
        LOGR_DB_PORT=3306
        read -p "Please specify the MYSQL_DB_PORT: [$LOGR_DB_PORT]" dbPort
        if [ ! -z $dbPort ]; then
            LOGR_DB_PORT=$dbPort
        fi
    fi

    cmd="cat $LOGR_ROOT_DIR/etc/mysql.conf.template \
        | sed 's?LOGR_INSTALL_DIR?$LOGR_INSTALL_DIR?g' \
        | sed 's?LOGR_DB_HOST?$LOGR_DB_HOST?g' \
        | sed 's?LOGR_DB_PORT?$LOGR_DB_PORT?g' \
        > $LOGR_MYSQLD_CONFIG_FILE"
    eval $cmd || exit 1
    setRootPassword=true
else
    echo "Service config file exists"
fi

echo "Restarting mysqld service"
$LOGR_MYSQLD_INIT_CMD restart

# TODO Update for use with latest version of mariadb.
# if [ $setRootPassword = "true" ]; then
#     if [ -z "$LOGR_DB_ADMIN_PASSWORD" ]; then
#         sttyOrig=`stty -g`
#         stty -echo
#         read -p "Enter DB root password: " LOGR_DB_ADMIN_PASSWORD
#         stty $sttyOrig
#         echo
#     fi
#     echo "Setting DB root password"
#     cmd="echo \"SET PASSWORD FOR 'root'@'localhost' = PASSWORD('$LOGR_DB_ADMIN_PASSWORD');\" | $LOGR_SUPPORT_DIR/mysql/$LOGR_HOST_ARCH/bin/mysql -u root -h $LOGR_DB_HOST -P $LOGR_DB_PORT"
#     eval $cmd || exit 1
# fi

echo "Done deploying mysqld service"
