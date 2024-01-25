#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for deploying CDB web portal
# Deployment configuration can be set in etc/$LOGR_DB_NAME.deploy.conf file
#
# Usage:
#
# $0 [LOGR_DB_NAME] [MODE]
#
# Options for mode include: Dev

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
deployConfigFile=$LOGR_INSTALL_DIR/etc/${LOGR_DB_NAME}.deploy.conf
if [ -f $deployConfigFile ]; then
    echo "Using deployment config file: $deployConfigFile"
    . $deployConfigFile
else
    echo "Deployment config file $deployConfigFile not found, using defaults"
fi

LOGR_HOST_ARCH=$(uname -sm | tr -s '[:upper:][:blank:]' '[:lower:][\-]')
LOGR_CONTEXT_ROOT=${LOGR_CONTEXT_ROOT:=bely}
LOGR_PERM_CONTEXT_ROOT_URL=${LOGR_PERM_CONTEXT_ROOT_URL:=http://localhost:8080/logr}
LOGR_DATA_DIR=${LOGR_DATA_DIR:=/logr}
GLASSFISH_DIR=$LOGR_SUPPORT_DIR/payara/$LOGR_HOST_ARCH
LOGR_DIST_DIR=$LOGR_ROOT_DIR/src/java/LogrPortal/dist
LOGR_BUILD_WAR_FILE=LogrPortal.war
LOGR_WAR_FILE=$LOGR_CONTEXT_ROOT.war
JAVA_HOME=$LOGR_SUPPORT_DIR/java/$LOGR_HOST_ARCH
LOGR_WEB_SERVICE_HOST=`hostname -f`
LOGR_DATE=`date +%Y.%m.%d`

LOGR_REPOSITORY_URL=https://github.com/AdvancedPhotonSource/ComponentDB
LOGR_REPOSITORY_MILESTONES_PATH=/milestones
LOGR_REPOSITORY_RELEASES_PATH=/releases

LOGR_REPOSITORY_FULL_URL="$LOGR_REPOSITORY_URL$LOGR_REPOSITORY_MILESTONES_PATH"

if [ ! -z $2 ]; then
    DEPLOY_MODE=$2
    if [ $DEPLOY_MODE = "Dev" ]; then
        LOGR_SOFTWARE_VERSION="Development Snapshot"
    fi
fi

if [[ -z $LOGR_SOFTWARE_VERSION ]]; then
    LOGR_SOFTWARE_VERSION=`cat $LOGR_ROOT_DIR/etc/version`
    LOGR_REPOSITORY_FULL_URL="$LOGR_REPOSITORY_URL$LOGR_REPOSITORY_RELEASES_PATH"
fi

if [ ! -f $LOGR_DIST_DIR/$LOGR_BUILD_WAR_FILE ]; then
    echo "$LOGR_BUILD_WAR_FILE not found in $LOGR_DIST_DIR."
    exit 1
fi

# Create needed data directories
mkdir -p $LOGR_DATA_DIR/propertyValue
mkdir -p $LOGR_DATA_DIR/log

# Modify war file for proper settings and repackage it into new war
echo "Repackaging war file for context root $LOGR_CONTEXT_ROOT"
cd $LOGR_DIST_DIR
rm -rf $LOGR_CONTEXT_ROOT
mkdir -p $LOGR_CONTEXT_ROOT
cd $LOGR_CONTEXT_ROOT
jar xf ../$LOGR_BUILD_WAR_FILE

configFile=WEB-INF/glassfish-web.xml
cmd="cat $configFile | sed 's?<context-root.*?<context-root>${LOGR_CONTEXT_ROOT}</context-root>?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

webConfigFile=WEB-INF/web.xml
cmd="cat $webConfigFile.template | sed 's?LOGR_PROJECT_STAGE?Production?g' > $webConfigFile"
eval $cmd

cmd="cat $configFile | sed 's?dir=.*\"?dir=${LOGR_DATA_DIR}\"?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

configFile=WEB-INF/classes/META-INF/persistence.xml
cmd="cat $configFile | sed 's?<jta-data-source.*?<jta-data-source>${LOGR_DB_NAME}_DataSource</jta-data-source>?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

configFile=WEB-INF/classes/cdb.portal.properties
cmd="cat $configFile | sed 's?storageDirectory=.*?storageDirectory=${LOGR_DATA_DIR}?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd
cmd="cat $configFile | sed 's?cdb.webService.url=.*?cdb.webService.url=https://${LOGR_WEB_SERVICE_HOST}:${LOGR_WEB_SERVICE_PORT}/cdb?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd
cmd="cat $configFile | sed 's?cdb.permanentContextRoot.url=.*?cdb.permanentContextRoot.url=${LOGR_PERM_CONTEXT_ROOT_URL}?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

LOGR_LDAP_LOOKUP_FILTER=`echo ${LOGR_LDAP_LOOKUP_FILTER/&/\\\&}`

cmd="cat $configFile \
     | sed 's?LOGR_LDAP_AUTH_SERVER_URL?$LOGR_LDAP_AUTH_SERVER_URL?g' \
     | sed 's?LOGR_LDAP_AUTH_DN_FORMAT?$LOGR_LDAP_AUTH_DN_FORMAT?g' \
     | sed 's?LOGR_LDAP_SERVICE_DN?$LOGR_LDAP_SERVICE_DN?g' \
     | sed 's?LOGR_LDAP_SERVICE_PASS?$LOGR_LDAP_SERVICE_PASS?g' \
     | sed 's?LOGR_LDAP_LOOKUP_FILTER?$LOGR_LDAP_LOOKUP_FILTER?g' \
     > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

configFile=WEB-INF/classes/resources.properties
cmd="cat $configFile | sed 's?CdbPortalTitle=.*?CdbPortalTitle=${LOGR_PORTAL_TITLE}?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd
cmd="cat $configFile | sed 's?CdbSoftwareVersion=.*?CdbSoftwareVersion=${LOGR_SOFTWARE_VERSION} ($LOGR_DATE)?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

cmd="cat $configFile | sed 's?CdbSoftwareVersionUrl=.*?CdbSoftwareVersionUrl=${LOGR_REPOSITORY_FULL_URL}?g' > $configFile.2 && mv $configFile.2 $configFile"
eval $cmd

for cssFile in portal; do
    configFile=resources/css/$cssFile.css
    cmd="cat $configFile | sed 's?color:.*LOGR_CSS_PORTAL_TITLE_COLOR.*?color: ${LOGR_CSS_PORTAL_TITLE_COLOR};?g' > $configFile.2 && mv $configFile.2 $configFile"
    eval $cmd
done

jar cf ../$LOGR_WAR_FILE *

export AS_JAVA=$JAVA_HOME
ASADMIN_CMD=$GLASSFISH_DIR/bin/asadmin

echo "Attempting to undeploy application"
$ASADMIN_CMD undeploy $LOGR_CONTEXT_ROOT
echo "Attempting to deploy application"
$ASADMIN_CMD deploy $LOGR_DIST_DIR/$LOGR_WAR_FILE
