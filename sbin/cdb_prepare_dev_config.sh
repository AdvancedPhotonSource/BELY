#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for preparing CDB development
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
LOGR_INSTALL_DIR=${LOGR_INSTALL_DIR:=$LOGR_ROOT_DIR/..}
LOGR_ETC_DIR=${LOGR_INSTALL_DIR}/etc
LOGR_LOG_DIR=${LOGR_INSTALL_DIR}/var/log

LOGR_DB_NAME=logr
LOGR_WEB_SERVICE_CONFIG_FILE=${LOGR_ETC_DIR}/${LOGR_DB_NAME}.conf
LOGR_WEB_SERVICE_LOG_FILE=${LOGR_LOG_DIR}/${LOGR_DB_NAME}.log
LOGR_DB_PASSWORD_FILE=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.db.passwd
read -p "Please enter a url for the LDAP server: " LOGR_LDAP_AUTH_SERVER_URL
read -p "Please enter the dn string for the LDAP server (%s is replaced with username when lookup not needed): " LOGR_LDAP_AUTH_DN_FORMAT
read -p "Please enter the lookup service dn (don't specify if no user lookup required): " LOGR_LDAP_SERVICE_DN
read -p "Please enter the lookup service password (don't specify if no user lookup required): " LOGR_LDAP_SERVICE_PASS
read -p "Please enter the user lookup filter. (%s is replaced with username; don't specify if no user lookup required): " LOGR_LDAP_LOOKUP_FILTER

LOGR_LDAP_LOOKUP_FILTER=`echo ${LOGR_LDAP_LOOKUP_FILTER/&/\\\&}`

echo "Preparing development configuration"
mkdir -p $LOGR_ETC_DIR
mkdir -p $LOGR_LOG_DIR

echo "Modifying glassfish-web config file"
portalSrcDir=$LOGR_ROOT_DIR/src/java/LogrPortal
configFile=$portalSrcDir/web/WEB-INF/glassfish-web.xml
cmd="cat $configFile.template | sed 's?LOGR_DATA_DIR?$LOGR_DATA_DIR?g' > $configFile"
eval $cmd || exit 1

echo "Modifying web config file"
webConfigFile=$portalSrcDir/web/WEB-INF/web.xml
cmd="cat $webConfigFile.template \
    | sed 's?LOGR_PROJECT_STAGE?Development?g' \
    > $webConfigFile"
eval $cmd || exit 1

echo "Modifying cdb.portal.properties config file"
portalSrcDir=$LOGR_ROOT_DIR/src/java/LogrPortal
configFile=$portalSrcDir/src/java/cdb.portal.properties
cmd="cat $configFile.template \
    | sed 's?LOGR_LDAP_AUTH_SERVER_URL?$LOGR_LDAP_AUTH_SERVER_URL?g' \
    | sed 's?LOGR_LDAP_AUTH_DN_FORMAT?$LOGR_LDAP_AUTH_DN_FORMAT?g' \
    | sed 's?LOGR_LDAP_SERVICE_DN?$LOGR_LDAP_SERVICE_DN?g' \
    | sed 's?LOGR_LDAP_SERVICE_PASS?$LOGR_LDAP_SERVICE_PASS?g' \
    | sed 's?LOGR_LDAP_LOOKUP_FILTER?$LOGR_LDAP_LOOKUP_FILTER?g' \
    | sed 's?LOGR_DATA_DIR?$LOGR_DATA_DIR?g' \
    > $configFile"
eval $cmd || exit 1

echo "Configuring glassfish db access"
if [ ! -f $LOGR_DB_PASSWORD_FILE ]; then
    echo "File $LOGR_DB_PASSWORD_FILE does not exist."
    exit 1
fi

LOGR_DB_PASSWORD=`cat $LOGR_DB_PASSWORD_FILE`
configFile=$portalSrcDir/setup/glassfish-resources.xml
cmd="cat $configFile.template | sed 's?LOGR_DB_PASSWORD?$LOGR_DB_PASSWORD?g' > $configFile"
eval $cmd || exit 1

LOGR_PORTAL_URL="http://localhost:8080/cdb"

read -p "Please enter developer email address, used for web service email notification testing (Optional): " ADMIN_EMAIL_ADDRESS

if [[ ! -z $ADMIN_EMAIL_ADDRESS ]]; then
    EMAIL_UTILITY_MODE='developmentWithEmail'
else
    EMAIL_UTILITY_MODE='development'
    ADMIN_EMAIL_ADDRESS='None'
fi

# uncomment principal authenticator
if [ ! -z $LOGR_LDAP_SERVICE_DN ]; then
    uncommentAuthenticator="sed 's?#principalAuthenticator3?principalAuthenticator3?g'"
else
    uncommentAuthenticator="sed 's?#principalAuthenticator2?principalAuthenticator2?g'"
fi

LOGR_SENDER_EMAIL_ADDRESS='cdb@cdb'
EMAIL_SUBJECT_START="[LOGR_DEV] - `hostname` : "

LOGR_LDAP_LOOKUP_FILTER=`echo ${LOGR_LDAP_LOOKUP_FILTER/&/\\\&}`

echo "Generating web service config file"
cmd="cat $LOGR_ROOT_DIR/etc/cdb-web-service.conf.template \
    | $uncommentAuthenticator \
    | sed 's?sslCaCertFile=.*??g' \
    | sed 's?sslCertFile=.*??g' \
    | sed 's?sslKeyFile=.*??g' \
    | sed 's?LOGR_INSTALL_DIR?$LOGR_INSTALL_DIR?g' \
    | sed 's?LOGR_DB_NAME?$LOGR_DB_NAME?g' \
    | sed 's?handler=TimedRotatingFileLoggingHandler.*?handler=TimedRotatingFileLoggingHandler(\"$LOGR_WEB_SERVICE_LOG_FILE\")?g' \
    | sed 's?LOGR_PORTAL_URL?$LOGR_PORTAL_URL?g' \
    | sed 's?EMAIL_UTILITY_MODE?$EMAIL_UTILITY_MODE?g' \
    | sed 's?LOGR_SENDER_EMAIL_ADDRESS?$LOGR_SENDER_EMAIL_ADDRESS?g' \
    | sed 's?ADMIN_EMAIL_ADDRESS?$ADMIN_EMAIL_ADDRESS?g' \
    | sed 's?EMAIL_SUBJECT_START?$EMAIL_SUBJECT_START?g' \
    | sed 's?LOGR_LDAP_AUTH_DN_FORMAT?$LOGR_LDAP_AUTH_DN_FORMAT?g' \
    | sed 's?LOGR_LDAP_AUTH_SERVER_URL?$LOGR_LDAP_AUTH_SERVER_URL?g' \
    | sed 's?LOGR_LDAP_SERVICE_DN?$LOGR_LDAP_SERVICE_DN?g' \
    | sed 's?LOGR_LDAP_SERVICE_PASS?$LOGR_LDAP_SERVICE_PASS?g' \
    | sed 's?LOGR_LDAP_LOOKUP_FILTER?$LOGR_LDAP_LOOKUP_FILTER?g' \
    | sed 's?LOGR_DATA_DIR?$LOGR_DATA_DIR?g'\
    > $LOGR_WEB_SERVICE_CONFIG_FILE"
eval $cmd || exit 1
#rsync -ar $LOGR_DB_PASSWORD_FILE $LOGR_ETC_DIR || exit 1

python $LOGR_ROOT_DIR/tools/developer_tools/logr_plugins/update_plugin_generated_files.py

echo "Done preparing development configuration"
