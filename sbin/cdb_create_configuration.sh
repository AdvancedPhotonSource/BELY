#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for creation of configuration file used for logr.
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

LOGR_ETC_DIR=$LOGR_INSTALL_DIR/etc

# Look for deployment file in etc directory.
deployConfigFile=$LOGR_ETC_DIR/${LOGR_DB_NAME}.deploy.conf
if [ -f $deployConfigFile ]; then
    echo "Using deployment config file: $deployConfigFile"
    . $deployConfigFile
else
    echo "Deployment config file $deployConfigFile not found, creating new file."
    mkdir -p $LOGR_ETC_DIR
fi

# Get a DB name based on configuration file.
LOGR_DB_NAME=${LOGR_DB_NAME:=$1}
LOGR_DB_NAME=${LOGR_DB_NAME:=logr}

LOGR_DB_USER=${LOGR_DB_USER:=$LOGR_DB_NAME}
LOGR_DB_HOST=${LOGR_DB_HOST:=127.0.0.1}
LOGR_DB_PORT=${LOGR_DB_PORT:=3306}
LOGR_DB_ADMIN_USER=${LOGR_DB_ADMIN_USER:=root}
LOGR_DB_ADMIN_HOSTS=${LOGR_DB_ADMIN_HOSTS:=127.0.0.1}
LOGR_DB_CHARACTER_SET=${LOGR_DB_CHARACTER_SET:=utf8}
LOGR_DB_SCRIPTS_DIR=${LOGR_DB_SCRIPTS_DIR:=$LOGR_INSTALL_DIR/db/$LOGR_DB_NAME}
LOGR_CONTEXT_ROOT=${LOGR_CONTEXT_ROOT:=$LOGR_DB_NAME}
LOGR_DATA_DIR=${LOGR_DATA_DIR:=$LOGR_INSTALL_DIR/data/LOGR_DB_NAME}
LOGR_PORTAL_TITLE=${LOGR_PORTAL_TITLE:=Logr Portal}
LOGR_CSS_PORTAL_TITLE_COLOR=${LOGR_CSS_PORTAL_TITLE_COLOR:=#f2f4f7}
LOGR_WEB_SERVICE_PORT=${LOGR_WEB_SERVICE_PORT:=10232}
LOGR_PERM_CONTEXT_ROOT_URL=${LOGR_PERM_CONTEXT_ROOT_URL:=http://localhost:8080/logr}

read -p "DB Name [$LOGR_DB_NAME]: " userDbName
read -p "DB User [$LOGR_DB_USER]: " userDbUser
read -p "DB Host [$LOGR_DB_HOST]: " userDbHost
read -p "DB Port [$LOGR_DB_PORT]: " userDbPort
read -p "DB Admin User [$LOGR_DB_ADMIN_USER]: " userDbAdminUser
read -p "DB Admin Hosts [$LOGR_DB_ADMIN_HOSTS]: " userDbAdminHosts
read -p "DB Character Set [$LOGR_DB_CHARACTER_SET]: " userDbCharset
read -p "DB Populate Scripts Dir [$LOGR_DB_SCRIPTS_DIR]: " userDbScriptsDir
read -p "DB Data Dir [$LOGR_DATA_DIR]: " userDataDir
read -p "Context Root [$LOGR_CONTEXT_ROOT]: " userContextRoot
read -p "Portal Title [$LOGR_PORTAL_TITLE]: " userPortalTitle
read -p "Portal Title Color [$LOGR_CSS_PORTAL_TITLE_COLOR]: " userPortalTitleColor
read -p "Portal Permanent URL Context Root [$LOGR_PERM_CONTEXT_ROOT_URL]: " permanentContextRootUrl
read -p "Service Port [$LOGR_WEB_SERVICE_PORT]: " userServicePort

read -p "LDAP with user lookup? [y/N]: " ldapLookup

ldapLookup=`echo $ldapLookup | tr '[:upper:]' '[:lower:]'`

read -p "Auth LDAP server [$LOGR_LDAP_AUTH_SERVER_URL]: " userLdapServerUrl

if [ -z $ldapLookup ] || [ $ldapLookup != 'y' ]; then
	read -p "Auth LDAP dn format (use %s for username placeholder) [$LOGR_LDAP_AUTH_DN_FORMAT]: " userLdapServerDnFormat
else
	read -p "LDAP dn root for lookup [$LOGR_LDAP_AUTH_DN_FORMAT]: " userLdapServerDnFormat
	read -p "LDAP user lookup filter (use %s for username placeholder) [$LOGR_LDAP_LOOKUP_FILTER]: " userLdapLookupFilter
	read -p "Auth LDAP service account dn [$LOGR_LDAP_SERVICE_DN]: " ldapServiceDn
	echo "Auth LDAP service account password: " && read -s ldapServicePass
fi

if [ ! -z $userDbName ]; then
	LOGR_DB_NAME=$userDbName
fi
if [ ! -z $userDbUser ]; then
	LOGR_DB_USER=$userDbUser
fi
if [ ! -z $userDbHost ]; then
	LOGR_DB_HOST=$userDbHost
fi
if [ ! -z $userDbPort ]; then
	LOGR_DB_PORT=$userDbPort
fi
if [ ! -z $userDbAdminUser ]; then
	LOGR_DB_ADMIN_USER=$userDbAdminUser
fi
if [ ! -z $userDbAdminHosts ]; then
	LOGR_DB_ADMIN_HOSTS=$userDbAdminHosts
fi
if [ ! -z $userDbCharset ]; then
	LOGR_DB_CHARACTER_SET=$userDbCharset
fi
if [ ! -z $userDbScriptsDir ]; then
	LOGR_DB_SCRIPTS_DIR=$userDbScriptsDir
fi
if [ ! -z $userDataDir ]; then
	LOGR_DATA_DIR=$userDataDir
fi
if [ ! -z $userContextRoot ]; then
	LOGR_CONTEXT_ROOT=$userContextRoot
fi
if [ ! -z "$userPortalTitle" ]; then
	LOGR_PORTAL_TITLE=$userPortalTitle
fi
if [ ! -z $userPortalTitleColor ]; then
	LOGR_CSS_PORTAL_TITLE_COLOR=$userPortalTitleColor
fi
if [ ! -z $permanentContextRootUrl ]; then
	LOGR_PERM_CONTEXT_ROOT_URL=$permanentContextRootUrl
fi
if [ ! -z $userServicePort ]; then
	LOGR_WEB_SERVICE_PORT=$userServicePort
fi
if [ ! -z $userLdapServerUrl ]; then
	LOGR_LDAP_AUTH_SERVER_URL=$userLdapServerUrl
fi
if [ ! -z $userLdapServerDnFormat ]; then
	LOGR_LDAP_AUTH_DN_FORMAT=$userLdapServerDnFormat
fi
if [[ $ldapLookup == 'y' ]]; then
	if [ ! -z $userLdapLookupFilter ]; then
		LOGR_LDAP_LOOKUP_FILTER="'$userLdapLookupFilter'"
	elif [ ! -z $LOGR_LDAP_LOOKUP_FILTER ]; then
		LOGR_LDAP_LOOKUP_FILTER="'$LOGR_LDAP_LOOKUP_FILTER'"
	fi
	if [ ! -z $ldapServiceDn ]; then
		LOGR_LDAP_SERVICE_DN=$ldapServiceDn
	fi
else
	LOGR_LDAP_LOOKUP_FILTER=''
	LOGR_LDAP_SERVICE_DN=''
fi 
configContents="LOGR_DB_NAME=$LOGR_DB_NAME"
configContents="$configContents\nLOGR_DB_USER=$LOGR_DB_USER"
configContents="$configContents\nLOGR_DB_HOST=$LOGR_DB_HOST"
configContents="$configContents\nLOGR_DB_PORT=$LOGR_DB_PORT"
configContents="$configContents\nLOGR_DB_ADMIN_USER=$LOGR_DB_ADMIN_USER"
configContents="$configContents\nLOGR_DB_ADMIN_HOSTS=$LOGR_DB_ADMIN_HOSTS"
configContents="$configContents\nLOGR_DB_CHARACTER_SET=$LOGR_DB_CHARACTER_SET"
configContents="$configContents\nLOGR_DB_SCRIPTS_DIR=$LOGR_DB_SCRIPTS_DIR"
configContents="$configContents\nLOGR_DATA_DIR=$LOGR_DATA_DIR"
configContents="$configContents\nLOGR_CONTEXT_ROOT=$LOGR_CONTEXT_ROOT"
configContents="$configContents\nLOGR_PORTAL_TITLE=\"$LOGR_PORTAL_TITLE\""
configContents="$configContents\nLOGR_CSS_PORTAL_TITLE_COLOR=$LOGR_CSS_PORTAL_TITLE_COLOR"
configContents="$configContents\nLOGR_PERM_CONTEXT_ROOT_URL=$LOGR_PERM_CONTEXT_ROOT_URL"
configContents="$configContents\nLOGR_WEB_SERVICE_PORT=$LOGR_WEB_SERVICE_PORT"
configContents="$configContents\nLOGR_LDAP_AUTH_SERVER_URL=$LOGR_LDAP_AUTH_SERVER_URL"
configContents="$configContents\nLOGR_LDAP_AUTH_DN_FORMAT=$LOGR_LDAP_AUTH_DN_FORMAT"
configContents="$configContents\nLOGR_LDAP_LOOKUP_FILTER=$LOGR_LDAP_LOOKUP_FILTER"
configContents="$configContents\nLOGR_LDAP_SERVICE_DN=$LOGR_LDAP_SERVICE_DN"
configContents="$configContents\nLOGR_LDAP_SERVICE_PASS=$ldapServicePass"


echo '**************** RESULTING CONFIGURATION ****************'
echo -e $configContents
echo '*********************************************************'

echo "Saving configuration to: $deployConfigFile"
echo -e $configContents > $deployConfigFile

$LOGR_ROOT_DIR/sbin/cdb_create_configuration_openssl.sh
