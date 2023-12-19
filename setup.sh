#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.


# CDB setup script for Bourne-type shells
# This file is typically sourced in user's .bashrc file

if [ -n "$BASH_SOURCE" ]; then
  input_param=$BASH_SOURCE
elif [ -n "$ZSH_VERSION" ]; then
  setopt function_argzero
  input_param=$0
else
  echo 1>&2 "Unsupported shell. Please use bash or zsh."
  exit 2
fi

myDir=`dirname $input_param`

currentDir=`pwd` && cd $myDir
if [ ! -z "$LOGR_ROOT_DIR" -a "$LOGR_ROOT_DIR" != `pwd` ]; then
    echo "WARNING: Resetting LOGR_ROOT_DIR environment variable (old value: $LOGR_ROOT_DIR)" 
fi
export LOGR_ROOT_DIR=`pwd`

if [ -z $LOGR_INSTALL_DIR ]; then
    export LOGR_INSTALL_DIR=$LOGR_ROOT_DIR/..
    if [ -d $LOGR_INSTALL_DIR ]; then
        cd $LOGR_INSTALL_DIR
        export LOGR_INSTALL_DIR=`pwd`
    fi
fi
if [ -z $LOGR_DATA_DIR ]; then
    export LOGR_DATA_DIR=$LOGR_INSTALL_DIR/data
    if [ -d $LOGR_DATA_DIR ]; then
        cd $LOGR_DATA_DIR
        export LOGR_DATA_DIR=`pwd`
    fi
fi
if [ ! -d $LOGR_DATA_DIR ]; then
    echo "WARNING: $LOGR_DATA_DIR directory does not exist. Developers should point LOGR_DATA_DIR to the desired area." 
    #unset LOGR_DATA_DIR
fi

if [ -z $LOGR_VAR_DIR ]; then
    export LOGR_VAR_DIR=$LOGR_INSTALL_DIR/var
    if [ -d $LOGR_VAR_DIR ]; then
        cd $LOGR_VAR_DIR
        export LOGR_VAR_DIR=`pwd`
    else
    	unset LOGR_VAR_DIR
    fi
fi

# Establish machine architecture and host name
LOGR_HOST_ARCH=$(uname -sm | tr -s '[:upper:][:blank:]' '[:lower:][\-]')
LOGR_SHORT_HOSTNAME=`hostname -s`

# Check support setup
if [ -z $LOGR_SUPPORT_DIR ]; then
    export LOGR_SUPPORT_DIR=$LOGR_INSTALL_DIR/support-$LOGR_SHORT_HOSTNAME
    if [ -d $LOGR_SUPPORT_DIR ]; then
        cd $LOGR_SUPPORT_DIR
        export LOGR_SUPPORT_DIR=`pwd`
    fi
fi
if [ ! -d $LOGR_SUPPORT_DIR ]; then
    echo "Warning: $LOGR_SUPPORT_DIR directory does not exist. Developers should point LOGR_SUPPORT_DIR to the desired area." 
    #unset LOGR_SUPPORT_DIR
else
    export LOGR_GLASSFISH_DIR=$LOGR_SUPPORT_DIR/payara/$LOGR_HOST_ARCH
fi

# Add to path only if directory exists.
prependPathIfDirExists() {
    _dir=$1
    if [ -d ${_dir} ]; then
        PATH=${_dir}:$PATH
    fi
}

prependPathIfDirExists $LOGR_GLASSFISH_DIR/bin
prependPathIfDirExists $LOGR_SUPPORT_DIR/java/$LOGR_HOST_ARCH/bin
prependPathIfDirExists $LOGR_SUPPORT_DIR/ant/bin
prependPathIfDirExists $LOGR_SUPPORT_DIR/netbeans/currentNetbeans/bin
prependPathIfDirExists $LOGR_ROOT_DIR/bin
prependPathIfDirExists $LOGR_SUPPORT_DIR/anaconda/$LOGR_HOST_ARCH/bin
prependPathIfDirExists $LOGR_SUPPORT_DIR/netbeans/currentNetbeans/java/maven/bin
prependPathIfDirExists $LOGR_ROOT_DIR/tools/developer_tools/portal_testing/PythonSeleniumTest/support_bin

mysqlPath=$LOGR_SUPPORT_DIR/mysql/$LOGR_HOST_ARCH
if [ -d $mysqlPath ]; then
    cd $mysqlPath
    pythonDir=`pwd`
    export PATH=`pwd`/bin:$PATH
    export LD_LIBRARY_PATH=`pwd`/lib:$LD_LIBRARY_PATH    
fi

# Check if we have  local python
if [ -z $LOGR_PYTHON_DIR ]; then
    pythonDir=$LOGR_SUPPORT_DIR/python/$LOGR_HOST_ARCH
else
    pythonDir=$LOGR_PYTHON_DIR
fi
if [ -d $pythonDir ]; then
    cd $pythonDir
    pythonDir=`pwd`
    export PATH=`pwd`/bin:$PATH
    export LD_LIBRARY_PATH=`pwd`/lib:$LD_LIBRARY_PATH
    export LOGR_PYTHON_DIR=$pythonDir
fi

if [ -z $PYTHONPATH ]; then
    PYTHONPATH=$LOGR_ROOT_DIR/src/python
else
    PYTHONPATH=$LOGR_ROOT_DIR/src/python:$PYTHONPATH
fi
PYTHONPATH=$LOGR_ROOT_DIR/tools/developer_tools/python-client:$PYTHONPATH
export PYTHONPATH

# Done
cd $currentDir

