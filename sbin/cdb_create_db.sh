#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


#
# Script used for creating CDB database
# Deployment configuration can be set in etc/$LOGR_DB_NAME.deploy.conf file
#
# Usage:
#
# $0 [LOGR_DB_NAME [LOGR_DB_SCRIPTS_DIR] [ONLY_TABLES_BIT 0/1]]
#

LOGR_DB_NAME=logr
LOGR_DB_USER=logr
LOGR_DB_PASSWORD=logr
LOGR_DB_HOST=127.0.0.1
LOGR_DB_PORT=3306
LOGR_DB_ADMIN_USER=root
LOGR_DB_ADMIN_HOSTS="127.0.0.1"
LOGR_DB_ADMIN_PASSWORD=
LOGR_DB_CHARACTER_SET=utf8

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
LOGR_ETC_DIR=$LOGR_INSTALL_DIR/etc

# Use first argument as db name, if provided
if [ ! -z "$1" ]; then
    LOGR_DB_NAME=$1
    LOGR_DB_USER=$1
    LOGR_DB_PASSWORD=$1
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

# Second argument overrides directory with db population scripts
LOGR_SQL_DIR=$LOGR_ROOT_DIR/db/sql
LOGR_DB_RESTORE_DIR=$LOGR_INSTALL_DIR/db/$LOGR_DB_NAME
LOGR_DB_SCRIPTS_DIR=${LOGR_DB_SCRIPTS_DIR:=$LOGR_DB_RESTORE_DIR}
if [ ! -z "$2" ]; then
    LOGR_DB_SCRIPTS_DIR=$2
    if [ -f "$2/create_logr_tables.sql" ]; then
	LOGR_SQL_DIR=$2
    fi
fi
if [ ! -d $LOGR_DB_SCRIPTS_DIR ]; then
    echo "DB Scripts directory $LOGR_DB_SCRIPTS_DIR does not exist."
    echo "Usage: "
    echo "$0 [LOGR_DB_NAME [LOGR_DB_SCRIPTS_DIR] [ONLY_TABLES_BIT 0/1]]"
    exit 1
fi

echo "Using DB scripts directory: $LOGR_DB_SCRIPTS_DIR"

# Read password if needed
if [ -z "$LOGR_DB_ADMIN_PASSWORD" ]; then
    sttyOrig=`stty -g`
    stty -echo
    read -p "Enter DB root password: " LOGR_DB_ADMIN_PASSWORD
    stty $sttyOrig
    echo
fi


# Read user db password if needed
LOGR_DB_PASSWORD=$LOGR_DB_USER_PASSWORD
if [ -z "$LOGR_DB_USER_PASSWORD" ]; then
    LOGR_DB_PASSWD_FILE="$LOGR_INSTALL_DIR/etc/$LOGR_DB_NAME.db.passwd"
    if [ -f $LOGR_DB_PASSWD_FILE ]; then
	LOGR_DB_PASSWORD=`cat $LOGR_DB_PASSWD_FILE`
    else
	sttyOrig=`stty -g`
	stty -echo
	read -p "Enter DB password for the $LOGR_DB_USER user: " LOGR_DB_PASSWORD
	stty $sttyOrig
	echo
    fi
fi
if [ -z "$LOGR_DB_PASSWORD" ]; then
    echo "$LOGR_DB_USER user password cannot be empty."
    exit 1
fi

# Prepare mysql config if needed
mysqlConfig=mysql.conf
if [ -d $LOGR_SUPPORT_DIR/mysql ]; then
    if [ ! -f $LOGR_ETC_DIR/$mysqlConfig ]; then
        echo "Local MySQL installation exists, preparing server configuration file"
        cmd="cat $LOGR_ROOT_DIR/etc/$mysqlConfig.template \
            | sed 's?LOGR_DB_HOST?$LOGR_DB_HOST?g' \
            | sed 's?LOGR_DB_PORT?$LOGR_DB_PORT?g' \
            | sed 's?LOGR_INSTALL_DIR?$LOGR_INSTALL_DIR?g' \
            > $LOGR_ETC_DIR/$mysqlConfig
        "
        eval $cmd || exit 1
        $LOGR_ROOT_DIR/etc/init.d/cdb-mysqld restart
        echo "Setting DB root password"
        cmd="echo \"SET PASSWORD FOR 'root'@'localhost' = PASSWORD('$LOGR_DB_ADMIN_PASSWORD');\" | $LOGR_SUPPORT_DIR/mysql/$LOGR_HOST_ARCH/bin/mysql -u root -h $LOGR_DB_HOST"
        eval $cmd || exit 1
    fi
fi

mysqlCmd="mysql --port=$LOGR_DB_PORT --host=$LOGR_DB_HOST -u $LOGR_DB_ADMIN_USER"
if [ ! -z "$LOGR_DB_ADMIN_PASSWORD" ]; then
    mysqlCmd="$mysqlCmd -p$LOGR_DB_ADMIN_PASSWORD"
fi

mysqlUserCmd="mysql $LOGR_DB_NAME --port=$LOGR_DB_PORT --host=$LOGR_DB_HOST -u $LOGR_DB_USER -p$LOGR_DB_PASSWORD"

execute() {
    msg="$@"
    if [ ! -z "$LOGR_DB_ADMIN_PASSWORD" ]; then
        sedCmd="s?$LOGR_DB_ADMIN_PASSWORD?\\*\\*\\*\\*\\*\\*?g"
        echo "Executing: $@" | sed -e $sedCmd
    else
        echo "Executing: $@"
    fi
    if eval "$@"; then
	echo 'Success'
    else
	exit 1
    fi
}

# recreate db
cd $LOGR_SQL_DIR
sqlFile=/tmp/create_LOGR_db.`id -u`.sql
rm -f $sqlFile
echo "DROP DATABASE IF EXISTS $LOGR_DB_NAME;" >> $sqlFile
echo "CREATE DATABASE $LOGR_DB_NAME CHARACTER SET $LOGR_DB_CHARACTER_SET;" >> $sqlFile
for host in $LOGR_DB_ADMIN_HOSTS; do
    echo "GRANT ALL PRIVILEGES ON $LOGR_DB_NAME.* TO '$LOGR_DB_USER'@'$host'
    IDENTIFIED BY '$LOGR_DB_PASSWORD';" >> $sqlFile
done
execute "$mysqlCmd < $sqlFile"
# create db tables
mysqlCmd="$mysqlCmd -D $LOGR_DB_NAME <"
execute $mysqlCmd create_logr_tables.sql
execute $mysqlCmd create_views.sql

mysqlUserCmd="$mysqlUserCmd -D $LOGR_DB_NAME <"
execute $mysqlUserCmd create_stored_procedures.sql

# create db password file
if [ ! -d $LOGR_ETC_DIR ]; then
    mkdir -p $LOGR_ETC_DIR
fi
passwordFile=$LOGR_ETC_DIR/$LOGR_DB_NAME.db.passwd
echo $LOGR_DB_PASSWORD > $passwordFile
chmod 600 $passwordFile

if [ "$3" == "1" ]; then
    exit 0
fi

function executePopulateScripts {
    for dbTable in $1; do
        dbFile=populate_$dbTable.sql
        if [ -f $dbFile ]; then
            echo "Populating $dbTable using $dbFile script"
            execute $mysqlCmd $dbFile || exit 1
        else
            echo "$dbFile not found, skipping $dbTable update"
        fi
    done
}

STATIC_DB_SCRIPTS_DIR="$LOGR_SQL_DIR/static"
cd $CURRENT_DIR && cd $STATIC_DB_SCRIPTS_DIR
STATIC_LOGR_DB_TABLES="\
    setting_type \
    domain \    
    relationship_type_handler \
    relationship_type \
"

executePopulateScripts "$STATIC_LOGR_DB_TABLES"

# populate db
cd $CURRENT_DIR && cd $LOGR_DB_SCRIPTS_DIR
LOGR_DB_TABLES="\    
    user_info \
    user_group \
    user_user_group \
    user_group_setting \
    user_setting \
    user_session \
    entity_info \
    role_type \
    user_role \
    list \
    user_list \
    user_group_list \
    attachment \
    log_topic \
    log \
    log_attachment \
    log_level \
    system_log \
    reaction \
    log_reaction \
    item \
    item_element \
    item_element_history \
    item_element_log \
    item_element_list \
    item_category \
    item_item_category \
    item_type \
    item_item_type \
    item_category_item_type \
    item_project \
    item_item_project \
    entity_type \
    allowed_entity_type_domain \
    item_entity_type \
    allowed_child_entity_type \
    source \
    item_source \
    resource_type_category \
    resource_type \
    connector_type \
    connector \
    item_connector \
    item_resource \
    item_element_relationship \
    item_element_relationship_history \
    property_type_handler \
    property_type_category \
    property_type \
    property_type_metadata \
    allowed_property_metadata_value \
    allowed_property_value \
    allowed_entity_type \
    allowed_property_domain \
    property_value \
    property_metadata \
    property_value_history \
    property_metadata_history \
    item_connector_property \
    item_element_relationship_property \
    item_element_property \
    connector_property \
"

executePopulateScripts "$LOGR_DB_TABLES"


cd $LOGR_SQL_DIR
execute $mysqlCmd create_triggers.sql

echo "select username from user_info inner join user_user_group on user_info.id = user_user_group.user_id inner join user_group on user_group.id = user_user_group.user_group_id where user_group.name = 'LOGR_ADMIN' and user_info.password is not null;" > temporaryAdminCommand.sql

adminWithLocalPassword=`eval $mysqlCmd temporaryAdminCommand.sql`

if [ -z "$adminWithLocalPassword" ]; then
    echo "No portal admin user with a local password exists"
    read -sp "Enter password for local portal admin (username: logr): [leave blank for no local password] " LOGR_LOCAL_SYSTEM_ADMIN_PASSWORD
    echo ""
    if [ ! -z "$LOGR_LOCAL_SYSTEM_ADMIN_PASSWORD" ]; then
	adminCryptPassword=`python -c "from cdb.common.utility.cryptUtility import CryptUtility; print CryptUtility.cryptPasswordWithPbkdf2('$LOGR_LOCAL_SYSTEM_ADMIN_PASSWORD')"`
	echo "update user_info set password = '$adminCryptPassword' where username='logr'" > temporaryAdminCommand.sql
        execute $mysqlCmd temporaryAdminCommand.sql
    fi
fi

execute rm temporaryAdminCommand.sql

# cleanup
execute rm -f $sqlFile
