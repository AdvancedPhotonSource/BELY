#!/bin/bash

MY_DIR=`dirname $0` && cd $MY_DIR && MY_DIR=`pwd`
ROOT_DIR=$MY_DIR

ENV_NAME=bely-api-env
CONDA_DIR=$CONDA_PREFIX_1
echo $CONDA_DIR

if [ -z $CONDA_DIR ]
then
    CONDA_DIR=$CONDA_PREFIX
fi

if [ -z $CONDA_DIR ]
then
    echo '$CONDA_PRIFX must be defined.'
    exit 1
fi

source $CONDA_DIR/etc/profile.d/conda.sh || exit 1

# Prepare build source.
rm -rf src  
mkdir src 
ln -s ../../../generatePyClient.sh src/
cp ../../BelyApiFactory.py src/
cp ../../setup-api.py src/setup.py
cp ../../ClientApiConfig.yml src/
## Clean up and build new version of bely api
./src/generatePyClient.sh $1 || exit 1

# Clean and Build
rm -rvf ./build
conda build . --output-folder ./build || exit 1

# Install build into a new env 
conda create -n $ENV_NAME -y || exit 1
conda activate $ENV_NAME || exit 1
conda install BELY-API -c ./build -y || exit 1

#Export
conda list -n $ENV_NAME --explicit > $ENV_NAME.txt

echo "Please use the c2 tool to upload the $ENV_NAME.txt"

# Clean up
conda activate
conda env remove -n $ENV_NAME
rm -rf src